"""구성도 레이아웃(공통). 열(LR)/행(TB) 기반 결정적 배치. pptx 도형·PNG 가 이 좌표를 받는다.

# ponytail: 열 기반 단순 배치, 20노드 넘으면 grandalf 등 그래프 레이아웃 검토(D9).
"""

from __future__ import annotations

from collections import OrderedDict

from ..theme import color, tint

NODE_W = 1.9
NODE_H = 0.8
LINE_EXTRA = 0.25
GROUP_PAD = 0.25
GROUP_GAP = 0.6
NODE_GAP = 0.35
IMPLICIT = "__implicit__"


def kind_style(theme, kind):
    """kind 6종 -> 테마 색 역할. 색은 전부 테마에서 온다."""

    def c(role):
        return color(theme, role)

    table = {
        "ui": {"fill": c("surface_alt"), "stroke": c("primary"), "text": c("ink")},
        "service": {"fill": c("white"), "stroke": c("primary"), "text": c("primary")},
        "gateway": {"fill": c("primary"), "stroke": c("primary"), "text": c("white")},
        "data": {"fill": c("surface"), "stroke": c("primary"), "text": c("ink")},
        "external": {
            "fill": c("white"),
            "stroke": c("ink_muted"),
            "text": c("ink_muted"),
            "dashed": True,
        },
        "llm": {"fill": tint(c("accent"), 0.12), "stroke": c("accent"), "text": c("ink")},
    }
    base = {"fill": c("white"), "stroke": c("primary"), "text": c("ink"), "dashed": False}
    base.update(table.get(kind, table["service"]))
    return base


def label_lines(label):
    return str(label).split("\\n")  # YAML plain scalar 의 리터럴 backslash-n


def _node_h(node):
    return NODE_H + (len(label_lines(node.get("label", ""))) - 1) * LINE_EXTRA


def _r(v):
    return round(v, 3)


def _grouped(spec):
    grouped = OrderedDict()
    labels, styles = {}, {}
    for g in spec.get("groups") or []:
        grouped[g["id"]] = []
        labels[g["id"]] = g.get("label", "")
        styles[g["id"]] = g.get("style")
    for n in spec.get("nodes") or []:
        gid = n.get("group") or IMPLICIT
        if gid not in grouped:
            grouped[gid] = []
            labels[gid] = ""
        grouped[gid].append(n)
    grouped = OrderedDict((k, v) for k, v in grouped.items() if v)
    return grouped, labels, styles


def layout(spec):
    direction = (spec.get("direction") or "LR").upper()
    grouped, labels, styles = _grouped(spec)
    warnings = []
    if len(spec.get("nodes") or []) > 20:
        warnings.append("노드 20개 초과: 열 기반 배치가 겹칠 수 있습니다")
    if len(spec.get("groups") or []) > 6:
        warnings.append("그룹 6개 초과: 배치를 검토하세요")

    nodes, groups = OrderedDict(), []

    if direction == "TB":
        row_w = {
            gid: sum(NODE_W for _ in ns) + NODE_GAP * (len(ns) - 1) for gid, ns in grouped.items()
        }
        max_bw = max((w + 2 * GROUP_PAD for w in row_w.values()), default=0)
        y = 0.0
        for gid, ns in grouped.items():
            bw = row_w[gid] + 2 * GROUP_PAD
            bx = (max_bw - bw) / 2
            row_h = max((_node_h(n) for n in ns), default=NODE_H)
            bh = row_h + 2 * GROUP_PAD
            groups.append(
                {
                    "id": gid,
                    "label": labels[gid],
                    "style": styles.get(gid),
                    "x": _r(bx),
                    "y": _r(y),
                    "w": _r(bw),
                    "h": _r(bh),
                }
            )
            xx = bx + GROUP_PAD
            for n in ns:
                nodes[n["id"]] = _mknode(n, xx, y + GROUP_PAD, gid)
                xx += NODE_W + NODE_GAP
            y += bh + GROUP_GAP
        width, height = max_bw, max(y - GROUP_GAP, 0)
    else:  # LR
        col_h = {
            gid: sum(_node_h(n) for n in ns) + NODE_GAP * (len(ns) - 1)
            for gid, ns in grouped.items()
        }
        max_bh = max((h + 2 * GROUP_PAD for h in col_h.values()), default=0)
        x = 0.0
        for gid, ns in grouped.items():
            bh = col_h[gid] + 2 * GROUP_PAD
            by = (max_bh - bh) / 2
            bw = NODE_W + 2 * GROUP_PAD
            groups.append(
                {
                    "id": gid,
                    "label": labels[gid],
                    "style": styles.get(gid),
                    "x": _r(x),
                    "y": _r(by),
                    "w": _r(bw),
                    "h": _r(bh),
                }
            )
            yy = by + GROUP_PAD
            for n in ns:
                nh = _node_h(n)
                nodes[n["id"]] = _mknode(n, x + GROUP_PAD, yy, gid)
                yy += nh + NODE_GAP
            x += bw + GROUP_GAP
        width, height = max(x - GROUP_GAP, 0), max_bh

    edges = [
        {
            "from": e.get("from"),
            "to": e.get("to"),
            "label": e.get("label", ""),
            "dashed": e.get("style") == "dashed",
        }
        for e in (spec.get("edges") or [])
    ]
    return {
        "direction": direction,
        "nodes": nodes,
        "groups": groups,
        "edges": edges,
        "width": _r(width),
        "height": _r(height),
        "warnings": warnings,
    }


def _mknode(n, x, y, gid):
    return {
        "id": n["id"],
        "label": n.get("label", ""),
        "kind": n.get("kind", "service"),
        "note": n.get("note"),
        "group": gid,
        "x": _r(x),
        "y": _r(y),
        "w": NODE_W,
        "h": _r(_node_h(n)),
    }
