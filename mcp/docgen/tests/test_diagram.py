"""구성도 레이아웃 결정성 + mermaid 출력."""

from docgen.diagram import layout as L
from docgen.diagram import mermaid as M
from docgen.theme import load_theme

SPEC = {
    "type": "architecture",
    "direction": "LR",
    "groups": [{"id": "g1", "label": "채널"}],
    "nodes": [
        {"id": "web", "label": "웹 포털", "kind": "ui", "group": "g1"},
        {"id": "api", "label": "요약 API\\n(FastAPI)", "kind": "service", "group": "g1"},
        {"id": "gw", "label": "Gateway", "kind": "gateway"},
    ],
    "edges": [
        {"from": "web", "to": "api", "label": "HTTPS"},
        {"from": "api", "to": "gw", "style": "dashed"},
    ],
}


def test_layout_deterministic():
    a = L.layout(SPEC)
    b = L.layout(SPEC)
    assert a == b
    assert a["nodes"]["web"]["w"] == 1.9
    assert a["nodes"]["gw"]["group"] == L.IMPLICIT
    assert a["width"] > 0 and a["height"] > 0


def test_layout_multiline_taller():
    # api 는 2줄 라벨이라 web 보다 높다
    a = L.layout(SPEC)
    assert a["nodes"]["api"]["h"] > a["nodes"]["web"]["h"]


def test_layout_warns_over_20_nodes():
    spec = {"nodes": [{"id": f"n{i}", "label": str(i)} for i in range(21)]}
    assert any("20" in w for w in L.layout(spec)["warnings"])


def test_png_render(tmp_path):
    from docgen.diagram import png

    theme = load_theme("datasolution", ".")
    out = tmp_path / "d.png"
    res = png.render_png(SPEC, theme, str(out))
    if png.find_font(theme) is None:
        assert res is None  # 폰트 없으면 None(호출부가 mermaid 로 대체)
    else:
        assert res and out.is_file() and out.stat().st_size > 0
        from PIL import Image

        assert Image.open(str(out)).size[0] > 0


def test_mermaid_output():
    theme = load_theme("datasolution", ".")
    s = M.to_mermaid(SPEC, theme)
    assert s.startswith("flowchart LR")
    assert 'web["웹 포털"]' in s
    assert "요약 API<br/>(FastAPI)" in s  # \n -> <br/>
    assert "-.->|" not in s and "-.->" in s  # dashed edge (라벨 없음)
    assert "subgraph g1" in s
    assert "classDef gateway" in s
    assert "class gw gateway" in s
