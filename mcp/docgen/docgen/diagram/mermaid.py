"""배치 → mermaid flowchart 문자열. GitLab·GitHub 이 .md 에서 바로 렌더링한다."""

from __future__ import annotations

import re

from .. import theme as T
from .layout import KIND_STYLE, build_layout

_SAFE = re.compile(r"[^A-Za-z0-9_]")


def _nid(node_id: str) -> str:
    s = _SAFE.sub("_", node_id)
    return s if s and s[0].isalpha() or s.startswith("_") else f"n_{s}"


def _label(text: str) -> str:
    return str(text).replace("\\n", "\n").replace("\n", "<br/>").replace('"', "&quot;")


def _node_label(node: dict) -> str:
    return "<br/>".join(s.replace('"', "&quot;") for s in node["lines"])


def _fill(theme: dict, kind: str) -> str:
    role = KIND_STYLE[kind]["fill"]
    if role == "llm_tint":
        return T.tint(theme, "accent", 0.9)
    return T.color(theme, role)


def to_mermaid(spec: dict, theme: dict) -> tuple[str, dict]:
    lay = build_layout(spec)
    direction = "LR" if lay["direction"] != "TB" else "TB"
    lines = [f"flowchart {direction}"]

    grouped: set[str] = set()
    for g in lay["groups"]:
        members = [n for n in lay["nodes"] if _in_group(n, g, lay)]
        if not g["id"] or g["id"] == "__none__" or not g["label"]:
            continue
        lines.append(f'  subgraph g_{_nid(g["id"])}["{_label(g["label"])}"]')
        for n in members:
            lines.append(f'    {_nid(n["id"])}["{_node_label(n)}"]')
            grouped.add(n["id"])
        lines.append("  end")
        if str(g.get("style", "")).lower() == "highlight":
            lines.append(
                f"  style g_{_nid(g['id'])} stroke:{T.color(theme, 'accent')},stroke-dasharray:5 5"
            )

    for n in lay["nodes"]:
        if n["id"] not in grouped:
            lines.append(f'  {_nid(n["id"])}["{_node_label(n)}"]')

    for e in lay["edges"]:
        a, b = _nid(e["from"]), _nid(e["to"])
        lbl = _label(e["label"])
        dashed = str(e.get("style", "")).lower() == "dashed"
        if dashed:
            lines.append(f"  {a} -. {lbl} .-> {b}" if lbl else f"  {a} -.-> {b}")
        else:
            lines.append(f"  {a} -->|{lbl}| {b}" if lbl else f"  {a} --> {b}")

    used_kinds = {n["kind"] for n in lay["nodes"]}
    for kind in used_kinds:
        st = KIND_STYLE[kind]
        fill = _fill(theme, kind)
        stroke = T.color(theme, st["stroke"])
        text = T.color(theme, st["text"])
        dash = ",stroke-dasharray:4 3" if st["dashed"] else ""
        lines.append(f"  classDef {kind} fill:{fill},stroke:{stroke},color:{text}{dash};")
    for n in lay["nodes"]:
        lines.append(f"  class {_nid(n['id'])} {n['kind']}")

    return "\n".join(lines), {
        "warnings": lay["warnings"],
        "nodes": len(lay["nodes"]),
        "edges": len(lay["edges"]),
    }


def _in_group(node: dict, group: dict, lay: dict) -> bool:
    return (
        group["x"] <= node["cx"] <= group["x"] + group["w"]
        and group["y"] <= node["cy"] <= group["y"] + group["h"]
    )
