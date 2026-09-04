"""배치 → PNG(Pillow). 한글 폰트를 찾지 못하면 (None, 경고) — docx 는 mermaid 텍스트로 대체."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .. import theme as T
from .layout import KIND_STYLE, build_layout

_COMMON_FONTS = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/malgunsl.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]


def find_font_path(theme: dict) -> str | None:
    for p in list(T.font_paths(theme)) + _COMMON_FONTS:
        if p and Path(p).exists():
            return p
    return None


def _font(path: str | None, size: int):
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _tint_fill(theme: dict, kind: str) -> tuple[int, int, int]:
    role = KIND_STYLE[kind]["fill"]
    hexv = T.tint(theme, "accent", 0.9) if role == "llm_tint" else T.color(theme, role)
    return T.rgb_tuple(hexv)


def _text_w(draw, s, font) -> float:
    try:
        b = draw.textbbox((0, 0), s, font=font)
        return b[2] - b[0]
    except Exception:  # noqa: BLE001
        return len(s) * font.size * 0.6


def to_png(spec: dict, theme: dict, out_path: str, dpi: int = 150) -> tuple[str | None, list[str]]:
    lay = build_layout(spec)
    warnings = list(lay["warnings"])
    font_path = find_font_path(theme)
    if font_path is None:
        warnings.append(
            "한글 폰트를 찾지 못해 PNG 를 만들지 않았습니다. 테마 font_paths 에 폰트 경로를 "
            "넣거나 맑은 고딕/나눔고딕을 설치하세요. (docx 는 mermaid 텍스트로 대체됩니다)"
        )
        return None, warnings

    scale = dpi
    W = int(lay["width"] * scale)
    H = int(lay["height"] * scale)
    img = Image.new("RGB", (W, H), T.rgb_tuple(T.color(theme, "white")))
    d = ImageDraw.Draw(img)
    node_font = _font(font_path, int(0.16 * scale))
    small_font = _font(font_path, int(0.12 * scale))
    ink = T.rgb_tuple(T.color(theme, "ink"))
    line_c = T.rgb_tuple(T.color(theme, "line"))

    def px(v):
        return v * scale

    for g in lay["groups"]:
        if not g["label"]:
            continue
        hi = str(g.get("style", "")).lower() == "highlight"
        gc = T.rgb_tuple(T.color(theme, "accent")) if hi else line_c
        d.rounded_rectangle(
            [px(g["x"]), px(g["y"]), px(g["x"] + g["w"]), px(g["y"] + g["h"])],
            radius=int(0.08 * scale),
            outline=gc,
            width=2,
        )
        d.text(
            (px(g["x"]) + 6, px(g["y"]) + 4),
            g["label"],
            fill=T.rgb_tuple(T.color(theme, "ink_muted")),
            font=small_font,
        )

    for e in lay["edges"]:
        x1, y1, x2, y2 = px(e["x1"]), px(e["y1"]), px(e["x2"]), px(e["y2"])
        dashed = str(e.get("style", "")).lower() == "dashed"
        _line(d, x1, y1, x2, y2, ink, dashed)
        _arrow(d, x1, y1, x2, y2, ink, scale)
        if e["label"]:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            tw = _text_w(d, e["label"], small_font)
            d.rectangle(
                [
                    mx - tw / 2 - 2,
                    my - small_font.size / 2 - 1,
                    mx + tw / 2 + 2,
                    my + small_font.size / 2 + 1,
                ],
                fill=T.rgb_tuple(T.color(theme, "white")),
            )
            d.text(
                (mx - tw / 2, my - small_font.size / 2),
                e["label"],
                fill=T.rgb_tuple(T.color(theme, "ink_muted")),
                font=small_font,
            )

    for n in lay["nodes"]:
        st = KIND_STYLE[n["kind"]]
        x0, y0, x1, y1 = px(n["x"]), px(n["y"]), px(n["x"] + n["w"]), px(n["y"] + n["h"])
        d.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=int(0.08 * scale),
            fill=_tint_fill(theme, n["kind"]),
            outline=T.rgb_tuple(T.color(theme, st["stroke"])),
            width=2,
        )
        tc = T.rgb_tuple(T.color(theme, st["text"]))
        lines = n["lines"]
        cy = (y0 + y1) / 2 - (len(lines) - 1) * node_font.size * 0.65
        for ln in lines:
            tw = _text_w(d, ln, node_font)
            d.text(((x0 + x1) / 2 - tw / 2, cy - node_font.size / 2), ln, fill=tc, font=node_font)
            cy += node_font.size * 1.3

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, dpi=(dpi, dpi))
    return out_path, warnings


def _line(d, x1, y1, x2, y2, color, dashed):
    if not dashed:
        d.line([x1, y1, x2, y2], fill=color, width=2)
        return
    total = math.hypot(x2 - x1, y2 - y1)
    if total == 0:
        return
    ux, uy = (x2 - x1) / total, (y2 - y1) / total
    seg, gap, dist = 8, 5, 0.0
    while dist < total:
        a = dist
        b = min(dist + seg, total)
        d.line([x1 + ux * a, y1 + uy * a, x1 + ux * b, y1 + uy * b], fill=color, width=2)
        dist += seg + gap


def _arrow(d, x1, y1, x2, y2, color, scale):
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 0.09 * scale
    p1 = (x2 - size * math.cos(ang - math.pi / 7), y2 - size * math.sin(ang - math.pi / 7))
    p2 = (x2 - size * math.cos(ang + math.pi / 7), y2 - size * math.sin(ang + math.pi / 7))
    d.polygon([(x2, y2), p1, p2], fill=color)
