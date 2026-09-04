"""의존성 정책: templates/ 와 skills/*/scripts/ 는 표준 라이브러리만 import. PRD 16-3, CLAUDE.md."""

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
STDLIB = set(sys.stdlib_module_names)


def _sources():
    files = list((ROOT / "templates").glob("*.py"))
    files += list((ROOT / "skills").rglob("scripts/*.py"))
    return files


def _top_imports(tree):
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
    return mods


@pytest.mark.parametrize("path", _sources(), ids=lambda p: str(p.relative_to(ROOT)))
def test_stdlib_only(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    third_party = _top_imports(tree) - STDLIB - {"__future__"}
    assert not third_party, f"{path.name} 가 표준 라이브러리 밖을 import: {third_party}"
