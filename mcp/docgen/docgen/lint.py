"""FR-14: doc_lint 을 그대로 import 한다(단일 구현). 드리프트는 테스트가 막는다.

templates/doc_lint.py 는 표준 라이브러리 훅이자 CLI 다. docgen 은 같은 lint() 함수를 재사용한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

# mcp/docgen/docgen/lint.py -> parents[3] = 저장소(플러그인) 루트 -> templates/
_TEMPLATES = Path(__file__).resolve().parents[3] / "templates"
if str(_TEMPLATES) not in sys.path:
    sys.path.insert(0, str(_TEMPLATES))

import doc_lint  # noqa: E402

lint = doc_lint.lint  # 같은 함수 객체(assert docgen.lint.lint is doc_lint.lint)


def lint_doc(path, mode="all", base_dir="."):
    """산문 파일을 검사해 {hard, soft, warnings} 로 돌려준다. MCP/CLI 의 lint_doc 툴."""
    p = Path(path)
    cfg = doc_lint.find_config(str(p.resolve()), base_dir) or {}
    text = p.read_text(encoding="utf-8", errors="replace")
    findings = lint(text, str(p), cfg, soft=(mode != "hard"))
    return {
        "path": str(p.resolve()),
        "hard": [f for f in findings if f["tier"] == "hard"],
        "soft": [f for f in findings if f["tier"] == "soft"],
        "warnings": [],
    }
