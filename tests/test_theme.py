"""테마 JSON 스키마 검증 + 렌더러·훅 소스에 hex 리터럴 0개. PRD 12.1, 16-4."""

import json
import re
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")


def test_theme_matches_schema():
    theme = json.loads((ROOT / "themes" / "datasolution.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "themes" / "theme.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(theme, schema)  # 예외 없으면 통과


def test_theme_colors_are_hex():
    theme = json.loads((ROOT / "themes" / "datasolution.json").read_text(encoding="utf-8"))
    for name, val in theme["colors"].items():
        assert re.fullmatch(r"#[0-9A-Fa-f]{6}", val), f"{name} = {val}"


def test_no_hex_literals_in_sources():
    # 렌더러·훅·스크립트 소스에는 hex 색 리터럴이 없어야 한다(색은 테마 JSON 에만).
    sources = list((ROOT / "templates").glob("*.py"))
    sources += list((ROOT / "skills").rglob("scripts/*.py"))
    sources += list((ROOT / "mcp").rglob("*.py")) if (ROOT / "mcp").exists() else []
    offenders = []
    for f in sources:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if HEX.search(line):
                offenders.append(f"{f.relative_to(ROOT)}:{i} {line.strip()}")
    assert not offenders, "hex 리터럴 발견:\n" + "\n".join(offenders)
