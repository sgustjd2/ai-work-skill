"""M2 스킬 스크립트 단위 테스트: import_graph, test_gaps, scaffold, route_table, ci_lint."""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.deterministic
ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str):
    p = ROOT / rel
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _pkg(tmp_path):
    root = tmp_path / "myapp"
    for d in ("api", "services", "infra"):
        (root / d).mkdir(parents=True)
        (root / d / "__init__.py").write_text("", encoding="utf-8")
    (root / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='myapp'\n[tool.ai-work]\nlayers = ['api', 'services', 'infra']\n",
        encoding="utf-8",
    )
    (root / "api" / "routes.py").write_text(
        "from myapp.services.svc import svc\ndef handler():\n    return svc()\n", encoding="utf-8"
    )
    (root / "services" / "svc.py").write_text(
        "from myapp.infra.db import db\n"
        "from myapp.api.routes import handler\n"
        "def svc():\n    return db()\n",
        encoding="utf-8",
    )
    (root / "infra" / "db.py").write_text("def db():\n    return 1\n", encoding="utf-8")
    return root


# ─── import_graph ────────────────────────────────────────────────────────────
def test_import_graph_cycle_and_layers(tmp_path):
    ig = _load("skills/py-refactor/scripts/import_graph.py")
    root = _pkg(tmp_path)
    r = ig.check(str(root))
    assert r["cycles"]  # routes <-> svc
    assert any(
        v["from_layer"] == "services" and v["to_layer"] == "api" for v in r["layer_violations"]
    )


def test_import_graph_clean(tmp_path):
    ig = _load("skills/py-refactor/scripts/import_graph.py")
    root = tmp_path / "clean"
    (root / "services").mkdir(parents=True)
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "services" / "__init__.py").write_text("", encoding="utf-8")
    (root / "services" / "a.py").write_text("def a():\n    return 1\n", encoding="utf-8")
    r = ig.check(str(root), layers=["api", "services", "infra"])
    assert r["cycles"] == [] and r["layer_violations"] == []


# ─── test_gaps ───────────────────────────────────────────────────────────────
def test_gaps_finds_unreferenced(tmp_path):
    tg = _load("skills/py-test/scripts/test_gaps.py")
    root = _pkg(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text(
        "from myapp.api.routes import handler\ndef test_h():\n    assert handler\n",
        encoding="utf-8",
    )
    r = tg.check(str(root))
    flat = {n for names in r["gaps"].values() for n in names}
    assert "svc" in flat and "db" in flat and "handler" not in flat


# ─── scaffold ────────────────────────────────────────────────────────────────
def test_scaffold_base(tmp_path):
    sc = _load("skills/fastapi-service/scripts/scaffold.py")
    sc.scaffold("myapi", str(tmp_path / "svc"), "요약 API", {}, force=True)
    root = tmp_path / "svc"
    assert (root / "myapi" / "main.py").exists()
    assert (root / "pyproject.toml").exists()
    # 옵션 파일은 없어야 한다
    assert not (root / "myapi" / "api" / "v1" / "rag.py").exists()
    assert not (root / "myapi" / "infra").exists()
    # 템플릿 토큰 치환: Dockerfile CMD 와 conftest 가 패키지명을 참조
    assert "myapi.main:app" in (root / "Dockerfile").read_text(encoding="utf-8")
    assert "myapi.main" in (root / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "__pkg__" not in "".join(p.name for p in root.rglob("*"))
    assert "sqlalchemy" not in (root / "pyproject.toml").read_text(encoding="utf-8")


def test_scaffold_options(tmp_path):
    sc = _load("skills/fastapi-service/scripts/scaffold.py")
    sc.scaffold(
        "full",
        str(tmp_path / "svc"),
        None,
        {"with_rag": True, "with_sse": True, "with_jobs": True},
        True,
    )
    root = tmp_path / "svc"
    assert (root / "full" / "api" / "v1" / "rag.py").exists()
    assert (root / "full" / "infra" / "db.py").exists()  # rag 는 db 를 함의
    assert (root / "full" / "api" / "v1" / "chat_stream.py").exists()
    assert (root / "full" / "services" / "jobs.py").exists()
    pp = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert "sqlalchemy" in pp
    assert "pgvector" in (root / "compose.yaml").read_text(encoding="utf-8")
    # 마커 줄이 제거됐는지
    assert "# scaffold:" not in (root / "full" / "api" / "v1" / "rag.py").read_text(
        encoding="utf-8"
    )


# ─── route_table (fastapi 없이 순수 로직) ────────────────────────────────────
class _FakeApp:
    def openapi(self):
        return {
            "paths": {
                "/api/v1/chat": {
                    "post": {
                        "tags": ["chat"],
                        "operationId": "chat",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/ChatResponse"}
                                    }
                                }
                            }
                        },
                    }
                },
                "/api/v1/healthz": {
                    "get": {"tags": ["health"], "operationId": "healthz", "responses": {}}
                },
            }
        }


def test_route_table_openapi():
    rt = _load("skills/fastapi-service/scripts/route_table.py")
    rows = rt.routes(_FakeApp())
    assert len(rows) == 2
    chat = next(r for r in rows if r["path"] == "/api/v1/chat")
    assert (
        chat["method"] == "POST"
        and chat["response_model"] == "ChatResponse"
        and chat["tags"] == "chat"
    )
    md = rt.md_table(rows)
    assert md.count("|") >= 12 and "메서드" in md


# ─── ci_lint ─────────────────────────────────────────────────────────────────
def test_ci_lint_undefined_stage():
    cl = _load("skills/gitlab-ci/scripts/ci_lint.py")
    r = cl.local_check("stages:\n  - build\n\njob:\n  stage: deploy\n  script:\n    - echo hi\n")
    assert not r["valid"]
    assert any("deploy" in e for e in r["errors"])


def test_ci_lint_ok():
    cl = _load("skills/gitlab-ci/scripts/ci_lint.py")
    good = (ROOT / "skills/gitlab-ci/assets/gitlab-ci.yml").read_text(encoding="utf-8")
    r = cl.local_check(good)
    assert r["valid"], r["errors"]


def test_ci_lint_tab():
    cl = _load("skills/gitlab-ci/scripts/ci_lint.py")
    r = cl.local_check("stages:\n\t- build\n")
    assert not r["valid"] and any("탭" in e for e in r["errors"])


@pytest.mark.manual
def test_scaffold_service_runs(tmp_path):
    """생성 골격이 실제로 uv sync + pytest 를 통과하는지(네트워크 필요, 수동)."""
    import subprocess
    import sys

    sc = _load("skills/fastapi-service/scripts/scaffold.py")
    sc.scaffold("svc_it", str(tmp_path / "svc"), "요약 API", {}, True)
    root = tmp_path / "svc"
    subprocess.run(["uv", "sync", "--quiet"], cwd=root, check=True, timeout=600)
    r = subprocess.run(
        ["uv", "run", "pytest", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=300,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert sys is not None
