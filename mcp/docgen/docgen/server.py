"""docgen MCP 서버(FastMCP, stdio). 툴은 core 함수를 얇게 감싼다(로직 없음).

경로는 절대 경로 권장. 상대 경로는 DOCGEN_PROJECT_DIR(=${CLAUDE_PROJECT_DIR}) 기준.
반환에는 항상 절대 out_path 와 warnings 가 들어간다.
"""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from . import core

mcp = FastMCP("docgen")


def _guard(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        raise ToolError(f"DSL_ERROR: {e}") from e
    except FileNotFoundError as e:
        raise ToolError(f"NOT_FOUND: {e}") from e


@mcp.tool
def render_docx(
    spec_path: str,
    out_path: str | None = None,
    theme: str | None = None,
    template_docx: str | None = None,
) -> dict:
    """`.doc.md` → docx. 표지·개정이력·목차·머리글/바닥글·표·구성도·캡션 포함."""
    return _guard(core.render_docx, spec_path, out_path, theme, template_docx)


@mcp.tool
def render_pptx(
    spec_path: str,
    out_path: str | None = None,
    theme: str | None = None,
    template_pptx: str | None = None,
) -> dict:
    """`.deck.md` → pptx. 레이아웃 10종, 헤드 메시지, 네이티브 차트·구성도, 발표자 노트."""
    return _guard(core.render_pptx, spec_path, out_path, theme, template_pptx)


@mcp.tool
def render_diagram(spec: str, out_path: str, format: str = "png", theme: str | None = None) -> dict:
    """구성도 DSL(파일 경로 또는 YAML 문자열) → png|svg|mermaid."""
    return _guard(core.render_diagram, spec, out_path, format, theme)


@mcp.tool
def diagram_from_compose(compose_path: str, out_path: str | None = None) -> dict:
    """compose.yaml → 현행(AS-IS) 구성도 DSL 초안."""
    return _guard(core.diagram_from_compose, compose_path, out_path)


@mcp.tool
def lint_doc(path: str, mode: str = "all") -> dict:
    """산문 파일을 doc_lint 로 검사(단일 구현). {path, hard, soft, warnings}."""
    return _guard(core.lint_doc, path, mode)


@mcp.tool
def preview(path: str, pages: str = "1-3", dpi: int = 110) -> dict:
    """docx·pptx 를 PNG 로 미리보기(LibreOffice 필요). 없으면 available=false."""
    return _guard(core.preview, path, pages, dpi)


@mcp.tool
def docx_to_md(path: str) -> dict:
    """기존 docx → Markdown + 구조 요약."""
    return _guard(core.docx_to_md, path)


@mcp.tool
def pptx_to_md(path: str) -> dict:
    """기존 pptx → Markdown + 구조 요약."""
    return _guard(core.pptx_to_md, path)


@mcp.tool
def theme_from_pptx(path: str, name: str, out_dir: str = "themes") -> dict:
    """회사 템플릿 pptx 의 색·폰트·크기를 테마 JSON 으로 추출(매핑은 초안)."""
    return _guard(core.theme_from_pptx, path, name, out_dir)


@mcp.tool
def layouts(path: str) -> dict:
    """pptx 의 레이아웃 이름·placeholder 목록."""
    return _guard(core.layouts, path)


@mcp.tool
def theme_export(name: str = "datasolution", format: str = "tokens-css") -> dict:
    """ui-skill-set 용 --ui-accent 램프(tokens-css) 등 내보내기."""
    return _guard(core.theme_export, name, format)


def run():
    mcp.run()


if __name__ == "__main__":
    run()
