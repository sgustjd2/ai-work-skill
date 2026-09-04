"""`.doc.md` / `.deck.md` 파서 (FR-9).

Markdown(GFM 표) + YAML frontmatter 를 결정적 블록 모델로 바꾼다. 렌더러(docx/pptx)는
이 블록만 본다. 구성도/타임라인/차트는 펜스 코드(```diagram 등)로, 캡션·쪽나눔·노트는
HTML 주석으로 표현한다.

블록 종류:
  heading{level,text,runs}  paragraph{runs}  list{ordered,items:[{runs,level}]}
  table{header:[[run]],rows:[[[run]]],align,caption}  code{lang,text}
  diagram{spec,raw}  timeline{spec,raw}  chart{spec,raw}
  image{src,caption}  quote{blocks}  pagebreak  hr  footnote{id,runs}
run = {text,bold,italic,code}
"""

from __future__ import annotations

import re

import yaml
from markdown_it import MarkdownIt

_FM = re.compile(r"^﻿?---\r?\n(.*?)\r?\n---\r?\n?", re.S)
_FOOTNOTE_DEF = re.compile(r"^\[\^([^\]]+)\]:[ \t]*(.*)$")
_COMMENT = re.compile(r"<!--\s*(.*?)\s*-->", re.S)
_CTRL = re.compile(r"^(layout|note|source|caption|col|pagebreak)\s*:?\s*(.*)$", re.S | re.I)


def _md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True})
    for rule in ("table", "strikethrough"):
        try:
            md.enable(rule)
        except Exception:  # noqa: BLE001 - 규칙이 없으면 조용히 건너뜀
            pass
    return md


def split_frontmatter(text: str) -> tuple[dict, str]:
    m = _FM.match(text)
    if not m:
        return {}, text
    data = yaml.safe_load(m.group(1)) or {}
    if not isinstance(data, dict):
        data = {}
    return data, text[m.end() :]


def _extract_footnotes(body: str) -> tuple[str, list[dict]]:
    kept, notes = [], []
    for line in body.splitlines():
        m = _FOOTNOTE_DEF.match(line)
        if m:
            notes.append({"type": "footnote", "id": m.group(1), "runs": _text_runs(m.group(2))})
        else:
            kept.append(line)
    return "\n".join(kept), notes


def _text_runs(s: str) -> list[dict]:
    return [{"text": s, "bold": False, "italic": False, "code": False}] if s else []


# ─── 인라인 → run ───────────────────────────────────────────────────────────
def _inline_runs(token) -> list[dict]:
    runs: list[dict] = []
    bold = italic = 0
    if token is None or not getattr(token, "children", None):
        return runs
    for c in token.children:
        t = c.type
        if t == "text":
            if c.content:
                runs.append(
                    {"text": c.content, "bold": bold > 0, "italic": italic > 0, "code": False}
                )
        elif t == "code_inline":
            runs.append({"text": c.content, "bold": bold > 0, "italic": italic > 0, "code": True})
        elif t == "strong_open":
            bold += 1
        elif t == "strong_close":
            bold = max(0, bold - 1)
        elif t in ("em_open",):
            italic += 1
        elif t in ("em_close",):
            italic = max(0, italic - 1)
        elif t in ("softbreak", "hardbreak"):
            runs.append({"text": " ", "bold": bold > 0, "italic": italic > 0, "code": False})
        elif t == "image":
            alt = c.content or (c.attrGet("alt") or "")
            if alt:
                runs.append({"text": alt, "bold": bold > 0, "italic": italic > 0, "code": False})
        # link_open/close, html_inline, s_open/close → 텍스트만 유지(자식 text 로 이미 들어옴)
    return _merge_runs(runs)


def _merge_runs(runs: list[dict]) -> list[dict]:
    out: list[dict] = []
    for r in runs:
        if (
            out
            and out[-1]["bold"] == r["bold"]
            and out[-1]["italic"] == r["italic"]
            and out[-1]["code"] == r["code"]
        ):
            out[-1] = {**out[-1], "text": out[-1]["text"] + r["text"]}
        else:
            out.append(r)
    return out


def _runs_text(runs: list[dict]) -> str:
    return "".join(r["text"] for r in runs)


# ─── 토큰 → 블록 ─────────────────────────────────────────────────────────────
def _parse_spec(raw: str, kind: str) -> dict:
    try:
        spec = yaml.safe_load(raw) or {}
        if not isinstance(spec, dict):
            raise ValueError("최상위가 매핑이 아님")
        return spec
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"{kind} 블록 YAML 파싱 실패: {e}") from e


def _control_from_comment(content: str) -> dict | None:
    m = _CTRL.match(content.strip())
    if not m:
        return None
    key = m.group(1).lower()
    val = (m.group(2) or "").strip()
    return {"type": "control", "key": key, "value": val}


class _Walker:
    def __init__(self, tokens):
        self.tk = tokens
        self.i = 0

    def _peek(self):
        return self.tk[self.i] if self.i < len(self.tk) else None

    def blocks(self, stop=None) -> list[dict]:
        out: list[dict] = []
        while self.i < len(self.tk):
            tok = self.tk[self.i]
            if stop and tok.type == stop:
                return out
            b = self._one()
            if b is not None:
                out.extend(b if isinstance(b, list) else [b])
        return out

    def _one(self):
        tok = self.tk[self.i]
        t = tok.type
        if t == "heading_open":
            level = int(tok.tag[1])
            inline = self.tk[self.i + 1]
            runs = _inline_runs(inline)
            self.i += 3  # open, inline, close
            return {"type": "heading", "level": level, "text": _runs_text(runs), "runs": runs}
        if t == "paragraph_open":
            inline = self.tk[self.i + 1]
            self.i += 3
            return self._paragraph(inline)
        if t == "fence":
            self.i += 1
            return self._fence(tok)
        if t == "code_block":
            self.i += 1
            return {"type": "code", "lang": "", "text": tok.content.rstrip("\n")}
        if t in ("bullet_list_open", "ordered_list_open"):
            return self._list()
        if t == "table_open":
            return self._table()
        if t == "blockquote_open":
            self.i += 1
            inner = self.blocks(stop="blockquote_close")
            self.i += 1  # close
            return {"type": "quote", "blocks": inner}
        if t == "html_block":
            self.i += 1
            return self._html(tok.content)
        if t == "hr":
            self.i += 1
            return {"type": "hr"}
        # 알 수 없는 토큰은 건너뜀
        self.i += 1
        return None

    def _paragraph(self, inline):
        # 이미지 단독 문단 → image 블록
        kids = [c for c in (inline.children or []) if c.type not in ("softbreak",)]
        imgs = [c for c in kids if c.type == "image"]
        non_img = [
            c
            for c in kids
            if c.type not in ("image", "text") or (c.type == "text" and c.content.strip())
        ]
        if len(imgs) == 1 and not non_img:
            img = imgs[0]
            return {
                "type": "image",
                "src": img.attrGet("src") or "",
                "caption": img.content or (img.attrGet("alt") or ""),
            }
        runs = _inline_runs(inline)
        if not _runs_text(runs).strip():
            return None
        return {"type": "paragraph", "runs": runs}

    def _fence(self, tok):
        info = (tok.info or "").strip().split()
        lang = info[0] if info else ""
        if lang in ("diagram", "timeline", "chart"):
            spec = _parse_spec(tok.content, lang)
            return {"type": lang, "spec": spec, "raw": tok.content}
        return {"type": "code", "lang": lang, "text": tok.content.rstrip("\n")}

    def _list(self):
        tok = self.tk[self.i]
        ordered = tok.type == "ordered_list_open"
        self.i += 1
        items: list[dict] = []
        while self.i < len(self.tk) and self.tk[self.i].type == "list_item_open":
            self.i += 1  # list_item_open
            inner = self.blocks(stop="list_item_close")
            self.i += 1  # list_item_close
            items.append(self._flatten_item(inner))
        # list_close
        if self.i < len(self.tk) and self.tk[self.i].type in (
            "bullet_list_close",
            "ordered_list_close",
        ):
            self.i += 1
        return {"type": "list", "ordered": ordered, "items": items}

    @staticmethod
    def _flatten_item(inner: list[dict]) -> dict:
        """리스트 항목: 첫 문단은 본문, 중첩 리스트는 level+1 로 편다."""
        runs: list[dict] = []
        children: list[dict] = []
        for b in inner:
            if b["type"] == "paragraph" and not runs:
                runs = b["runs"]
            elif b["type"] == "list":
                for sub in b["items"]:
                    children.append({**sub, "level": sub.get("level", 0) + 1})
            elif b["type"] == "paragraph":
                runs = (
                    runs
                    + [{"text": " ", "bold": False, "italic": False, "code": False}]
                    + b["runs"]
                )
        return {"runs": runs, "level": 0, "children": children}

    def _table(self):
        self.i += 1  # table_open
        header: list[list[dict]] = []
        rows: list[list[list[dict]]] = []
        align: list[str] = []
        while self.i < len(self.tk) and self.tk[self.i].type != "table_close":
            tok = self.tk[self.i]
            if tok.type == "th_open":
                a = tok.attrGet("style") or ""
                align.append("right" if "right" in a else "center" if "center" in a else "left")
                header.append(_inline_runs(self.tk[self.i + 1]))
                self.i += 3
            elif tok.type == "tr_open" and header:
                self.i += 1
                cells: list[list[dict]] = []
                while self.i < len(self.tk) and self.tk[self.i].type != "tr_close":
                    if self.tk[self.i].type == "td_open":
                        cells.append(_inline_runs(self.tk[self.i + 1]))
                        self.i += 3
                    else:
                        self.i += 1
                self.i += 1  # tr_close
                if cells:
                    rows.append(cells)
            else:
                self.i += 1
        self.i += 1  # table_close
        return {"type": "table", "header": header, "rows": rows, "align": align, "caption": None}

    def _html(self, content: str):
        out = []
        for m in _COMMENT.finditer(content):
            ctrl = _control_from_comment(m.group(1))
            if ctrl:
                out.append(ctrl)
        return out or None


_CAPTIONABLE = ("table", "image", "diagram", "timeline", "chart")


def _apply_controls_doc(blocks: list[dict]) -> list[dict]:
    """문서: caption 은 다음 표/그림에, pagebreak 는 블록으로. 나머지 control 은 버린다."""
    out: list[dict] = []
    pending_caption: str | None = None
    for b in blocks:
        if b["type"] == "control":
            if b["key"] == "caption":
                pending_caption = b["value"]
            elif b["key"] == "pagebreak":
                out.append({"type": "pagebreak"})
            continue
        if pending_caption and b["type"] in _CAPTIONABLE:
            b = {**b, "caption": pending_caption}
            pending_caption = None
        out.append(b)
    return out


def parse_doc(text: str) -> dict:
    fm, body = split_frontmatter(text)
    body, footnotes = _extract_footnotes(body)
    tokens = _md().parse(body)
    blocks = _Walker(tokens).blocks()
    blocks = _apply_controls_doc(blocks)
    return {"frontmatter": fm, "blocks": blocks, "footnotes": footnotes}


# ─── 덱 ──────────────────────────────────────────────────────────────────────
def _split_slides_tokens(tokens):
    groups, cur = [], []
    for tok in tokens:
        if tok.type == "hr":
            groups.append(cur)
            cur = []
        else:
            cur.append(tok)
    groups.append(cur)
    return [
        g for g in groups if any(t.type not in ("html_block",) or t.content.strip() for t in g)
    ] or groups


def _build_slide(tokens) -> dict:
    blocks = _Walker(tokens).blocks()
    title = None
    headline = None
    layout = None
    notes: list[str] = []
    source = None
    saw_col = False
    segments: list[list[dict]] = [[]]  # col 마커로 나뉘는 구간

    for b in blocks:
        if b["type"] == "control":
            k, v = b["key"], b["value"]
            if k == "layout":
                layout = v
            elif k == "note":
                notes.append(v)
            elif k == "source":
                source = v
            elif k == "col":
                saw_col = True
                segments.append([])
            continue
        if b["type"] == "heading" and b["level"] == 1 and title is None:
            title = b["text"]
            continue
        if b["type"] == "heading" and b["level"] == 2 and headline is None:
            headline = b["text"]
            continue
        segments[-1].append(b)

    if saw_col:
        columns = [s for s in segments if s]  # 빈 구간(첫 마커 앞) 제거
        body = []
        all_blocks = [x for c in columns for x in c]
    else:
        columns = None
        body = segments[0]
        all_blocks = body

    if layout is None:
        layout = _infer_layout(all_blocks, columns)

    return {
        "title": title or "",
        "headline": headline or "",
        "layout": layout,
        "notes": " ".join(notes),
        "source": source or "",
        "blocks": body,
        "columns": columns,
    }


def _infer_layout(body: list[dict], columns) -> str:
    if columns is not None:
        return "two-col"
    kinds = {b["type"] for b in body}
    if "diagram" in kinds:
        return "diagram"
    if "chart" in kinds:
        return "chart"
    if "timeline" in kinds:
        return "timeline"
    if "table" in kinds:
        return "table"
    if kinds == {"image"} or (len(body) == 1 and "image" in kinds):
        return "image"
    return "message"


def parse_deck(text: str) -> dict:
    fm, body = split_frontmatter(text)
    tokens = _md().parse(body)
    groups = _split_slides_tokens(tokens)
    slides = [_build_slide(g) for g in groups]
    slides = [s for s in slides if s["title"] or s["headline"] or s["blocks"] or s["columns"]]
    return {"frontmatter": fm, "slides": slides}
