"""구성도 -> mermaid flowchart. GitLab 이 .md 에서 바로 렌더링한다. classDef 색은 테마에서."""

from __future__ import annotations

from .layout import IMPLICIT, _grouped, kind_style


def _esc(s):
    return str(s).replace('"', "'").replace("\\n", "<br/>")


def to_mermaid(spec, theme):
    direction = (spec.get("direction") or "LR").upper()
    grouped, labels, _styles = _grouped(spec)
    lines = [f"flowchart {direction}"]
    kinds_used = []
    for gid, ns in grouped.items():
        if gid != IMPLICIT:
            lines.append(f'  subgraph {gid}["{_esc(labels[gid])}"]')
        for n in ns:
            indent = "    " if gid != IMPLICIT else "  "
            lines.append(f'{indent}{n["id"]}["{_esc(n.get("label", ""))}"]')
            k = n.get("kind", "service")
            if k not in kinds_used:
                kinds_used.append(k)
        if gid != IMPLICIT:
            lines.append("  end")
    for e in spec.get("edges") or []:
        arrow = "-.->" if e.get("style") == "dashed" else "-->"
        lbl = e.get("label")
        if lbl:
            lines.append(f"  {e['from']} {arrow}|{_esc(lbl)}| {e['to']}")
        else:
            lines.append(f"  {e['from']} {arrow} {e['to']}")
    for kind in sorted(kinds_used):
        st = kind_style(theme, kind)
        dash = ",stroke-dasharray: 4 3" if st.get("dashed") else ""
        lines.append(
            f"  classDef {kind} fill:{st['fill']},stroke:{st['stroke']},color:{st['text']}{dash};"
        )
    for _gid, ns in grouped.items():
        for n in ns:
            lines.append(f"  class {n['id']} {n.get('kind', 'service')};")
    return "\n".join(lines) + "\n"
