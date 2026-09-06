#!/usr/bin/env python3
"""humanize_scan.py — 산출물에서 근거가 필요한 문장과 평균값 글의 신호를 찾는다 (FR-39).

표면 신호(em-dash·상투어·이모지·3항목)는 doc_lint 가 본다. 이 스크립트는 그 뒤에 남는 것,
즉 확인 후보 문장(수치·출처·인용·고유명사·제도), 과한 일반화, 교훈형 마무리, 균일 문단,
불릿 과다, 반복 종결, 재료 밀도를 본다. 표준 라이브러리만 쓰고 종료코드는 항상 0(정보 제공용).
근거 열은 채우지 않는다. 그것은 사람(모델)이 한다. PRD 8.14, 부록 G.

  python humanize_scan.py <파일> [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ponytail: 어휘 목록 휴리스틱이다. 오탐이 쌓이면 STYLE.md allow_terms 처럼 설정으로 뺀다.
RE_NUMBER = re.compile(r"\d")
RE_QUOTE = re.compile(r"[“”\"]")
RE_SOURCE_FORM = re.compile(r"에 따르면|연구|조사|보고서|통계|전문가|알려져 있|나타났")
RE_PROPER = re.compile(r"\b[A-Z][a-z]+[A-Za-z0-9]*\b")
RE_INSTITUTION = re.compile(r"법률|법령|시행령|규정|정책|지침|고시|표준|버전 ?\d|\bv\d")
RE_SOURCE_HINT = re.compile(r"https?://|출처|source|\[\d+\]", re.I)
RE_GENERAL = re.compile(
    r"누구나|항상|언제나|모든 (?:상황|경우|사람)|대부분의 (?:사람|경우|조직|기업)"
    r"|많은 (?:사람|기업|조직)|일반적으로"
)
RE_MORAL = re.compile(r"해\s?보세요|하시기 바랍니다|바랍니다|실천하|꾸준히")
RE_STOCK = re.compile(r"것이 좋습니다|도움이 됩니다|중요합니다|할 수 있습니다")
RE_ANCHOR = re.compile(r"\d|[A-Za-z]{2,}|[“”\"]")
RE_BULLET = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
RE_HEADING = re.compile(r"^#{1,6}\s")
RE_TABLE = re.compile(r"^\s*\|")
RE_SENT_SPLIT = re.compile(r"(?<=[.?!])\s+")

KINDS = (
    ("수치", RE_NUMBER),
    ("인용", RE_QUOTE),
    ("출처", RE_SOURCE_FORM),
    ("고유명사", RE_PROPER),
    ("제도", RE_INSTITUTION),
)
MATERIAL_SUSPECT = 0.2


def clean_lines(text: str) -> list[str]:
    """frontmatter·펜스 코드·HTML 주석을 빈 줄로 바꾼다. 줄 수는 원문과 같다."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    in_fm = in_fence = in_comment = False
    for i, line in enumerate(raw):
        s = line.strip()
        if i == 0 and s == "---":
            in_fm = True
            out.append("")
            continue
        if in_fm:
            out.append("")
            in_fm = s != "---"
            continue
        if not in_fence and re.match(r"^\s*(```|~~~)", line):
            in_fence = True
            out.append("")
            continue
        if in_fence:
            out.append("")
            if re.match(r"^\s*(```|~~~)\s*$", line):
                in_fence = False
            continue
        if in_comment:
            out.append("")
            in_comment = "-->" not in line
            continue
        if "<!--" in line:
            in_comment = "-->" not in line
            out.append(line.split("<!--", 1)[0])
            continue
        out.append(line)
    return out


def blocks(lines: list[str]) -> list[dict]:
    """연속 줄을 블록으로 묶는다. kind: prose | bullet | heading | table."""
    res: list[dict] = []
    cur: list[tuple[int, str]] = []

    def flush():
        if not cur:
            return
        first = cur[0][1]
        if RE_HEADING.match(first):
            kind = "heading"
        elif RE_TABLE.match(first):
            kind = "table"
        elif RE_BULLET.match(first):
            kind = "bullet"
        else:
            kind = "prose"
        res.append({"kind": kind, "lines": list(cur)})
        cur.clear()

    for n, line in enumerate(lines, 1):
        if not line.strip():
            flush()
            continue
        if cur and (RE_HEADING.match(line) or RE_BULLET.match(line) != RE_BULLET.match(cur[0][1])):
            flush()
        cur.append((n, line))
    flush()
    return res


def sentences(block: dict) -> list[tuple[int, str]]:
    """블록의 (줄, 문장). bullet 은 줄마다 한 문장, prose 는 마침표로 나눈다."""
    if block["kind"] == "bullet":
        return [(n, RE_BULLET.sub(lambda m: m.group()[-1], t).strip()) for n, t in block["lines"]]
    joined = " ".join(t.strip() for _, t in block["lines"])
    out: list[tuple[int, str]] = []
    for s in RE_SENT_SPLIT.split(joined):
        s = s.strip()
        if not s:
            continue
        line = block["lines"][0][0]
        for n, t in block["lines"]:
            if s[:12] in t:
                line = n
                break
        out.append((line, s))
    return out


def scan(text: str) -> dict:
    lines = clean_lines(text)
    bl = blocks(lines)
    verify: list[dict] = []
    signals: list[dict] = []
    all_sents: list[tuple[int, str]] = []
    prose_counts: list[int] = []
    bullet_lines = text_lines = 0
    stock = 0
    last_prose = ""

    for b in bl:
        if b["kind"] in ("heading", "table"):
            continue
        text_lines += len(b["lines"])
        if b["kind"] == "bullet":
            bullet_lines += len(b["lines"])
        sents = sentences(b)
        all_sents.extend(sents)
        para = " ".join(t for _, t in b["lines"])
        sourced = bool(RE_SOURCE_HINT.search(para))
        if b["kind"] == "prose":
            prose_counts.append(len(sents))
            last_prose = para
        for line, s in sents:
            kinds = [k for k, rx in KINDS if rx.search(s)]
            if kinds:
                verify.append(
                    {"line": line, "sentence": s, "kinds": kinds, "unsourced": not sourced}
                )
            m = RE_GENERAL.search(s)
            if m:
                signals.append({"name": "generalization", "line": line, "detail": m.group()})
            stock += len(RE_STOCK.findall(s))

    if last_prose:
        m = RE_MORAL.search(last_prose)
        if m:
            signals.append({"name": "moral-closer", "line": None, "detail": m.group()})
    if len(prose_counts) >= 4 and len(set(prose_counts)) == 1:
        signals.append(
            {
                "name": "uniform-paragraphs",
                "line": None,
                "detail": f"문단 {len(prose_counts)}개가 전부 {prose_counts[0]}문장",
            }
        )
    if text_lines >= 8 and bullet_lines / text_lines >= 0.6:
        ratio = bullet_lines / text_lines
        signals.append(
            {
                "name": "bullet-heavy",
                "line": None,
                "detail": f"{bullet_lines}/{text_lines} 줄이 글머리표 ({ratio:.2f})",
            }
        )
    if stock >= 4:
        signals.append({"name": "stock-ending", "line": None, "detail": f"{stock}회"})

    anchored = sum(1 for _, s in all_sents if RE_ANCHOR.search(s))
    density = round(anchored / len(all_sents), 2) if all_sents else 0.0
    return {
        "sentences": len(all_sents),
        "material_density": density,
        "material_suspect": len(all_sents) >= 5 and density < MATERIAL_SUSPECT,
        "verify": verify,
        "signals": signals,
    }


def format_report(r: dict, name: str) -> str:
    unsourced = sum(1 for v in r["verify"] if v["unsourced"])
    head = f"[humanize-scan] {name} · 문장 {r['sentences']} · 재료 밀도 {r['material_density']:.2f}"
    if r["material_suspect"]:
        head += " (재료 부족 의심)"
    out = [head, "", f"## 확인 후보 ({len(r['verify'])}건, 근거 없음 {unsourced}건)"]
    if r["verify"]:
        out += ["| 줄 | 종류 | 근거 | 문장 |", "|---|---|---|---|"]
        for v in r["verify"]:
            src = "없음" if v["unsourced"] else "문단에 있음"
            out.append(f"| {v['line']} | {'·'.join(v['kinds'])} | {src} | {v['sentence'][:80]} |")
    else:
        out.append("(없음)")
    out += ["", "## 평균값 신호"]
    if r["signals"]:
        for s in r["signals"]:
            where = f" [줄 {s['line']}]" if s["line"] else ""
            out.append(f"- {s['name']}{where}: {s['detail']}")
    else:
        out.append("(없음)")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="산출물의 확인 후보·평균값 신호·재료 밀도 (정보 제공용, 종료 0)"
    )
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        p = Path(a.file)
        r = scan(p.read_text(encoding="utf-8"))
        r["file"] = str(p.resolve())
        sys.stdout.write(
            json.dumps(r, ensure_ascii=False, indent=2) if a.json else format_report(r, p.name)
        )
    except Exception as e:  # 정보 제공용 도구는 세션을 깨지 않는다
        sys.stderr.write(f"[humanize-scan] {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
