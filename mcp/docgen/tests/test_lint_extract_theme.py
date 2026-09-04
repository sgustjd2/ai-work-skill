import subprocess
import sys

import pytest

pytestmark = pytest.mark.deterministic


def test_lint_single_implementation():
    """FR-14: docgen.lint.lint 은 templates/doc_lint.py 의 lint 와 같은 객체."""
    from docgen import lint as L  # noqa: I001 - doc_lint 보다 먼저 import 되어야 sys.modules 등록
    import doc_lint

    assert doc_lint.lint is L.lint


def test_lint_doc_flags_dash_and_emoji(tmp_path):
    from docgen import lint as L

    style = tmp_path / "STYLE.md"
    style.write_text("---\nai_work_skill: 0.1\n---\n", encoding="utf-8")
    bad = tmp_path / "bad.doc.md"
    bad.write_text("혁신적인 솔루션 — 최고입니다! 🚀\n", encoding="utf-8")
    res = L.lint_doc(str(bad))
    codes = {f["code"] for f in res["hard"]}
    assert {"H1", "H2", "H6", "H7"} & codes
    assert res["path"].endswith("bad.doc.md")


def test_theme_color_and_contrast(theme):
    from docgen import theme as T

    assert T.color(theme, "primary").startswith("#")
    assert T.contrast_ratio(T.color(theme, "primary"), T.color(theme, "white")) > 4.5
    a, b = T.color(theme, "ink"), T.color(theme, "white")
    assert T.mix(a, b, 0.0) == a and T.mix(a, b, 1.0).upper() == b.upper()  # 양 끝 정확
    mid = T.mix(a, b, 0.5)
    assert T.relative_luminance(a) < T.relative_luminance(mid) < T.relative_luminance(b)


def test_theme_resolution_project_over_plugin(tmp_path):
    from docgen import theme as T

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "theme.json").write_text(
        (T._plugin_themes() / "datasolution.json")
        .read_text(encoding="utf-8")
        .replace('"datasolution"', '"proj"', 1),
        encoding="utf-8",
    )
    th = T.load_theme(None, base_dir=str(tmp_path))
    assert th["name"] == "proj"


def test_tokens_css_ramp(theme):
    from docgen import core

    r = core.theme_export("datasolution", "tokens-css")
    css = r["content"]
    for step in (100, 400, 700, 900):
        assert f"--ui-accent-{step}:" in css


def test_docx_to_md_and_pptx_to_md(theme, tmp_path, design_md, deck_md):
    from docgen import core, docx_render, parse, pptx_render

    dx = tmp_path / "d.docx"
    docx_render.render_docx(parse.parse_doc(design_md), str(dx), theme, base_dir=str(tmp_path))
    md = core.docx_to_md(str(dx))
    assert md["structure"]["tables"] >= 3
    assert "#" in md["markdown"]

    pp = tmp_path / "d.pptx"
    pptx_render.render_pptx(parse.parse_deck(deck_md), str(pp), theme, base_dir=str(tmp_path))
    pmd = core.pptx_to_md(str(pp))
    assert pmd["structure"]["slides"] == 8


def test_theme_from_pptx(theme, tmp_path, deck_md):
    from docgen import core, parse, pptx_render

    pp = tmp_path / "company.pptx"
    pptx_render.render_pptx(parse.parse_deck(deck_md), str(pp), theme, base_dir=str(tmp_path))
    res = core.theme_from_pptx(str(pp), "company", out_dir=str(tmp_path / "themes"))
    assert res["out_path"].endswith("company.json")
    assert "primary" in res["colors"]


def test_diagram_from_compose(tmp_path):
    from docgen import core

    comp = tmp_path / "compose.yaml"
    comp.write_text(
        "services:\n"
        "  api:\n    image: myorg/api\n    depends_on: [litellm, db]\n"
        "  litellm:\n    image: ghcr.io/berriai/litellm\n    depends_on: [db]\n"
        "  db:\n    image: pgvector/pgvector:pg16\n",
        encoding="utf-8",
    )
    res = core.diagram_from_compose(str(comp))
    kinds = {n["id"]: n["kind"] for n in res["spec"]["nodes"]}
    assert kinds["litellm"] == "gateway" and kinds["db"] == "data"
    assert {"from": "api", "to": "db"} in res["spec"]["edges"]


def test_cli_help_and_render(tmp_path):
    import os

    env = dict(os.environ)
    r = subprocess.run(
        [sys.executable, "-m", "docgen", "--help"],
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0 and "render-docx" in r.stdout


def test_cli_render_json(tmp_path, design_md):
    import json
    import os

    src = tmp_path / "d.doc.md"
    src.write_text(design_md, encoding="utf-8")
    out = tmp_path / "d.docx"
    env = dict(os.environ)
    r = subprocess.run(
        [sys.executable, "-m", "docgen", "--json", "render-docx", str(src), "--out", str(out)],
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["out_path"].endswith("d.docx")
    assert out.exists()
