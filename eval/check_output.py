#!/usr/bin/env python3
"""check_output.py — 골든 실행 결과 검증 (FR-32). 표준 라이브러리만.

한 실행 디렉터리(.doc.md/.deck.md 원본 + 렌더된 docx/pptx)를 받아:
  1. 산문 파일에 doc_lint 하드 룰 0, 덱 소프트 룰(S9~S12) 0
  2. 생성 docx/pptx 의 색이 테마 팔레트(+ 흑·백) 안에 있는가
을 확인하고 PASS/FAIL 을 낸다.

  python check_output.py <run_dir> [--theme themes/datasolution.json] [--json]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_COLOR_PATTERNS = [
    re.compile(r'srgbClr val="([0-9A-Fa-f]{6})"'),  # pptx·docx drawing
    re.compile(r'w:color[^>]*w:val="([0-9A-Fa-f]{6})"'),  # docx 글자색
    re.compile(r'w:fill="([0-9A-Fa-f]{6})"'),  # docx shd 음영
]
NEUTRALS = {"000000", "FFFFFF"}
DECK_SOFT = {"deck-long-bullet", "deck-many-bullets", "deck-headline", "deck-sentence"}
# 콘텐츠 부분만 본다. theme1.xml·styles.xml·마스터/레이아웃의 기본 Office 팔레트는 제외.
_CONTENT = re.compile(r"(word/(document|header\d+|footer\d+)\.xml|ppt/slides/slide\d+\.xml)$")


def _load_doc_lint():
    if "doc_lint" in sys.modules:
        return sys.modules["doc_lint"]
    spec = importlib.util.spec_from_file_location("doc_lint", ROOT / "templates" / "doc_lint.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["doc_lint"] = mod
    spec.loader.exec_module(mod)
    return mod


def _mix(hex_a: str, hex_b: str, t: float) -> str:
    def rgb(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    ra, ga, ba = rgb(hex_a)
    rb, gb, bb = rgb(hex_b)
    r, g, b = (round(a + (c - a) * t) for a, c in ((ra, rb), (ga, gb), (ba, bb)))
    return f"{r:02X}{g:02X}{b:02X}"


def theme_hexes(theme_path: Path) -> set[str]:
    """테마 팔레트 + 렌더러가 쓰는 파생 틴트(흰색 방향 블렌드)를 허용 집합으로."""
    data = json.loads(theme_path.read_text(encoding="utf-8"))
    colors = data.get("colors", {})
    allowed = {v.lstrip("#").upper() for v in colors.values()}
    white = colors.get("white", "#FFFFFF")
    for hexv in colors.values():
        for t in (0.8, 0.85, 0.9):  # 구성도 노드·표 짝수 행 등의 틴트
            allowed.add(_mix(hexv, white, t))
    return allowed


def office_colors(path: Path) -> set[str]:
    out: set[str] = set()
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if not _CONTENT.search(name):
                continue
            xml = z.read(name).decode("utf-8", "ignore")
            for pat in _COLOR_PATTERNS:
                for m in pat.finditer(xml):
                    out.add(m.group(1).upper())
    return out


def check_run(run_dir: str, theme_path: str | None = None) -> dict:
    d = Path(run_dir)
    theme = Path(theme_path) if theme_path else ROOT / "themes" / "datasolution.json"
    allowed = theme_hexes(theme) | NEUTRALS
    dl = _load_doc_lint()

    prose = [f for f in d.rglob("*") if f.suffix in (".md", ".txt") and f.is_file()]
    hard = []
    deck_soft = []
    for f in prose:
        findings = dl.lint(f.read_text(encoding="utf-8"), str(f), soft=True)
        for x in findings:
            if x["tier"] == "hard":
                hard.append({"file": f.name, "code": x["code"], "line": x["line"]})
            elif x["name"] in DECK_SOFT:
                deck_soft.append({"file": f.name, "name": x["name"], "line": x["line"]})

    off_theme = {}
    for f in list(d.rglob("*.docx")) + list(d.rglob("*.pptx")):
        bad = sorted(office_colors(f) - allowed)
        if bad:
            off_theme[f.name] = bad

    verdict = "PASS" if not hard and not deck_soft and not off_theme else "FAIL"
    return {
        "run_dir": str(d.resolve()),
        "prose_files": len(prose),
        "office_files": len(list(d.rglob("*.docx")) + list(d.rglob("*.pptx"))),
        "hard_violations": hard,
        "deck_soft": deck_soft,
        "off_theme_colors": off_theme,
        "verdict": verdict,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="골든 실행 결과 검증")
    ap.add_argument("run_dir")
    ap.add_argument("--theme", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = check_run(a.run_dir, a.theme)
    if a.json:
        sys.stdout.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    else:
        sys.stdout.write(
            f"[check] {r['verdict']} · 산문 {r['prose_files']} · office {r['office_files']} · "
            f"하드 {len(r['hard_violations'])} · 덱소프트 {len(r['deck_soft'])} · "
            f"테마밖 색 {sum(len(v) for v in r['off_theme_colors'].values())}\n"
        )
        for h in r["hard_violations"]:
            sys.stdout.write(f"  하드 {h['code']} {h['file']}:{h['line']}\n")
        for name, cols in r["off_theme_colors"].items():
            sys.stdout.write(f"  테마 밖 색 {name}: {', '.join(cols)}\n")
    return 0 if r["verdict"] == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
