"""`.doc.md` -> docx. 표지·개정이력·목차·머리글/바닥글·쪽번호·스타일 6종·표·코드·그림·마커 형광.

함정 대응(10.5): East Asian 폰트(w:eastAsia), 어절 줄바꿈(w:wordWrap=0), 목차 필드+updateFields,
표 헤더 음영·반복, 캡션 번호. 색·폰트·치수는 테마 JSON 에서만 온다.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

from . import core
from .diagram import mermaid
from .parse import parse_doc, runs_text
from .theme import color as theme_color
from .theme import load_theme

_NUM_RE = re.compile(r"^\s*[\d,]+(?:\.\d+)?%?\s*$")


def _rgb(hexstr):
    return RGBColor.from_string(hexstr.lstrip("#"))


def _set_ea(rpr, name):
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(attr), name)


def _run_ea(run, name):
    run.font.name = name
    _set_ea(run._r.get_or_add_rPr(), name)


def _shade(element, fill_hex):
    """문단/셀 pPr·tcPr 에 배경 음영."""
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill_hex.lstrip("#"))
    element.append(shd)


def _field(paragraph, instr):
    run = paragraph.add_run()
    for kind, txt in (("begin", None), ("instr", instr), ("end", None)):
        if kind == "instr":
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        else:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        run._r.append(el)


def _ensure_style(doc, name, base="Normal"):
    try:
        return doc.styles[name]
    except KeyError:
        st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        st.base_style = doc.styles[base]
        return st


def _cfg_style(style, font, size_pt, color_hex=None, ea=True, bold=False):
    style.font.name = font
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    if color_hex:
        style.font.color.rgb = _rgb(color_hex)
    if ea:
        _set_ea(style.element.get_or_add_rPr(), font)


def _setup_styles(doc, theme, font, mono):
    dx = theme["docx"]

    def col(role):
        return theme_color(theme, role)

    normal = doc.styles["Normal"]
    _cfg_style(normal, font, dx["body_pt"], col("ink"))
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = dx.get("line_spacing", 1.6)
    pf.space_after = Pt(dx.get("para_after_pt", 6))
    ww = OxmlElement("w:wordWrap")
    ww.set(qn("w:val"), "0")
    normal.element.get_or_add_pPr().append(ww)

    for name, size in (
        ("Heading 1", dx["h1_pt"]),
        ("Heading 2", dx["h2_pt"]),
        ("Heading 3", dx["h3_pt"]),
    ):
        st = doc.styles[name]
        _cfg_style(st, font, size, col(dx.get("heading_color", "primary")), bold=True)
        st.paragraph_format.space_before = Pt(size * 0.9)
        st.paragraph_format.space_after = Pt(size * 0.35)

    _cfg_style(_ensure_style(doc, "Caption"), font, dx.get("caption_pt", 9), col("ink_subtle"))
    code = _ensure_style(doc, "Code")
    _cfg_style(code, mono, dx.get("code_pt", 9), col("ink"), ea=False)
    _shade(code.element.get_or_add_pPr(), col("surface"))
    _cfg_style(_ensure_style(doc, "TableText"), font, dx.get("table_pt", 9.5), col("ink"))
    try:
        _cfg_style(doc.styles["Quote"], font, dx["body_pt"], col("ink_muted"))
    except KeyError:
        pass


def _add_runs(p, runs, ctx):
    for r in runs:
        if r.get("kind") == "image":
            continue
        is_code = r.get("kind") == "code"
        for seg, is_marker in _split_marker(r.get("text", ""), ctx["marker_re"]):
            if not seg:
                continue
            run = p.add_run(seg)
            _run_ea(run, ctx["mono"] if is_code else ctx["font"])
            if not is_code:
                run.bold = bool(r.get("bold"))
                run.italic = bool(r.get("italic"))
                if r.get("strike"):
                    run.font.strike = True
                if r.get("link"):
                    run.font.color.rgb = _rgb(ctx["action"])
                    run.font.underline = True
            if is_marker:  # 마커는 코드/본문 어디서든 형광(10.5)
                run.font.highlight_color = WD_COLOR_INDEX.YELLOW


def _split_marker(text, marker_re):
    out, i = [], 0
    for m in marker_re.finditer(text):
        if m.start() > i:
            out.append((text[i : m.start()], False))
        out.append((m.group(), True))
        i = m.end()
    out.append((text[i:], False))
    return out


def _add_table(doc, block, ctx, counters):
    if block.get("caption"):
        counters["table"] += 1
        cap = doc.add_paragraph(style="Caption")
        cap.add_run(f"[표 {counters['table']}] {block['caption']}")
    header = block["header"]
    rows = block["rows"]
    ncol = len(header)
    table = doc.add_table(rows=1, cols=ncol)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    numeric = _numeric_cols(header, rows)
    hdr = table.rows[0].cells
    for j, cell_runs in enumerate(header):
        _fill_cell(hdr[j], runs_text(cell_runs), ctx, header=True, right=j in numeric)
    _repeat_header(table.rows[0])
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        for j in range(ncol):
            txt = runs_text(row[j]) if j < len(row) and row[j] else ""
            _fill_cell(cells[j], txt, ctx, header=False, right=j in numeric, band=(ri % 2 == 1))


def _numeric_cols(header, rows):
    out = set()
    for j in range(len(header)):
        vals = [runs_text(r[j]) for r in rows if j < len(r) and r[j]]
        if vals and all(_NUM_RE.match(v) for v in vals):
            out.add(j)
    return out


def _fill_cell(cell, text, ctx, header, right, band=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.style = cell.part.document.styles["TableText"]
    p.paragraph_format.space_after = Pt(0)
    if right:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(text)
    _run_ea(run, ctx["font"])
    if header:
        run.bold = True
        run.font.color.rgb = _rgb(ctx["table_header_text"])
        _shade(cell._tc.get_or_add_tcPr(), ctx["table_header_fill"])
    elif band:
        _shade(cell._tc.get_or_add_tcPr(), ctx["surface"])


def _repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)


def _add_toc(doc):
    p = doc.add_paragraph()
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), 'TOC \\o "1-3" \\h \\z \\u')
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "목차 (문서를 열고 F9 로 갱신)"
    r.append(t)
    fld.append(r)
    p._p.append(fld)


def _update_fields(doc):
    el = OxmlElement("w:updateFields")
    el.set(qn("w:val"), "true")
    doc.settings.element.append(el)


def _rule(doc, color_hex):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "18")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color_hex.lstrip("#"))
    pbdr.append(bottom)
    pPr.append(pbdr)
    return p


def render_docx(spec_path, out_path=None, theme=None, template_docx=None, base=None):
    bdir = core.base_dir(base)
    doc_data = parse_doc(spec_path)
    fm = doc_data["frontmatter"]
    style = core.load_style(bdir)
    th = load_theme(core.theme_name(fm, style, theme), bdir)
    font = fm.get("office_font") or style.get("office_font") or th["fonts"]["office_ko"]
    mono = th["fonts"].get("mono", "Consolas")
    warnings = []

    doc = Document()
    _setup_section(doc, th)
    _setup_styles(doc, th, font, mono)

    ctx = {
        "font": font,
        "mono": mono,
        "action": theme_color(th, "action"),
        "surface": theme_color(th, "surface"),
        "table_header_fill": theme_color(th, th["docx"].get("table_header_fill", "surface")),
        "table_header_text": theme_color(th, th["docx"].get("table_header_text", "primary")),
        "marker_re": core.marker_pattern(style),
    }
    _header_footer(doc, fm, style, th, font)
    _title_page(doc, fm, style, th, font, bdir, warnings)
    _history(doc, fm, ctx, th)
    if fm.get("toc", True):
        doc.add_paragraph("목차", style="Heading 1")
        _add_toc(doc)
        _update_fields(doc)
    doc.add_page_break()

    counters = {"table": 0, "figure": 0}
    headings = []
    for block in doc_data["blocks"]:
        _render_block(doc, block, ctx, counters, headings, th, warnings, bdir)

    out = core.out_path_for(spec_path, fm, style, out_path, ".docx", bdir)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return {
        "out_path": str(out.resolve()),
        "pages_estimate": max(1, round(len(doc_data["blocks"]) / 8) + 1),
        "headings": headings,
        "warnings": warnings,
    }


def _setup_section(doc, theme):
    dx = theme["docx"]
    sec = doc.sections[0]
    if dx.get("page", "A4") == "A4":
        sec.page_width = Mm(210)
        sec.page_height = Mm(297)
    m = dx.get("margins_mm", [25, 20, 25, 20])
    sec.top_margin, sec.right_margin, sec.bottom_margin, sec.left_margin = (
        Mm(m[0]),
        Mm(m[1]),
        Mm(m[2]),
        Mm(m[3]),
    )


def _header_footer(doc, fm, style, theme, font):
    sec = doc.sections[0]
    hp = sec.header.paragraphs[0]
    hp.text = fm.get("title", "")
    security = fm.get("security") or style.get("security")
    if security:
        tab = hp.add_run("\t" + str(security))
        _run_ea(tab, font)
    _run_ea(hp.runs[0], font) if hp.runs else None
    hp.paragraph_format.tab_stops.add_tab_stop(
        sec.page_width - sec.left_margin - sec.right_margin, alignment=WD_ALIGN_PARAGRAPH.RIGHT
    )
    fpar = sec.footer.paragraphs[0]
    fpar.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _field(fpar, "PAGE")
    fpar.add_run(" / ")
    _field(fpar, "NUMPAGES")
    for run in fpar.runs:
        run.font.size = Pt(theme["docx"].get("caption_pt", 9))
        run.font.color.rgb = _rgb(theme_color(theme, "ink_subtle"))


def _title_page(doc, fm, style, theme, font, bdir, warnings):
    logo = Path(bdir) / "docs" / "assets" / "logo.png"
    if logo.is_file():
        try:
            doc.add_picture(str(logo), width=Mm(35))
        except Exception:
            warnings.append("로고 삽입 실패")
    _rule(doc, theme_color(theme, "primary"))
    title = doc.add_paragraph()
    tr = title.add_run(fm.get("title", "제목 없음"))
    tr.bold = True
    tr.font.size = Pt(theme["docx"]["h1_pt"] + 8)
    tr.font.color.rgb = _rgb(theme_color(theme, "primary"))
    _run_ea(tr, font)
    if fm.get("subtitle"):
        sub = doc.add_paragraph()
        sr = sub.add_run(fm["subtitle"])
        sr.font.color.rgb = _rgb(theme_color(theme, "ink_muted"))
        _run_ea(sr, font)
    meta = [
        ("조직", fm.get("org") or style.get("org", "")),
        ("작성자", fm.get("author", "")),
        ("일자", str(fm.get("date", ""))),
        ("버전", str(fm.get("version", ""))),
    ]
    t = doc.add_table(rows=0, cols=2)
    for k, v in meta:
        if not v:
            continue
        cells = t.add_row().cells
        for cell, txt, bold in ((cells[0], k, True), (cells[1], str(v), False)):
            cell.text = ""
            run = cell.paragraphs[0].add_run(txt)
            run.bold = bold
            _run_ea(run, font)
    approvers = fm.get("approvers")
    if approvers:
        doc.add_paragraph()
        at = doc.add_table(rows=2, cols=len(approvers))
        at.style = "Table Grid"
        for j, name in enumerate(approvers):
            c = at.rows[0].cells[j]
            c.text = ""
            r = c.paragraphs[0].add_run(str(name))
            r.bold = True
            _run_ea(r, font)
    doc.add_page_break()


def _history(doc, fm, ctx, theme):
    hist = fm.get("history")
    if not hist:
        return
    doc.add_paragraph("개정 이력", style="Heading 1")
    header = [[{"kind": "text", "text": h}] for h in ("버전", "일자", "작성자", "내용")]
    rows = []
    for h in hist:
        if isinstance(h, dict):
            rows.append(
                [
                    [{"kind": "text", "text": str(h.get(k, ""))}]
                    for k in ("version", "date", "author", "note")
                ]
            )
    _add_table(doc, {"header": header, "rows": rows, "caption": None}, ctx, {"table": 0})


def _render_block(doc, block, ctx, counters, headings, theme, warnings, bdir):
    t = block["type"]
    if t == "heading":
        lvl = min(block["level"], 3)
        doc.add_paragraph(block["text"], style=f"Heading {lvl}")
        headings.append({"level": block["level"], "text": block["text"]})
    elif t == "paragraph":
        p = doc.add_paragraph()
        _add_runs(p, block["runs"], ctx)
    elif t == "list":
        _render_list(doc, block, ctx, 0)
    elif t == "table":
        _add_table(doc, block, ctx, counters)
    elif t == "code":
        for line in block["content"].rstrip("\n").split("\n"):
            para = doc.add_paragraph(style="Code")
            run = para.add_run(line)
            _run_ea(run, ctx["mono"])
    elif t in ("diagram", "chart", "timeline"):
        _render_special(doc, block, ctx, counters, theme, warnings, bdir)
    elif t == "image":
        _render_image(doc, block, counters, ctx, bdir, warnings)
    elif t == "blockquote":
        for b in block["blocks"]:
            if b["type"] == "paragraph":
                p = doc.add_paragraph(style="Quote")
                _add_runs(p, b["runs"], ctx)
            else:
                _render_block(doc, b, ctx, counters, headings, theme, warnings, bdir)
    elif t == "pagebreak":
        doc.add_page_break()


def _render_list(doc, block, ctx, depth):
    style = "List Number" if block["ordered"] else "List Bullet"
    for item in block["items"]:
        for b in item:
            if b["type"] == "paragraph":
                p = doc.add_paragraph(style=style)
                if depth:
                    p.paragraph_format.left_indent = Mm(6 * depth)
                _add_runs(p, b["runs"], ctx)
            elif b["type"] == "list":
                _render_list(doc, b, ctx, depth + 1)


def _render_image(doc, block, counters, ctx, bdir, warnings):
    path = Path(block["path"])
    if not path.is_absolute():
        path = Path(bdir) / path
    sec = doc.sections[0]
    maxw = sec.page_width - sec.left_margin - sec.right_margin
    if path.is_file():
        try:
            doc.add_picture(str(path), width=maxw)
        except Exception:
            warnings.append(f"그림 삽입 실패: {block['path']}")
            return
    else:
        warnings.append(f"그림 파일 없음: {block['path']}")
        doc.add_paragraph(f"[그림 자리: {block['path']}]")
    if block.get("caption"):
        counters["figure"] += 1
        cap = doc.add_paragraph(style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run(f"[그림 {counters['figure']}] {block['caption']}")


def _render_special(doc, block, ctx, counters, theme, warnings, bdir):
    t = block["type"]
    if t == "diagram":
        _render_diagram(doc, block, ctx, counters, theme, warnings)
    else:
        _chart_or_timeline_table(doc, block, ctx, counters)


def _render_diagram(doc, block, ctx, counters, theme, warnings):
    import tempfile

    from .diagram import png

    tmp = Path(tempfile.gettempdir()) / f"docgen_dia_{id(block):x}.png"
    res = png.render_png(block["spec"], theme, str(tmp))
    if res:
        warnings.extend(res["warnings"])
        sec = doc.sections[0]
        maxw = sec.page_width - sec.left_margin - sec.right_margin
        try:
            doc.add_picture(str(tmp), width=maxw)
        finally:
            tmp.unlink(missing_ok=True)
        counters["figure"] += 1
        cap = doc.add_paragraph(style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run(f"[그림 {counters['figure']}] 구성도")
    else:
        # 한글 폰트 미탐지: 문서가 깨지지 않게 mermaid 소스를 코드 블록으로(10.3)
        warnings.append("구성도 PNG 폰트 미탐지: mermaid 소스로 대체(테마 font_paths 확인)")
        for line in mermaid.to_mermaid(block["spec"], theme).rstrip("\n").split("\n"):
            _run_ea(doc.add_paragraph(style="Code").add_run(line), ctx["mono"])


def _chart_or_timeline_table(doc, block, ctx, counters):
    spec = block.get("spec", {})
    if block["type"] == "chart":
        cats = spec.get("categories", [])
        series = spec.get("series", [])
        header = [[{"kind": "text", "text": "구분"}]] + [
            [{"kind": "text", "text": s.get("name", "")}] for s in series
        ]
        rows = []
        for i, cat in enumerate(cats):
            row = [[{"kind": "text", "text": str(cat)}]]
            for s in series:
                vals = s.get("values", [])
                row.append([{"kind": "text", "text": str(vals[i]) if i < len(vals) else ""}])
            rows.append(row)
        title = spec.get("title", "차트")
        unit = spec.get("unit", "")
        cap = f"{title} ({unit})" if unit else title
        _add_table(doc, {"header": header, "rows": rows, "caption": cap}, ctx, counters)
    else:  # timeline
        tasks = spec.get("tasks", [])
        header = [[{"kind": "text", "text": h}] for h in ("항목", "시작", "종료", "비고")]
        rows = [
            [
                [{"kind": "text", "text": str(t.get(k, ""))}]
                for k in ("label", "start", "end", "group")
            ]
            for t in tasks
        ]
        _add_table(
            doc,
            {"header": header, "rows": rows, "caption": spec.get("title", "일정")},
            ctx,
            counters,
        )
