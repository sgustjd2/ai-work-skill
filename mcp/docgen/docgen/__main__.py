"""docgen CLI. MCP 서버와 같은 core 함수를 부른다.

  python -m docgen render-docx <파일> [--out ..] [--theme ..] [--template ..]
  python -m docgen render-pptx <파일> [--out ..] [--theme ..] [--template ..]
  python -m docgen render-diagram <파일|-> --out .. [--format png|svg|mermaid] [--theme ..]
  python -m docgen diagram-from-compose <compose.yaml> [--out ..]
  python -m docgen lint <파일> [--mode all|hard]
  python -m docgen preview <docx|pptx> [--pages 1-3] [--dpi 110]
  python -m docgen docx-to-md <파일> | pptx-to-md <파일>
  python -m docgen theme-from-pptx <파일> --name company [--out-dir themes]
  python -m docgen layouts <pptx>
  python -m docgen theme-export [--name datasolution] [--format tokens-css]
종료코드: 0 성공 · 2 DSL/파싱 오류 · 1 렌더 실패 · 3 외부 도구 없음
"""

from __future__ import annotations

import argparse
import json
import sys

from . import core


def _out(result, as_json):
    if as_json:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    else:
        for w in result.get("warnings", []):
            sys.stderr.write(f"[docgen] 경고: {w}\n")
        if "out_path" in result and result["out_path"]:
            sys.stdout.write(f"생성: {result['out_path']}\n")
        elif "markdown" in result:
            sys.stdout.write(result["markdown"])
        elif "content" in result:
            sys.stdout.write(result["content"] + "\n")
        else:
            sys.stdout.write(json.dumps(result, ensure_ascii=False) + "\n")


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    # default=SUPPRESS: 서브파서가 상위 파서의 값을 덮어쓰지 않게 한다(앞/뒤 위치 모두 동작).
    common.add_argument(
        "--json", action="store_true", default=argparse.SUPPRESS, help="결과를 JSON 으로 출력"
    )
    ap = argparse.ArgumentParser(prog="docgen", parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, *args):
        p = sub.add_parser(name, parents=[common])
        for a, kw in args:
            p.add_argument(a, **kw)
        return p

    add(
        "render-docx",
        ("spec", {}),
        ("--out", {}),
        ("--theme", {}),
        ("--template", {}),
        ("--base", {}),
    )
    add(
        "render-pptx",
        ("spec", {}),
        ("--out", {}),
        ("--theme", {}),
        ("--template", {}),
        ("--base", {}),
    )
    add(
        "render-diagram",
        ("spec", {}),
        ("--out", {"required": True}),
        ("--format", {"default": "png", "choices": ["png", "svg", "mermaid"]}),
        ("--theme", {}),
        ("--base", {}),
    )
    add("diagram-from-compose", ("spec", {}), ("--out", {}), ("--base", {}))
    add(
        "lint",
        ("spec", {}),
        ("--mode", {"default": "all", "choices": ["all", "hard"]}),
        ("--base", {}),
    )
    add(
        "preview",
        ("spec", {}),
        ("--pages", {"default": "1-3"}),
        ("--dpi", {"type": int, "default": 110}),
        ("--base", {}),
    )
    add("docx-to-md", ("spec", {}), ("--base", {}))
    add("pptx-to-md", ("spec", {}), ("--base", {}))
    add(
        "theme-from-pptx",
        ("spec", {}),
        ("--name", {"required": True}),
        ("--out-dir", {"default": "themes"}),
        ("--base", {}),
    )
    add("layouts", ("spec", {}), ("--base", {}))
    add(
        "theme-export",
        ("--name", {"default": "datasolution"}),
        ("--format", {"default": "tokens-css"}),
        ("--base", {}),
    )

    a = ap.parse_args(argv)
    as_json = getattr(a, "json", False)
    base = getattr(a, "base", None)
    try:
        if a.cmd == "render-docx":
            r = core.render_docx(a.spec, a.out, a.theme, a.template, base)
        elif a.cmd == "render-pptx":
            r = core.render_pptx(a.spec, a.out, a.theme, a.template, base)
        elif a.cmd == "render-diagram":
            r = core.render_diagram(a.spec, a.out, a.format, a.theme, base)
            if r.get("out_path") is None:
                _out(r, as_json)
                return 1
        elif a.cmd == "diagram-from-compose":
            r = core.diagram_from_compose(a.spec, a.out, base)
        elif a.cmd == "lint":
            r = core.lint_doc(a.spec, a.mode, base)
        elif a.cmd == "preview":
            r = core.preview(a.spec, a.pages, a.dpi, base)
            if not r.get("available"):
                _out(r, as_json)
                return 3
        elif a.cmd == "docx-to-md":
            r = core.docx_to_md(a.spec, base)
        elif a.cmd == "pptx-to-md":
            r = core.pptx_to_md(a.spec, base)
        elif a.cmd == "theme-from-pptx":
            r = core.theme_from_pptx(a.spec, a.name, a.out_dir, base)
        elif a.cmd == "layouts":
            r = core.layouts(a.spec, base)
        elif a.cmd == "theme-export":
            r = core.theme_export(a.name, a.format, base)
        else:  # pragma: no cover
            ap.error("알 수 없는 명령")
    except ValueError as e:
        sys.stderr.write(f"[docgen] DSL/파싱 오류: {e}\n")
        return 2
    except FileNotFoundError as e:
        sys.stderr.write(f"[docgen] 파일 없음: {e}\n")
        return 1
    _out(r, as_json)
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
