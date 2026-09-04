"""FR-14: 린트는 단일 구현. templates/doc_lint.py 의 lint() 를 그대로 가져온다.

doc_lint 모듈을 sys.modules['doc_lint'] 에 등록하므로, 다른 곳에서 `import doc_lint`
해도 같은 모듈 객체를 얻는다 → `doc_lint.lint is docgen.lint.lint` (테스트가 확인).
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    # 우선순위: 환경변수 → __file__ 기준(.../mcp/docgen/docgen/lint.py → parents[3]) → cwd
    env = os.environ.get("AI_WORK_SKILL_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    try:
        cand = here.parents[3]
        if (cand / "templates" / "doc_lint.py").exists():
            return cand
    except IndexError:
        pass
    return Path.cwd()


def _load_doc_lint():
    if "doc_lint" in sys.modules:
        return sys.modules["doc_lint"]
    path = _repo_root() / "templates" / "doc_lint.py"
    if not path.exists():
        raise FileNotFoundError(
            f"doc_lint.py 를 찾을 수 없습니다: {path}. "
            "AI_WORK_SKILL_ROOT 를 저장소 루트로 설정하세요."
        )
    spec = importlib.util.spec_from_file_location("doc_lint", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["doc_lint"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


doc_lint = _load_doc_lint()

# 그대로 재노출 (재구현 금지)
lint = doc_lint.lint
classify = doc_lint.classify
is_prose_file = doc_lint.is_prose_file
parse_frontmatter = doc_lint.parse_frontmatter


def lint_doc(path: str, mode: str = "all", base_dir=None) -> dict:
    """산문 파일을 린트해 findings 를 hard/soft 로 나눠 돌려준다. (MCP lint_doc 툴)"""
    p = Path(path)
    if base_dir and not p.is_absolute():
        p = Path(base_dir) / p
    text = p.read_text(encoding="utf-8")
    findings = lint(text, str(p), soft=(mode != "hard"))
    hard = [f for f in findings if f.get("tier") == "hard"]
    soft = [f for f in findings if f.get("tier") == "soft"]
    return {"path": str(p.resolve()), "hard": hard, "soft": soft, "warnings": []}
