import copy

import pytest

from docgen.diagram import layout, mermaid, png, svg

pytestmark = pytest.mark.deterministic


def test_layout_deterministic(sample_spec):
    a = layout.build_layout(sample_spec)
    b = layout.build_layout(copy.deepcopy(sample_spec))
    assert [n["x"] for n in a["nodes"]] == [n["x"] for n in b["nodes"]]
    assert a["width"] == b["width"]


def test_ungrouped_node_placed(sample_spec):
    lay = layout.build_layout(sample_spec)
    ids = {n["id"] for n in lay["nodes"]}
    assert "loose" in ids  # 무그룹 노드도 배치됨


def test_multiline_label_height(sample_spec):
    lay = layout.build_layout(sample_spec)
    api = next(n for n in lay["nodes"] if n["id"] == "api")
    gw = next(n for n in lay["nodes"] if n["id"] == "gw")
    assert api["h"] > gw["h"]  # 2줄 라벨이 더 높다
    assert api["lines"] == ["요약 API", "(FastAPI)"]


def test_edge_warning_for_missing_node():
    spec = {"nodes": [{"id": "a", "label": "A"}], "edges": [{"from": "a", "to": "ghost"}]}
    lay = layout.build_layout(spec)
    assert any("ghost" in w for w in lay["warnings"])


def test_node_count_warning():
    spec = {"nodes": [{"id": f"n{i}", "label": str(i)} for i in range(21)], "edges": []}
    lay = layout.build_layout(spec)
    assert any(">20" in w for w in lay["warnings"])


def test_mermaid_string(sample_spec, theme):
    mm, meta = mermaid.to_mermaid(sample_spec, theme)
    assert mm.startswith("flowchart LR")
    assert "classDef gateway" in mm
    assert "-." in mm and ".->" in mm  # 점선(라벨 있는) 폴백 엣지: gw -. 폴백 .-> az
    assert "요약 API<br/>(FastAPI)" in mm
    assert meta["nodes"] == 4


def test_svg_string(sample_spec, theme):
    s, meta = svg.to_svg(sample_spec, theme)
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>")
    assert "polygon" in s  # 화살촉


def test_png_created(sample_spec, theme, tmp_path):
    out = tmp_path / "d.png"
    p, warns = png.to_png(sample_spec, theme, str(out), dpi=120)
    # 폰트가 있으면 PNG, 없으면 None+경고 (둘 다 정상)
    if p:
        assert out.exists() and out.stat().st_size > 0
    else:
        assert any("폰트" in w for w in warns)


def test_png_font_missing_fallback(sample_spec, theme, tmp_path):
    th = copy.deepcopy(theme)
    th["fonts"]["font_paths"] = ["/nonexistent/font.ttf"]
    # 공통 폰트 경로 목록을 비워 "폰트 없음" 상황을 강제한다.
    import docgen.diagram.png as pmod

    orig = pmod._COMMON_FONTS
    pmod._COMMON_FONTS = []
    try:
        p, warns = png.to_png(sample_spec, th, str(tmp_path / "x.png"), dpi=100)
        assert p is None
        assert any("폰트" in w for w in warns)
    finally:
        pmod._COMMON_FONTS = orig
