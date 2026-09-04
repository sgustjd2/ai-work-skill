import os
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
os.environ.setdefault("AI_WORK_SKILL_ROOT", str(REPO))
os.environ.setdefault("DOCGEN_PROJECT_DIR", str(REPO))

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture(scope="session")
def theme():
    from docgen import theme as T

    return T.load_theme("datasolution")


@pytest.fixture
def design_md():
    return (FIXTURES / "design.doc.md").read_text(encoding="utf-8")


@pytest.fixture
def deck_md():
    return (FIXTURES / "gateway.deck.md").read_text(encoding="utf-8")


@pytest.fixture
def sample_spec():
    return {
        "type": "architecture",
        "direction": "LR",
        "groups": [
            {"id": "p", "label": "플랫폼", "style": "highlight"},
            {"id": "e", "label": "외부"},
        ],
        "nodes": [
            {"id": "api", "label": "요약 API\\n(FastAPI)", "kind": "service", "group": "p"},
            {"id": "gw", "label": "LiteLLM", "kind": "gateway", "group": "p"},
            {"id": "az", "label": "Azure OpenAI", "kind": "external", "group": "e"},
            {"id": "loose", "label": "무그룹", "kind": "data"},
        ],
        "edges": [
            {"from": "api", "to": "gw", "label": "OpenAI 호환"},
            {"from": "gw", "to": "az", "label": "폴백", "style": "dashed"},
        ],
    }
