#!/usr/bin/env python3
"""import_graph.py — 패키지 내부 import 그래프 분석 (FR-24).

순환 import, 레이어 방향 위반, 팬인/팬아웃 상위, 긴 파일을 찾는다.
표준 라이브러리만 쓴다(어느 프로젝트에서도 실행되도록). 의존성 0.

  python import_graph.py <패키지경로> [--layers api,services,infra] [--json] [--max-lines 300]

레이어를 안 주면 대상 프로젝트의 pyproject.toml [tool.ai-work].layers 를 읽고,
없으면 레이어 검사를 건너뛴다. 종료코드: 순환 또는 레이어 위반이 있으면 1, 없으면 0.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path


def _module_name(file: Path, root: Path, pkg: str) -> str:
    rel = file.relative_to(root).with_suffix("")
    parts = [pkg, *rel.parts]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _internal_imports(tree: ast.AST, self_mod: str, pkg: str, known: set[str]) -> set[str]:
    out: set[str] = set()
    self_parts = self_mod.split(".")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == pkg or a.name.startswith(pkg + "."):
                    out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                base = self_parts[: len(self_parts) - node.level]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            if mod == pkg or mod.startswith(pkg + "."):
                out.add(mod)
                for a in node.names:  # from pkg.sub import name → name 이 모듈일 수도
                    cand = f"{mod}.{a.name}"
                    if cand in known:
                        out.add(cand)
    out.discard(self_mod)
    # 알려진 모듈로만 좁힌다(외부·표준 라이브러리 제외)
    return {m for m in out if m in known or any(m.startswith(k + ".") for k in known)}


def _resolve(mod: str, known: set[str]) -> str | None:
    if mod in known:
        return mod
    # pkg.sub.func → pkg.sub 로 축약
    parts = mod.split(".")
    while parts:
        cand = ".".join(parts)
        if cand in known:
            return cand
        parts.pop()
    return None


def build_graph(root: Path, pkg: str) -> dict[str, set[str]]:
    files = [f for f in root.rglob("*.py") if "__pycache__" not in f.parts]
    known = {_module_name(f, root, pkg) for f in files}
    graph: dict[str, set[str]] = {}
    for f in files:
        mod = _module_name(f, root, pkg)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            graph[mod] = set()
            continue
        raw = _internal_imports(tree, mod, pkg, known)
        resolved = {r for r in (_resolve(m, known) for m in raw) if r and r != mod}
        graph[mod] = resolved
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Tarjan SCC. 노드가 2개 이상이거나 자기 순환인 SCC 만 순환으로 본다."""
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    low: dict[str, int] = {}
    result: list[list[str]] = []
    sys.setrecursionlimit(10000)

    def strong(v: str):
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, ()):  # noqa: B007
            if w not in indices:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in graph.get(v, ()):
                result.append(sorted(comp))

    for v in list(graph):
        if v not in indices:
            strong(v)
    return result


def _layer_of(mod: str, pkg: str, layers: list[str]) -> str | None:
    parts = mod.split(".")
    for p in parts[1:]:  # pkg 다음 세그먼트부터
        if p in layers:
            return p
    return None


def layer_violations(graph: dict[str, set[str]], pkg: str, layers: list[str]) -> list[dict]:
    """상위 레이어를 import 하면 위반. 순서: layers[0] 이 가장 상위(api), 마지막이 최하위(infra).
    허용: 상위 → 하위(인덱스 증가 방향). 위반: 하위가 상위를 import."""
    order = {name: i for i, name in enumerate(layers)}
    out = []
    for mod, deps in graph.items():
        li = _layer_of(mod, pkg, layers)
        if li is None:
            continue
        for dep in deps:
            lj = _layer_of(dep, pkg, layers)
            if lj is None:
                continue
            if order[lj] < order[li]:  # 더 상위를 import → 위반
                out.append({"from": mod, "to": dep, "from_layer": li, "to_layer": lj})
    return out


def fan_stats(graph: dict[str, set[str]]) -> tuple[list, list]:
    fan_out = sorted(((len(d), m) for m, d in graph.items()), reverse=True)
    fan_in_count: dict[str, int] = {m: 0 for m in graph}
    for deps in graph.values():
        for d in deps:
            fan_in_count[d] = fan_in_count.get(d, 0) + 1
    fan_in = sorted(((c, m) for m, c in fan_in_count.items()), reverse=True)
    return fan_in, fan_out


def long_files(root: Path, pkg: str, max_lines: int) -> list[dict]:
    out = []
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        n = len(f.read_text(encoding="utf-8").splitlines())
        if n > max_lines:
            out.append({"module": _module_name(f, root, pkg), "lines": n})
    return sorted(out, key=lambda x: -x["lines"])


def _read_layers(project_root: Path) -> list[str]:
    pp = project_root / "pyproject.toml"
    if not pp.exists():
        return []
    text = pp.read_text(encoding="utf-8")
    m = re.search(r"layers\s*=\s*\[([^\]]*)\]", text)
    if not m:
        return []
    return [s.strip().strip("\"'") for s in m.group(1).split(",") if s.strip()]


def check(pkg_path, layers=None, max_lines=300) -> dict:
    root = Path(pkg_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"패키지 디렉터리가 아닙니다: {root}")
    pkg = root.name
    if layers is None:
        layers = _read_layers(root.parent)
    graph = build_graph(root, pkg)
    cycles = find_cycles(graph)
    violations = layer_violations(graph, pkg, layers) if layers else []
    fan_in, fan_out = fan_stats(graph)
    return {
        "package": pkg,
        "modules": len(graph),
        "layers": layers,
        "cycles": cycles,
        "layer_violations": violations,
        "fan_in_top": [{"module": m, "count": c} for c, m in fan_in[:10] if c],
        "fan_out_top": [{"module": m, "count": c} for c, m in fan_out[:10] if c],
        "long_files": long_files(root, pkg, max_lines),
    }


def _report(r: dict) -> str:
    layers = r["layers"] or "없음"
    lines = [f"[import-graph] {r['package']} · 모듈 {r['modules']}개 · 레이어 {layers}"]
    if r["cycles"]:
        lines.append(f"순환 {len(r['cycles'])}건:")
        for c in r["cycles"]:
            lines.append("  - " + " -> ".join(c) + " -> " + c[0])
    else:
        lines.append("순환 0건")
    if r["layers"]:
        if r["layer_violations"]:
            lines.append(f"레이어 위반 {len(r['layer_violations'])}건 (하위가 상위를 import):")
            for v in r["layer_violations"]:
                lines.append(f"  - {v['from']} ({v['from_layer']}) -> {v['to']} ({v['to_layer']})")
        else:
            lines.append("레이어 위반 0건")
    if r["long_files"]:
        lines.append(
            f"긴 파일({len(r['long_files'])}건): "
            + ", ".join(f"{f['module']}({f['lines']})" for f in r["long_files"][:5])
        )
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="패키지 import 그래프 분석")
    ap.add_argument("package")
    ap.add_argument("--layers", default=None, help="쉼표로 구분(상위→하위). 예: api,services,infra")
    ap.add_argument("--max-lines", type=int, default=300)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    layers = [s.strip() for s in a.layers.split(",")] if a.layers else None
    try:
        r = check(a.package, layers, a.max_lines)
    except (NotADirectoryError, FileNotFoundError) as e:
        sys.stderr.write(f"[import-graph] {e}\n")
        return 2
    if a.json:
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(_report(r) + "\n")
    return 1 if (r["cycles"] or r["layer_violations"]) else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
