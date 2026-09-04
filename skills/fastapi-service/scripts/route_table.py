#!/usr/bin/env python3
"""route_table.py — FastAPI 앱의 라우트를 표로 덤프한다 (FR-20).

앱을 import 해 메서드·경로·태그·이름·응답 모델을 뽑는다. 설계서의 인터페이스 표 입력용.
스크립트 자체는 표준 라이브러리만 쓰지만, 대상 앱을 import 하므로 그 프로젝트 환경에서 실행한다.

  python route_table.py [--app pkg.main:create_app] [--openapi out.json] [--md]
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path


def load_app(spec: str):
    mod_name, _, attr = spec.partition(":")
    attr = attr or "app"
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)  # 프로젝트 루트에서 실행하는 로컬 패키지 import
    module = importlib.import_module(mod_name)
    obj = getattr(module, attr)
    return obj() if callable(obj) and not _is_app(obj) else obj


def _is_app(obj) -> bool:
    return obj.__class__.__name__ == "FastAPI" or hasattr(obj, "openapi")


def _resp_model(op: dict) -> str:
    try:
        schema = op["responses"]["200"]["content"]["application/json"]["schema"]
    except (KeyError, TypeError):
        return ""
    ref = schema.get("$ref") or schema.get("items", {}).get("$ref", "")
    return ref.rsplit("/", 1)[-1] if ref else ""


def routes(app) -> list[dict]:
    """openapi() 로 최종 경로·메서드를 뽑는다(include_router 중첩·prefix 를 정확히 반영)."""
    spec = app.openapi()
    out = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if not isinstance(op, dict) or method.lower() not in (
                "get",
                "post",
                "put",
                "patch",
                "delete",
            ):
                continue
            out.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "name": op.get("operationId", ""),
                    "tags": ",".join(op.get("tags", [])),
                    "response_model": _resp_model(op),
                }
            )
    return sorted(out, key=lambda x: (x["path"], x["method"]))


def md_table(rows: list[dict]) -> str:
    head = "| 메서드 | 경로 | 태그 | 이름 | 응답 모델 | 설명 |"
    sep = "|---|---|---|---|---|---|"
    lines = [head, sep]
    for r in rows:
        cells = [r["method"], r["path"], r["tags"], r["name"], r["response_model"], ""]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="FastAPI 라우트 표 덤프")
    ap.add_argument("--app", default="app.main:create_app")
    ap.add_argument("--openapi", default=None, help="openapi.json 저장 경로")
    ap.add_argument("--md", action="store_true", help="인터페이스 정의서용 GFM 표")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        app = load_app(a.app)
    except (ImportError, AttributeError) as e:
        sys.stderr.write(f"[route-table] 앱을 불러올 수 없습니다({a.app}): {e}\n")
        return 1
    rows = routes(app)
    if a.openapi:
        Path(a.openapi).write_text(
            json.dumps(app.openapi(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    if a.json:
        sys.stdout.write(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    elif a.md:
        sys.stdout.write(md_table(rows) + "\n")
    else:
        for r in rows:
            sys.stdout.write(f"{r['method']:8} {r['path']:32} {r['tags']:12} {r['name']}\n")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
