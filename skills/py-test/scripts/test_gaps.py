#!/usr/bin/env python3
"""test_gaps.py — 테스트가 참조하지 않는 공개 함수/메서드를 찾는다 (FR-22).

# ponytail: 이름 기반 매칭이다. 호출 그래프가 필요하면 coverage 로.
표준 라이브러리만 쓴다. 종료코드는 항상 0(정보 제공용).

  python test_gaps.py <패키지경로> [--tests tests] [--json]
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path


def _public_defs(root: Path) -> dict[str, list[str]]:
    """모듈 상대경로 -> 공개 함수/메서드 이름 목록."""
    out: dict[str, list[str]] = {}
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts or f.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    names.append(node.name)
        rel = str(f.relative_to(root)).replace("\\", "/")
        if names:
            out[rel] = sorted(set(names))
    return out


def _referenced_names(tests_dir: Path) -> set[str]:
    refs: set[str] = set()
    if not tests_dir.is_dir():
        return refs
    for f in tests_dir.rglob("*.py"):
        if "__pycache__" in f.parts:
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                refs.add(node.id)
            elif isinstance(node, ast.Attribute):
                refs.add(node.attr)
    return refs


def check(pkg_path, tests_path="tests") -> dict:
    root = Path(pkg_path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"패키지 디렉터리가 아닙니다: {root}")
    tests_dir = Path(tests_path)
    if not tests_dir.is_absolute():
        tests_dir = root.parent / tests_path
    defs = _public_defs(root)
    refs = _referenced_names(tests_dir)
    gaps: dict[str, list[str]] = {}
    total = covered = 0
    for mod, names in defs.items():
        missing = [n for n in names if n not in refs]
        total += len(names)
        covered += len(names) - len(missing)
        if missing:
            gaps[mod] = missing
    return {
        "package": root.name,
        "tests_dir": str(tests_dir),
        "public_defs": total,
        "referenced": covered,
        "gaps": gaps,
        "note": "이름 기반 휴리스틱. 참조 있음 != 테스트됨. 실제 커버리지는 coverage 로 확인.",
    }


def _report(r: dict) -> str:
    lines = [
        f"[test-gaps] {r['package']} · 공개 정의 {r['public_defs']}개 중 "
        f"테스트에서 이름 참조 {r['referenced']}개",
        r["note"],
    ]
    if not r["gaps"]:
        lines.append("미참조 0건.")
    else:
        lines.append(f"미참조 {sum(len(v) for v in r['gaps'].values())}건:")
        for mod, names in sorted(r["gaps"].items()):
            lines.append(f"  {mod}: {', '.join(names)}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="테스트 미참조 공개 함수 찾기")
    ap.add_argument("package")
    ap.add_argument("--tests", default="tests")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        r = check(a.package, a.tests)
    except NotADirectoryError as e:
        sys.stderr.write(f"[test-gaps] {e}\n")
        return 2
    if a.json:
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(_report(r) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
