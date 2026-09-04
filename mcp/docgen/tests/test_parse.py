import pytest

from docgen import parse

pytestmark = pytest.mark.deterministic


def _bt(blocks, t):
    return [b for b in blocks if b["type"] == t]


def test_frontmatter_and_headings(design_md):
    r = parse.parse_doc(design_md)
    assert r["frontmatter"]["doc_type"] == "설계서"
    assert r["frontmatter"]["title"].startswith("사내 LLM")
    hs = _bt(r["blocks"], "heading")
    assert hs[0]["level"] == 1 and hs[0]["text"].startswith("1. 개요")


def test_inline_runs_bold_code():
    r = parse.parse_doc("본문 **굵게** 와 `코드` 다.")
    runs = _bt(r["blocks"], "paragraph")[0]["runs"]
    assert any(x["bold"] for x in runs)
    assert any(x["code"] for x in runs)


def test_table_alignment_and_caption(design_md):
    r = parse.parse_doc(design_md)
    tables = _bt(r["blocks"], "table")
    # 대안 비교 표: 숫자 열이 오른쪽 정렬
    align_sets = [t["align"] for t in tables]
    assert any("right" in a for a in align_sets)
    assert any(t.get("caption") for t in tables)


def test_nested_list():
    r = parse.parse_doc("- a\n- b\n  - b1\n  - b2\n")
    lst = _bt(r["blocks"], "list")[0]
    assert lst["ordered"] is False
    b = lst["items"][1]
    assert len(b["children"]) == 2
    assert b["children"][0]["level"] == 1


def test_diagram_timeline_chart_blocks(design_md):
    r = parse.parse_doc(design_md)
    d = _bt(r["blocks"], "diagram")
    assert d and len(d[0]["spec"]["nodes"]) == 6
    assert len(d[0]["spec"]["edges"]) == 5


def test_chart_and_timeline_specs(deck_md):
    r = parse.parse_deck(deck_md)
    charts = [b for s in r["slides"] for b in s["blocks"] if b["type"] == "chart"]
    assert charts and charts[0]["spec"]["type"] == "bar"
    tls = [b for s in r["slides"] for b in s["blocks"] if b["type"] == "timeline"]
    assert tls and len(tls[0]["spec"]["tasks"]) == 3


def test_footnotes():
    r = parse.parse_doc("본문[^1]\n\n[^1]: 각주다\n")
    assert r["footnotes"] and r["footnotes"][0]["id"] == "1"


def test_bad_diagram_yaml_raises():
    with pytest.raises(ValueError):
        parse.parse_doc("```diagram\n: : : not yaml\n  - [\n```\n")


def test_deck_split_and_layout_inference(deck_md):
    r = parse.parse_deck(deck_md)
    titles = [(s["title"], s["layout"]) for s in r["slides"]]
    layouts = dict(titles)
    assert layouts["목표 아키텍처"] == "diagram"
    assert layouts["비용 비교"] == "chart"
    assert layouts["대안 비교"] == "table"
    assert layouts["추진 일정"] == "timeline"
    assert layouts["요청 사항"] == "closing"  # 명시 layout


def test_deck_headline_and_notes(deck_md):
    r = parse.parse_deck(deck_md)
    first = r["slides"][0]
    assert first["headline"].startswith("모델별 API 키가")
    assert "소유자 불명" in first["notes"]


def test_two_col():
    deck = (
        "---\ntitle: t\n---\n# s\n## h\n"
        "<!-- col -->\n### 왼쪽\n- a\n"
        "<!-- col -->\n### 오른쪽\n- b\n"
    )
    r = parse.parse_deck(deck)
    s = r["slides"][0]
    assert s["layout"] == "two-col"
    assert s["columns"] and len(s["columns"]) == 2
