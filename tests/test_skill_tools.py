"""스킬 allowed-tools 가 GitLab MCP 서버 전체를 허용하지 않는다(쓰기 툴도 열린다)."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))


@pytest.mark.parametrize("path", SKILLS, ids=lambda p: p.parent.name)
def test_no_server_wide_gitlab_grant(path):
    front = path.read_text(encoding="utf-8").split("---")[1]
    lines = [ln.strip() for ln in front.splitlines()]
    assert "- mcp__gitlab" not in lines, "mcp__gitlab__<툴> 로 조회 툴만 적는다"
