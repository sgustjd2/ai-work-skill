"""오케스트레이션: 경로 해석·테마 선택·기본 출력 경로·디스패치. CLI 와 MCP 서버가 이걸 쓴다.

MCP 서버 프로세스의 cwd 는 보장되지 않으므로 상대 경로는 DOCGEN_PROJECT_DIR(=${CLAUDE_PROJECT_DIR})
→ cwd 기준으로 잡고, 결과에는 항상 절대 경로를 담는다.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
from pathlib import Path

from . import docx_render, extract, parse, pptx_render
from . import preview as _preview
from . import theme as _theme
from .diagram import layout as _layout
from .diagram import mermaid as _mermaid
from .diagram import png as _png
from .diagram import svg as _svg
from .lint import lint_doc as _lint_doc

_ILLEGAL = re.compile(r'[<>:"/\\|?*\n\r\t]+')


def project_dir(base_dir=None) -> Path:
    if base_dir:
        return Path(base_dir).resolve()
    env = os.environ.get("DOCGEN_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env).resolve() if env else Path.cwd()


def _abs(path, base: Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (base / p)


def _read_style(base: Path) -> dict:
    sp = base / "STYLE.md"
    if not sp.exists():
        return {}
    fm, _ = parse.split_frontmatter(sp.read_text(encoding="utf-8"))
    return fm


class _DateProxy:
    def __init__(self, raw):
        self.raw = str(raw)
        self.dt = None
        for f in ("%Y-%m-%d", "%Y.%m.%d", "%Y. %m. %d", "%Y/%m/%d"):
            try:
                self.dt = _dt.datetime.strptime(self.raw.strip().rstrip("."), f)
                break
            except ValueError:
                continue

    def __format__(self, spec):
        if spec and self.dt:
            return self.dt.strftime(spec)
        return self.raw

    def __str__(self):
        return self.raw


def _fill_name(pattern: str, fm: dict) -> str:
    data = {
        "title": fm.get("title", "문서"),
        "version": fm.get("version", "0.1"),
        "org": fm.get("org", ""),
        "date": _DateProxy(fm.get("date", _dt.date.today().isoformat())),
    }
    try:
        name = pattern.format(**data)
    except (KeyError, ValueError):
        name = str(data["title"])
    name = _ILLEGAL.sub("", name).replace(" ", "_")
    return name or "문서"


def _resolve_theme(name, fm, style, base):
    tname = name or fm.get("theme") or style.get("theme")
    return _theme.load_theme(tname, base_dir=base)


def _default_out(base: Path, fm: dict, style: dict, ext: str) -> Path:
    outdir = base / style.get("render_output_dir", "docs/_build")
    pattern = style.get("filename_pattern", "{title}_v{version}_{date:%Y%m%d}")
    return outdir / f"{_fill_name(pattern, fm)}.{ext}"


# ─── 렌더 진입점 ─────────────────────────────────────────────────────────────
def render_docx(spec_path, out_path=None, theme=None, template_docx=None, base_dir=None):
    base = project_dir(base_dir)
    src = _abs(spec_path, base)
    parsed = parse.parse_doc(src.read_text(encoding="utf-8"))
    style = _read_style(base)
    th = _resolve_theme(theme, parsed["frontmatter"], style, base)
    out = (
        _abs(out_path, base)
        if out_path
        else _default_out(base, parsed["frontmatter"], style, "docx")
    )
    tpl = template_docx or parsed["frontmatter"].get("template_docx") or style.get("template_docx")
    logo = base / "docs" / "assets" / "logo.png"
    return docx_render.render_docx(
        parsed,
        str(out),
        th,
        base_dir=str(base),
        logo_path=str(logo) if logo.exists() else None,
        template_docx=tpl if tpl and str(tpl) != "None" else None,
    )


def render_pptx(spec_path, out_path=None, theme=None, template_pptx=None, base_dir=None):
    base = project_dir(base_dir)
    src = _abs(spec_path, base)
    parsed = parse.parse_deck(src.read_text(encoding="utf-8"))
    style = _read_style(base)
    th = _resolve_theme(theme, parsed["frontmatter"], style, base)
    out = (
        _abs(out_path, base)
        if out_path
        else _default_out(base, parsed["frontmatter"], style, "pptx")
    )
    tpl = template_pptx or parsed["frontmatter"].get("template") or style.get("template_pptx")
    return pptx_render.render_pptx(
        parsed,
        str(out),
        th,
        base_dir=str(base),
        template_pptx=tpl if tpl and str(tpl) != "None" else None,
    )


def render_diagram(spec_path_or_text, out_path, fmt="png", theme=None, base_dir=None):
    base = project_dir(base_dir)
    spec_text = _read_spec_text(spec_path_or_text, base)
    import yaml

    spec = yaml.safe_load(spec_text) or {}
    th = _theme.load_theme(theme, base_dir=base)
    out = _abs(out_path, base)
    if fmt == "mermaid":
        text, meta = _mermaid.to_mermaid(spec, th)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        lay = _layout.build_layout(spec)
        return {
            "out_path": str(out.resolve()),
            "nodes": len(lay["nodes"]),
            "edges": len(lay["edges"]),
            "warnings": meta["warnings"],
        }
    if fmt == "svg":
        text, meta = _svg.to_svg(spec, th)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        lay = _layout.build_layout(spec)
        return {
            "out_path": str(out.resolve()),
            "nodes": len(lay["nodes"]),
            "edges": len(lay["edges"]),
            "warnings": meta["warnings"],
        }
    p, warns = _png.to_png(spec, th, str(out), dpi=150)
    lay = _layout.build_layout(spec)
    return {
        "out_path": str(Path(p).resolve()) if p else None,
        "nodes": len(lay["nodes"]),
        "edges": len(lay["edges"]),
        "warnings": warns,
    }


def diagram_from_compose(compose_path, out_path=None, base_dir=None):
    """compose.yaml → 구성도 DSL 초안(현행 AS-IS)."""
    import yaml

    base = project_dir(base_dir)
    src = _abs(compose_path, base)
    data = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    services = data.get("services", {}) or {}
    nodes, edges, warnings = [], [], []

    def kind_of(image, name):
        s = f"{image} {name}".lower()
        if any(k in s for k in ("postgres", "pgvector", "mysql", "redis", "mongo", "db")):
            return "data"
        if "litellm" in s or "gateway" in s:
            return "gateway"
        if any(k in s for k in ("vllm", "ollama", "tgi", "sglang")):
            return "llm"
        if any(k in s for k in ("langfuse", "prometheus", "grafana", "jaeger")):
            return "external"
        return "service"

    for name, svc in services.items():
        svc = svc or {}
        image = svc.get("image", "")
        ports = svc.get("ports", []) or []
        port_lbl = str(ports[0]).split(":")[0] if ports else ""
        label = name if not port_lbl else f"{name}\\n:{port_lbl}"
        nodes.append({"id": name, "label": label, "kind": kind_of(image, name)})
    for name, svc in services.items():
        for dep in (svc or {}).get("depends_on", []) or []:
            dep_name = dep if isinstance(dep, str) else str(dep)
            if dep_name in services:
                edges.append({"from": name, "to": dep_name})
    if not nodes:
        warnings.append("compose 에서 services 를 찾지 못했습니다.")
    spec = {"type": "deployment", "direction": "LR", "nodes": nodes, "edges": edges}
    import yaml as _y

    text = _y.safe_dump(spec, allow_unicode=True, sort_keys=False)
    result = {"spec": spec, "dsl": text, "warnings": warnings}
    if out_path:
        out = _abs(out_path, base)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        result["out_path"] = str(out.resolve())
    return result


def lint_doc(path, mode="all", base_dir=None):
    base = project_dir(base_dir)
    return _lint_doc(str(_abs(path, base)), mode=mode)


def preview(path, pages="1-3", dpi=110, base_dir=None):
    base = project_dir(base_dir)
    return _preview.preview(str(_abs(path, base)), pages=pages, dpi=dpi)


def docx_to_md(path, base_dir=None):
    base = project_dir(base_dir)
    return extract.docx_to_md(str(_abs(path, base)))


def pptx_to_md(path, base_dir=None):
    base = project_dir(base_dir)
    return extract.pptx_to_md(str(_abs(path, base)))


def theme_from_pptx(path, name, out_dir="themes", base_dir=None):
    base = project_dir(base_dir)
    return extract.theme_from_pptx(str(_abs(path, base)), name, str(_abs(out_dir, base)))


def layouts(path, base_dir=None):
    base = project_dir(base_dir)
    return extract.layouts(str(_abs(path, base)))


def theme_export(name="datasolution", fmt="tokens-css", base_dir=None):
    base = project_dir(base_dir)
    th = _theme.load_theme(name, base_dir=base)
    if fmt == "tokens-css":
        return {"format": fmt, "content": _tokens_css(th), "warnings": []}
    return {"format": fmt, "content": "", "warnings": [f"알 수 없는 형식: {fmt}"]}


def _read_spec_text(spec_path_or_text, base: Path) -> str:
    s = str(spec_path_or_text)
    if "\n" not in s:
        p = _abs(s, base)
        if p.exists():
            return p.read_text(encoding="utf-8")
    return s


def _tokens_css(theme) -> str:
    """ui-skill-set 용 --ui-accent-100..900 램프. primary/action 기준 단순 명도 보간.
    # ponytail: OKLCH 정밀 보간은 FR-33(M4). 지금은 명도 램프 + 700 대비 보정.
    """
    base = _theme.color(theme, "action")
    white = _theme.color(theme, "white")
    ink = _theme.color(theme, "ink")
    steps = {
        100: 0.92,
        200: 0.82,
        300: 0.68,
        400: 0.5,
        500: 0.28,
        600: 0.12,
        700: 0.0,
        800: 0.18,
        900: 0.42,
    }
    lines = [":root {"]
    for step, t in steps.items():
        if step <= 700:
            hexv = _theme.mix(base, white, t)
        else:
            hexv = _theme.mix(base, ink, t)
        lines.append(f"  --ui-accent-{step}: {hexv};")
    # 700 이 흰 글자 대비 4.5:1 을 넘는지 확인
    c = _theme.contrast_ratio(_theme.mix(base, white, 0.0), white)
    if c < 4.5:
        lines.append(f"  /* 경고: accent-700 대비 {c:.2f}:1 (<4.5). 더 어두운 값 필요 */")
    lines.append("}")
    return "\n".join(lines)
