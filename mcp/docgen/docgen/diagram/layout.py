"""구성도 DSL → 배치(inch 단위). 렌더러(mermaid/png/svg/pptx)가 이 결과를 공유한다.

열 기반 단순 배치: 그룹을 direction 순서로 열(LR)/행(TB)에 놓고, 그룹 안 노드를 수직/수평
균등 배치. 겹침 최소화만 하고 최적화는 안 한다.
# ponytail: 20노드 넘으면 grandalf 같은 그래프 레이아웃 검토 (지금은 경고만)
"""

from __future__ import annotations

NODE_W = 1.9
NODE_H = 0.8
LINE_H = 0.25
GROUP_PAD = 0.25
GROUP_GAP = 0.6
NODE_GAP = 0.3
MARGIN = 0.3

# 노드 종류 → 테마 역할. 색 값은 렌더 시점에 테마에서 뽑는다(여기엔 hex 없음).
KIND_STYLE = {
    "ui": {"fill": "surface_alt", "stroke": "primary", "text": "ink", "dashed": False},
    "service": {"fill": "white", "stroke": "primary", "text": "primary", "dashed": False},
    "gateway": {"fill": "primary", "stroke": "primary", "text": "white", "dashed": False},
    "data": {"fill": "surface", "stroke": "line", "text": "ink", "dashed": False},
    "external": {"fill": "white", "stroke": "ink_muted", "text": "ink_muted", "dashed": True},
    "llm": {"fill": "llm_tint", "stroke": "accent", "text": "ink", "dashed": False},
}
DEFAULT_KIND = "service"


def _label_lines(label: str) -> list[str]:
    return str(label).replace("\\n", "\n").split("\n")


def _node_h(label: str) -> float:
    return NODE_H + LINE_H * (len(_label_lines(label)) - 1)


def build_layout(spec: dict) -> dict:
    direction = str(spec.get("direction", "LR")).upper()
    horizontal = direction != "TB"
    warnings: list[str] = []

    raw_nodes = spec.get("nodes", []) or []
    raw_edges = spec.get("edges", []) or []
    raw_groups = spec.get("groups", []) or []

    if len(raw_nodes) > 20:
        warnings.append(f"노드 {len(raw_nodes)}개(>20): 구성도를 나누는 것을 검토하세요.")
    if len(raw_groups) > 6:
        warnings.append(f"그룹 {len(raw_groups)}개(>6): 경계를 줄이는 것을 검토하세요.")

    # 그룹 순서: 선언된 그룹 + 노드가 참조한 미선언 그룹 + 무그룹(암묵적)
    group_meta = {g["id"]: g for g in raw_groups if "id" in g}
    order: list[str] = [g["id"] for g in raw_groups if "id" in g]
    members: dict[str, list[dict]] = {gid: [] for gid in order}
    implicit_key = "__none__"
    for n in raw_nodes:
        gid = n.get("group", implicit_key) or implicit_key
        if gid not in members:
            members[gid] = []
            order.append(gid)
    for n in raw_nodes:
        gid = n.get("group", implicit_key) or implicit_key
        members[gid].append(n)
    order = [g for g in order if members.get(g)]

    # 각 그룹의 콘텐츠 크기
    group_dims = {}
    for gid in order:
        ns = members[gid]
        heights = [_node_h(n.get("label", n.get("id", ""))) for n in ns]
        if horizontal:
            content_w = NODE_W
            content_h = sum(heights) + NODE_GAP * (len(ns) - 1)
        else:
            content_w = NODE_W * len(ns) + NODE_GAP * (len(ns) - 1)
            content_h = max(heights) if heights else NODE_H
        has_label = bool(group_meta.get(gid, {}).get("label"))
        label_pad = 0.3 if has_label else 0.0
        group_dims[gid] = {
            "w": content_w + 2 * GROUP_PAD,
            "h": content_h + 2 * GROUP_PAD + label_pad,
            "label_pad": label_pad,
        }

    # 그룹 배치
    if horizontal:
        max_h = max((d["h"] for d in group_dims.values()), default=NODE_H)
        x = MARGIN
        placed_groups = []
        node_rects: dict[str, dict] = {}
        for gid in order:
            d = group_dims[gid]
            gy = MARGIN + (max_h - d["h"]) / 2
            placed_groups.append(
                {
                    "id": gid,
                    "label": group_meta.get(gid, {}).get("label", ""),
                    "style": group_meta.get(gid, {}).get("style", ""),
                    "x": x,
                    "y": gy,
                    "w": d["w"],
                    "h": d["h"],
                }
            )
            # 노드 세로 배치
            ns = members[gid]
            heights = [_node_h(n.get("label", n.get("id", ""))) for n in ns]
            total = sum(heights) + NODE_GAP * (len(ns) - 1)
            ny = (
                gy
                + GROUP_PAD
                + d["label_pad"]
                + ((d["h"] - 2 * GROUP_PAD - d["label_pad"]) - total) / 2
            )
            nx = x + GROUP_PAD
            for n, h in zip(ns, heights, strict=False):
                node_rects[n["id"]] = _mk_node(n, nx, ny, NODE_W, h)
                ny += h + NODE_GAP
            x += d["w"] + GROUP_GAP
        canvas_w = x - GROUP_GAP + MARGIN
        canvas_h = MARGIN + max_h + MARGIN
    else:
        max_w = max((d["w"] for d in group_dims.values()), default=NODE_W)
        y = MARGIN
        placed_groups = []
        node_rects = {}
        for gid in order:
            d = group_dims[gid]
            gx = MARGIN + (max_w - d["w"]) / 2
            placed_groups.append(
                {
                    "id": gid,
                    "label": group_meta.get(gid, {}).get("label", ""),
                    "style": group_meta.get(gid, {}).get("style", ""),
                    "x": gx,
                    "y": y,
                    "w": d["w"],
                    "h": d["h"],
                }
            )
            ns = members[gid]
            widths = [NODE_W for _ in ns]
            total = sum(widths) + NODE_GAP * (len(ns) - 1)
            nx = gx + GROUP_PAD + ((d["w"] - 2 * GROUP_PAD) - total) / 2
            ny = y + GROUP_PAD + d["label_pad"]
            for n in ns:
                h = _node_h(n.get("label", n.get("id", "")))
                node_rects[n["id"]] = _mk_node(n, nx, ny, NODE_W, h)
                nx += NODE_W + NODE_GAP
            y += d["h"] + GROUP_GAP
        canvas_w = MARGIN + max_w + MARGIN
        canvas_h = y - GROUP_GAP + MARGIN

    # 노드가 어느 그룹인지 (같은 그룹이면 elbow)
    node_group = {}
    for gid in order:
        for n in members[gid]:
            node_group[n["id"]] = gid

    edges = []
    for e in raw_edges:
        a, b = e.get("from"), e.get("to")
        if a not in node_rects or b not in node_rects:
            warnings.append(f"엣지 대상 노드 없음: {a} → {b}")
            continue
        ra, rb = node_rects[a], node_rects[b]
        same = node_group.get(a) == node_group.get(b)
        p1, p2 = _connect_points(ra, rb, horizontal)
        edges.append(
            {
                "from": a,
                "to": b,
                "label": e.get("label", ""),
                "style": e.get("style", ""),
                "elbow": same,
                "x1": p1[0],
                "y1": p1[1],
                "x2": p2[0],
                "y2": p2[1],
            }
        )

    return {
        "direction": direction,
        "nodes": list(node_rects.values()),
        "groups": placed_groups,
        "edges": edges,
        "width": round(canvas_w, 3),
        "height": round(canvas_h, 3),
        "warnings": warnings,
    }


def _mk_node(n: dict, x: float, y: float, w: float, h: float) -> dict:
    kind = n.get("kind", DEFAULT_KIND)
    if kind not in KIND_STYLE:
        kind = DEFAULT_KIND
    return {
        "id": n["id"],
        "label": n.get("label", n["id"]),
        "lines": _label_lines(n.get("label", n["id"])),
        "kind": kind,
        "note": n.get("note", ""),
        "x": round(x, 3),
        "y": round(y, 3),
        "w": round(w, 3),
        "h": round(h, 3),
        "cx": round(x + w / 2, 3),
        "cy": round(y + h / 2, 3),
    }


def _connect_points(ra: dict, rb: dict, horizontal: bool):
    """노드 테두리에서 출발/도착하는 연결점(겹침 줄이기)."""
    ax, ay = ra["cx"], ra["cy"]
    bx, by = rb["cx"], rb["cy"]
    if horizontal and abs(bx - ax) >= ra["w"] / 2:
        if bx > ax:
            return (ra["x"] + ra["w"], ay), (rb["x"], by)
        return (ra["x"], ay), (rb["x"] + rb["w"], by)
    if not horizontal and abs(by - ay) >= ra["h"] / 2:
        if by > ay:
            return (ax, ra["y"] + ra["h"]), (bx, rb["y"])
        return (ax, ra["y"]), (bx, rb["y"] + rb["h"])
    # 같은 열/행: 옆면끼리
    if bx >= ax:
        return (ra["x"] + ra["w"], ay), (rb["x"] + rb["w"], by)
    return (ra["x"], ay), (rb["x"], by)
