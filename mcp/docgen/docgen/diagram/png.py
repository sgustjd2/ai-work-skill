"""구성도 -> PNG(Pillow). docx 삽입용. 한글 폰트가 없으면 None(호출부가 mermaid 로 대체).

폰트 탐색: 테마 font_paths -> DOCGEN_FONT_DIRS -> malgun/Nanum/AppleSDGothic. 좌표는 layout().
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..theme import color, rgb_tuple
from .layout import kind_style, label_lines, layout

_DEFAULT_FONTS = [
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]


def find_font(theme):
    cands = list(theme.get("fonts", {}).get("font_paths", []))
    for d in os.environ.get("DOCGEN_FONT_DIRS", "").split(os.pathsep):
        if d:
            cands += [str(p) for p in Path(d).glob("*.tt?")]
    cands += _DEFAULT_FONTS
    for c in cands:
        if c and Path(c).is_file():
            return c
    return None


def _c(theme, role):
    return rgb_tuple(color(theme, role))


def render_png(spec, theme, out_path, dpi=200):
    font_path = find_font(theme)
    lay = layout(spec)
    warnings = list(lay["warnings"])
    if not font_path:
        return None
    margin = 0.35
    W = max(int((lay["width"] + 2 * margin) * dpi), dpi)
    H = max(int((lay["height"] + 2 * margin) * dpi), dpi)
    img = Image.new("RGB", (W, H), _c(theme, "white"))
    draw = ImageDraw.Draw(img)
    off = int(margin * dpi)

    def px(v):
        return int(v * dpi) + off

    node_font = ImageFont.truetype(font_path, int(0.15 * dpi))
    group_font = ImageFont.truetype(font_path, int(0.12 * dpi))
    edge_font = ImageFont.truetype(font_path, int(0.11 * dpi))
    radius = int(0.1 * dpi)

    for g in lay["groups"]:
        if g.get("label"):
            draw.rounded_rectangle(
                [px(g["x"]), px(g["y"]), px(g["x"] + g["w"]), px(g["y"] + g["h"])],
                radius=radius,
                outline=_c(theme, "line"),
                width=1,
            )
            draw.text(
                (px(g["x"]) + 6, px(g["y"]) + 4),
                g["label"],
                fill=_c(theme, "ink_subtle"),
                font=group_font,
            )

    centers = {
        nid: (px(n["x"] + n["w"] / 2), px(n["y"] + n["h"] / 2)) for nid, n in lay["nodes"].items()
    }
    for e in lay["edges"]:
        if e["from"] in centers and e["to"] in centers:
            _edge(draw, centers[e["from"]], centers[e["to"]], e, theme, edge_font)

    for _nid, n in lay["nodes"].items():
        st = kind_style(theme, n["kind"])
        box = [px(n["x"]), px(n["y"]), px(n["x"] + n["w"]), px(n["y"] + n["h"])]
        draw.rounded_rectangle(
            box, radius=radius, fill=_rgb(st["fill"]), outline=_rgb(st["stroke"]), width=2
        )
        _centered(draw, box, label_lines(n["label"]), node_font, _rgb(st["text"]))

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return {
        "out_path": str(Path(out_path).resolve()),
        "nodes": len(lay["nodes"]),
        "edges": len(lay["edges"]),
        "warnings": warnings,
    }


def _rgb(hexstr):
    return rgb_tuple(hexstr)


def _edge(draw, a, b, edge, theme, font):
    col = _c(theme, "ink_muted")
    if edge.get("dashed"):
        _dashed_line(draw, a, b, col, 2)
    else:
        draw.line([a, b], fill=col, width=2)
    _arrowhead(draw, a, b, col)
    if edge.get("label"):
        mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
        tb = draw.textbbox((mx, my), edge["label"], font=font, anchor="mm")
        draw.rectangle([tb[0] - 3, tb[1] - 1, tb[2] + 3, tb[3] + 1], fill=_c(theme, "white"))
        draw.text((mx, my), edge["label"], fill=_c(theme, "ink"), font=font, anchor="mm")


def _dashed_line(draw, a, b, col, width, dash=10, gap=7):
    dist = math.hypot(b[0] - a[0], b[1] - a[1])
    if dist == 0:
        return
    dx, dy = (b[0] - a[0]) / dist, (b[1] - a[1]) / dist
    n = 0
    while n < dist:
        s = (a[0] + dx * n, a[1] + dy * n)
        e = (a[0] + dx * min(n + dash, dist), a[1] + dy * min(n + dash, dist))
        draw.line([s, e], fill=col, width=width)
        n += dash + gap


def _arrowhead(draw, a, b, col, size=12):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for da in (-0.4, 0.4):
        x = b[0] - size * math.cos(ang + da)
        y = b[1] - size * math.sin(ang + da)
        draw.line([b, (x, y)], fill=col, width=2)


def _centered(draw, box, lines, font, col):
    cx = (box[0] + box[2]) // 2
    cy = (box[1] + box[3]) // 2
    lh = font.size + 4
    total = lh * len(lines)
    y = cy - total // 2 + lh // 2
    for line in lines:
        draw.text((cx, y), line, fill=col, font=font, anchor="mm")
        y += lh
