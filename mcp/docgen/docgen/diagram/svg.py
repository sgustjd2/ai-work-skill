"""배치 → SVG 문자열(의존성 0). 미리보기·경량 삽입용."""

from __future__ import annotations

import math

from .. import theme as T
from .layout import KIND_STYLE, build_layout

PX = 96.0  # inch → px


def _fill(theme: dict, kind: str) -> str:
    role = KIND_STYLE[kind]["fill"]
    return T.tint(theme, "accent", 0.9) if role == "llm_tint" else T.color(theme, role)


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_svg(spec: dict, theme: dict) -> tuple[str, dict]:
    lay = build_layout(spec)
    w = lay["width"] * PX
    h = lay["height"] * PX
    ink = T.color(theme, "ink")
    line_c = T.color(theme, "line")
    muted = T.color(theme, "ink_muted")
    white_c = T.color(theme, "white")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
        f'viewBox="0 0 {w:.0f} {h:.0f}" font-family="sans-serif">'
    ]

    for g in lay["groups"]:
        if not g["label"]:
            continue
        gx, gy, gw, gh = (g[k] * PX for k in ("x", "y", "w", "h"))
        dash = ' stroke-dasharray="6 4"' if str(g.get("style", "")).lower() == "highlight" else ""
        gstroke = (
            T.color(theme, "accent") if str(g.get("style", "")).lower() == "highlight" else line_c
        )
        parts.append(
            f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh:.1f}" rx="8" '
            f'fill="none" stroke="{gstroke}"{dash}/>'
        )
        parts.append(
            f'<text x="{gx + 8:.1f}" y="{gy + 16:.1f}" font-size="11" fill="{muted}">'
            f"{_esc(g['label'])}</text>"
        )

    for e in lay["edges"]:
        x1, y1, x2, y2 = (e[k] * PX for k in ("x1", "y1", "x2", "y2"))
        dashed = str(e.get("style", "")).lower() == "dashed"
        da = ' stroke-dasharray="5 4"' if dashed else ""
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{ink}"{da}/>'
        )
        parts.append(_arrow(x1, y1, x2, y2, ink))
        if e["label"]:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            parts.append(
                f'<rect x="{mx - len(e["label"]) * 3.4 - 2:.1f}" y="{my - 8:.1f}" '
                f'width="{len(e["label"]) * 6.8 + 4:.1f}" height="14" fill="{white_c}"/>'
            )
            parts.append(
                f'<text x="{mx:.1f}" y="{my + 3:.1f}" font-size="10" text-anchor="middle" '
                f'fill="{muted}">{_esc(e["label"])}</text>'
            )

    for n in lay["nodes"]:
        st = KIND_STYLE[n["kind"]]
        x, y, nw, nh = (n[k] * PX for k in ("x", "y", "w", "h"))
        stroke = T.color(theme, st["stroke"])
        dash = ' stroke-dasharray="5 4"' if st["dashed"] else ""
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{nw:.1f}" height="{nh:.1f}" rx="8" '
            f'fill="{_fill(theme, n["kind"])}" stroke="{stroke}" stroke-width="1.5"{dash}/>'
        )
        tc = T.color(theme, st["text"])
        lines = n["lines"]
        cy = y + nh / 2 - (len(lines) - 1) * 8
        for ln in lines:
            parts.append(
                f'<text x="{x + nw / 2:.1f}" y="{cy + 4:.1f}" font-size="12" text-anchor="middle" '
                f'fill="{tc}">{_esc(ln)}</text>'
            )
            cy += 16

    parts.append("</svg>")
    return "\n".join(parts), {"warnings": lay["warnings"]}


def _arrow(x1, y1, x2, y2, color) -> str:
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 8
    p1 = (x2 - size * math.cos(ang - math.pi / 7), y2 - size * math.sin(ang - math.pi / 7))
    p2 = (x2 - size * math.cos(ang + math.pi / 7), y2 - size * math.sin(ang + math.pi / 7))
    pts = f"{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return f'<polygon points="{pts}" fill="{color}"/>'
