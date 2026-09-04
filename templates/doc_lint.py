#!/usr/bin/env python
"""doc_lint.py - ai-work-skill 0.1 - MIT

편집이 파일에 닿기 전에 하드 룰(H1~H10)을 검사하고, 종료 전에 소프트 룰(S1~S18)을 한 번 지적한다.
순수 Python 표준 라이브러리, 의존성 0, 3.9 문법. bash/jq/심링크 없음.

  --pre   PreToolUse(Edit|Write|MultiEdit): 제안 내용 검사 -> 위반 시 stderr + exit 2 (차단)
  --stop  Stop: git 변경 산문 파일에 하드+소프트+체크리스트 -> block 한 번 (재진입 시 통과)
  --all   CI: 경로(기본 저장소 전체)의 산문 파일 검사 -> 하드 위반 있으면 exit 1
  --lint <file> --json  : 단일 파일 findings JSON (docgen.lint_doc 가 import 해서 쓰는 함수와 동일)

룰·예외·메시지: docs/PRD.md 7절. 어떤 내부 오류도 세션을 깨지 않는다 (최상위 except -> exit 0).
정규식 구조는 ui-skill-set/templates/design-lint.mjs 에서 옮겼다(파일 복사 아님). NOTICE 참조.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.1.0"

MAX_EDIT = 128 * 1024  # --pre 편집 내용 상한
MAX_FILE = 256 * 1024  # 파일 스캔 상한

# ─── 설정 (STYLE.md frontmatter) ─────────────────────────────────────────────
DEFAULTS = {
    "dash_policy": "deny",  # deny | allow
    "emoji_policy": "deny",  # deny | allow
    "exclaim_policy": "deny",  # deny | allow
    "buzzword_policy": "block",  # block | warn
    "allow_terms": [],
    "placeholder_marker": "[확인 필요]",
    "tone_doc": "서술식",
    "tone_deck": "개조식",
    "date_format": "YYYY-MM-DD",
    "glossary": "docs/glossary.md",
    "_glossary_terms": [],
}


def parse_frontmatter(text):
    """YAML 부분집합: 스칼라와 [a, b] 리스트만. 중첩 없음. 없으면 {}."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return {}
    cfg = {}
    for line in m.group(1).split("\n"):
        line = line.rstrip("\r")
        km = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if not km:
            continue
        k, v = km.group(1), km.group(2)
        # 인라인 주석 제거(따옴표 밖의 #)
        if v and v[0] not in "\"'[{":
            v = re.split(r"\s+#", v, maxsplit=1)[0].strip()
        if v.startswith("["):
            inner = v[1:-1] if v.endswith("]") else v[1:]
            v = [s.strip().strip("\"'") for s in inner.split(",")]
            v = [s for s in v if s]
        elif v.startswith("{"):
            v = v  # 중첩 맵은 config 에서 안 씀
        else:
            v = v.strip("\"'")
        cfg[k] = v
    return cfg


def load_glossary_banned(text):
    """`| 표준 표기 | 금지 표기 | 비고 |` 표의 '금지 표기' 열을 읽는다."""
    terms = []
    col = None
    for line in text.split("\n"):
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if col is None:
            for i, c in enumerate(cells):
                if "금지" in c:
                    col = i
            continue
        if all(set(c) <= set("-: ") for c in cells):  # 구분선
            continue
        if col < len(cells) and cells[col]:
            terms.append(cells[col])
    return terms


def load_config(root):
    """root/STYLE.md 를 읽어 설정을 만든다. 없으면 None(미설치 프로젝트 -> no-op)."""
    p = Path(root) / "STYLE.md"
    if not p.exists():
        return None
    cfg = dict(DEFAULTS)
    cfg.update(parse_frontmatter(_read(p)))
    gl = cfg.get("glossary")
    if gl:
        gp = Path(root) / str(gl)
        if gp.exists():
            cfg["_glossary_terms"] = load_glossary_banned(_read(gp))
    return cfg


def find_config(file_abs, root):
    """편집 파일 위치에서 root 까지 올라가며 STYLE.md 를 찾는다."""
    root = Path(root).resolve()
    d = Path(file_abs).resolve().parent
    while True:
        if (d / "STYLE.md").exists():
            return load_config(d)
        if d == root or root not in d.parents:
            return load_config(root)
        d = d.parent


# ─── 파일 분류 (7.4) ─────────────────────────────────────────────────────────
SKIP_ALWAYS = re.compile(
    r"(^|/)(node_modules|\.git|\.venv|venv|dist|build|site-packages|__pycache__|\.claude)(/|$)"
    r"|/docs/_build/"
    r"|(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|uv\.lock|Cargo\.lock|bun\.lockb?)$"
    r"|(^|/)(changelog|license|notice)[^/]*$",
    re.I,
)
PROSE_EXT = re.compile(r"\.(md|markdown|mdx|txt|rst|adoc)$", re.I)
TEXT_EXT = re.compile(r"\.(py|js|ts|json|ya?ml|toml|cfg|ini|env)$|(^|/)\.env(\.[\w.-]+)?$", re.I)
OFFICE_EXT = re.compile(r"\.(docx|pptx|xlsx|pdf)$", re.I)
POLICY_BASES = {"style.md", "claude.md", "agents.md", "glossary.md"}


def classify(path):
    rel = str(path).replace("\\", "/")
    if SKIP_ALWAYS.search(rel):
        return "skip"
    base = rel.rsplit("/", 1)[-1].lower()
    if base in POLICY_BASES:
        return "policy"
    if PROSE_EXT.search(rel):
        return "prose"
    if TEXT_EXT.search(rel):
        return "text"
    return "skip"


def is_prose_file(path):
    return classify(path) == "prose"


def is_office_binary(path):
    return bool(OFFICE_EXT.search(str(path).replace("\\", "/")))


# ─── 룰 (7.1 하드, 7.2 소프트) ───────────────────────────────────────────────
RE_DASH = re.compile(r"[—–]")
RE_BUZZ_KO = re.compile(
    r"혁신적|차세대|획기적|최첨단|패러다임|게임\s?체인저|시너지|극대화"
    r"|최적의\s?(?:솔루션|방안|선택)"
    r"|경쟁력을?\s?(?:강화|확보)"
    r"|효율성을?\s?(?:극대화|제고|향상)"
    r"|생산성을?\s?향상"
    r"|다양한\s?활용이\s?가능"
    r"|안정적인\s?운영이\s?가능"
    r"|확장성이\s?우수"
    r"|지속적인\s?고도화가\s?가능"
    r"|전반적으로\s?우수한\s?것으로"
)
RE_BUZZ_EN = re.compile(
    r"\b(?:seamless(?:ly)?|leverag(?:e|es|ed|ing)|cutting[- ]edge|state[- ]of[- ]the[- ]art"
    r"|game[- ]?chang(?:er|ing)|delve(?:s|d)?|tapestry|unleash(?:es|ed|ing)?|supercharg\w*"
    r"|next[- ]gen(?:eration)?|best[- ]in[- ]class|revolutioni[sz]\w*|synerg\w*|paradigm)\b",
    re.I,
)
RE_AI_KO = re.compile(
    r"알아보(?:겠|도록 하겠)습니다|살펴보(?:겠|도록 하겠)습니다"
    r"|하는 것이 (?:매우 |무엇보다 )?중요합니다|주목할 만한 점은"
    r"|다음과 같은 (?:이점|장점|특징)이 있습니다"
)
RE_AI_EN = re.compile(
    r"\b(?:in conclusion|it(?:'s| is) (?:important|worth) (?:to note|noting)"
    r"|let'?s (?:dive|explore|delve)|in today'?s (?:fast-paced|rapidly|ever)"
    r"|as an ai|i hope this helps|great question|certainly!|in summary,|to summarize,)",
    re.I,
)
RE_EMOJI = re.compile(
    "[\U0001f1e6-\U0001f1ff\U0001f300-\U0001f5ff\U0001f600-\U0001f64f"
    "\U0001f680-\U0001f6ff\U0001f900-\U0001f9ff\U0001fa70-\U0001faff"
    "☀-➿⭐⭕]️?"
)
# 한국 기업 문서 관용 기호(이모지로 차단 안 함). ※ ○ → 등은 범위 밖이라 애초에 안 잡힌다.
ALLOWED_SYMBOLS = set("★☆☜☝☞☐☑☒✓✔")
RE_EXCLAIM = re.compile(r"""(?<=[가-힣A-Za-z0-9)\]"'”’])!(?![\[=(])""")
RE_PLACEHOLDER = re.compile(
    r"lorem ipsum|홍길동|john doe|\bTBD\b|\bTODO\b"
    r"|\[(?:insert|여기에|내용 입력)[^\]]*\]|\bXXX+\b",
    re.I,
)
RE_SECRET = re.compile(
    r"sk-[A-Za-z0-9_-]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"
    r"|ghp_[A-Za-z0-9]{30,}"
    r"|glpat-[A-Za-z0-9_-]{20,}"
    r"|xox[bp]-[A-Za-z0-9-]{20,}"
    r"|AIza[0-9A-Za-z_-]{35}"
)
RE_SECRET_PLACEHOLDER = re.compile(r"(.)\1{5,}|example|your[_-]|placeholder|<[^>]*>|changeme", re.I)

RE_CLOSER = re.compile(
    r"^\s*(?:결론적으로|요약하자면|종합하자면|마무리하자면|정리하자면"
    r"|In summary|To summarize|Overall,)"
)
RE_BOLD_LABEL = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\*\*[^*\n]{1,30}\*\*\s*[:：]")
RE_VAGUE = re.compile(
    r"다양한|효과적으로|체계적으로|적극적으로|원활하게|안정적으로|지속적으로|효율적으로"
)
RE_CAN_STACK = re.compile(r"할 수 (?:있습니다|있다)\.")
CONNECTIVES = [
    "또한",
    "그리고",
    "이를 통해",
    "따라서",
    "한편",
    "먼저",
    "마지막으로",
    "Additionally",
    "Furthermore",
    "Moreover",
]
RE_COLON_LEADIN = re.compile(r"다음과 같(?:습니다|다)[:：]?\s*$")
RE_GENERIC_HEADING = re.compile(
    r"^#{1,6}\s*(?:Introduction|Overview|Conclusion|Summary"
    r"|Key (?:Takeaways|Points)|Final Thoughts)\s*$",
    re.I,
)
RE_PERFECT_NUMBER = re.compile(r"\b(?:99\.9+|100)\s?%|100%\s?(?:달성|보장|해결)")
RE_OVER_GLOSS = re.compile(r"[가-힣]+\s?\([A-Za-z][A-Za-z0-9 ./-]{1,40}\)")
RE_DATE1 = re.compile(r"\d{4}\.\s?\d{1,2}\.\s?\d{1,2}\.?")
RE_DATE2 = re.compile(r"\d{4}-\d{2}-\d{2}")
RE_PCT = re.compile(r"\d+(?:\.\d+)?\s?%")
RE_SOURCE_HINT = re.compile(r"http|출처|source|\[\d+\]", re.I)
RE_FORMAL_END = re.compile(r"(?:습니다|입니다)\.")
RE_PLAIN_END = re.compile(r"[가-힣]다\.")
RE_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
RE_HEADING = re.compile(r"^#{1,6}\s")

FIX = {
    "dash": "em-dash 는 AI 문체의 첫 신호. 범위는 ~, 구분은 ·/괄호/줄바꿈으로",
    "buzzword-ko": "상투어. 대상 + 현재 한계 + 도입 후 가능한 작업 순서로 바꾼다",
    "buzzword-en": "영어 상투어. 구체 동사·명사로",
    "ai-phrase-ko": "블로그 문체. 보고서는 결론을 먼저 단정문으로 쓴다",
    "ai-phrase-en": "ChatGPT 관용구. 삭제하거나 내용으로 대체",
    "emoji": "기업 문서에 이모지 없음. 상태는 완료/진행/보류 같은 단어로, 강조는 ※·★·☞",
    "exclaim": "느낌표 없음. 마침표로",
    "placeholder": "가짜 채움 금지. 모르는 값은 [확인 필요] 로 표시하고 계속 쓴다",
    "secret": "시크릿 인라인 금지. os.environ/NAME 또는 ${NAME} 참조, 값은 .env(git 제외)에",
    "office-binary": "Office 파일은 직접 쓰지 않는다. .doc.md/.deck.md 를 고쳐 docgen 으로 렌더링",
    "rule-of-three": "항목이 늘 3개면 기계 티. 실제 개수대로(2개면 2개, 5개면 5개)",
    "bold-label": "굵은 라벨+콜론 목록은 ChatGPT 서식. 문장으로 풀거나 표로",
    "closer": "요약 문단은 앞 내용을 반복한다. 삭제하거나 새 판단만 남긴다",
    "vague-adverb": "대상·수치 없는 부사. 무엇을·얼마나로",
    "can-stack": "'할 수 있다' 반복은 가능성 나열. 실제로 하는 것·한 것으로",
    "same-starter": "접속사 반복. 문장을 합치거나 순서를 바꾼다",
    "colon-leadin": "'다음과 같습니다:' 반복. 바로 목록·표로 들어간다",
    "generic-heading-en": "영어 빈 제목. 주장이 담긴 제목으로",
    "deck-long-bullet": "슬라이드 글머리표는 한 줄. 40자 안에서 명사형으로",
    "deck-many-bullets": "6개 넘으면 두 장으로 나누거나 표로",
    "deck-headline": "슬라이드마다 헤드 메시지(##) 정확히 1개, 60자 이내",
    "deck-sentence": "덱은 개조식. '~구축'·'~필요'처럼 명사형 종결, 마침표 없음",
    "unsourced-number": "수치에는 출처. 사실/추론 구분",
    "perfect-number": "완벽한 숫자는 근거 없는 확정. 실측치나 범위로",
    "over-gloss": "영문 병기는 첫 등장 1회만",
    "honorific-mix": "존댓말/평서문 섞임. tone_doc 대로 하나로",
    "date-mix": "날짜 표기 하나로 (STYLE.md date_format)",
    "glossary-term": "용어는 용어집 표기로",
}

RE_MARKER = re.compile(r"doc-lint-allow\s+([a-z0-9-]+)\s*:\s*(?!-->)\S")


def collect_markers(text):
    return {m.group(1) for m in RE_MARKER.finditer(text)}


def _mk(code, name, line, snippet, tier="hard", severity="block"):
    return {
        "code": code,
        "name": name,
        "line": line,
        "snippet": str(snippet).strip()[:70],
        "fix": FIX.get(name, ""),
        "tier": tier,
        "severity": severity,
    }


def _has_korean(s):
    return bool(re.search(r"[가-힣]", s))


# ─── 산문 스킵 처리: 펜스 코드·frontmatter·인라인 코드·URL·링크·HTML 주석 ────
def _strip_inline(line, in_comment):
    """HTML 주석 영역을 공백으로 지우고, 인라인 코드·URL·링크 대상을 공백으로."""
    res = []
    i = 0
    while i < len(line):
        if in_comment:
            end = line.find("-->", i)
            if end == -1:
                res.append(" " * (len(line) - i))
                i = len(line)
            else:
                res.append(" " * (end + 3 - i))
                i = end + 3
                in_comment = False
            continue
        start = line.find("<!--", i)
        if start == -1:
            res.append(line[i:])
            i = len(line)
        else:
            res.append(line[i:start])
            res.append("    ")
            i = start + 4
            in_comment = True
    clean = "".join(res)
    clean = re.sub(r"`[^`]*`", lambda m: " " * len(m.group()), clean)
    clean = re.sub(r"https?://\S+", lambda m: " " * len(m.group()), clean)
    clean = re.sub(r"\]\([^)]*\)", lambda m: " " * len(m.group()), clean)
    return clean, in_comment


def clean_prose_lines(text):
    """H1~H8·소프트 룰용. 줄 수는 원문과 같게 유지(줄 번호 보존)."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    in_fm = False
    in_fence = False
    in_comment = False
    for i, line in enumerate(raw):
        stripped = line.strip()
        if i == 0 and stripped == "---":
            in_fm = True
            out.append("")
            continue
        if in_fm:
            out.append("")
            if stripped == "---":
                in_fm = False
            continue
        if not in_fence and re.match(r"^\s*(```+|~~~+)", line):
            in_fence = True
            out.append("")
            continue
        if in_fence:
            out.append("")
            if re.match(r"^\s*(```+|~~~+)\s*$", line):
                in_fence = False
            continue
        clean, in_comment = _strip_inline(line, in_comment)
        out.append(clean)
    return out


# ─── 하드 산문 룰 H1~H8 ──────────────────────────────────────────────────────
def _hard_prose(clean, cfg, markers):
    out = []
    allow_terms = {str(t) for t in (cfg.get("allow_terms") or [])}
    warn_buzz = cfg.get("buzzword_policy") == "warn"
    for idx, line in enumerate(clean):
        if not line.strip():
            continue
        n = idx + 1
        if cfg.get("dash_policy") != "allow" and "dash" not in markers:
            m = RE_DASH.search(line)
            if m:
                out.append(_mk("H1", "dash", n, m.group()))
        if "buzzword-ko" not in markers:
            for m in RE_BUZZ_KO.finditer(line):
                if m.group() in allow_terms:
                    continue
                out.append(
                    _mk(
                        "H2", "buzzword-ko", n, m.group(), severity="warn" if warn_buzz else "block"
                    )
                )
        if "buzzword-en" not in markers:
            for m in RE_BUZZ_EN.finditer(line):
                if m.group().lower() in {t.lower() for t in allow_terms}:
                    continue
                out.append(
                    _mk(
                        "H3", "buzzword-en", n, m.group(), severity="warn" if warn_buzz else "block"
                    )
                )
        if "ai-phrase-ko" not in markers:
            m = RE_AI_KO.search(line)
            if m:
                out.append(_mk("H4", "ai-phrase-ko", n, m.group()))
        if "ai-phrase-en" not in markers:
            m = RE_AI_EN.search(line)
            if m:
                out.append(_mk("H5", "ai-phrase-en", n, m.group()))
        if cfg.get("emoji_policy") != "allow" and "emoji" not in markers:
            for m in RE_EMOJI.finditer(line):
                if m.group()[0] in ALLOWED_SYMBOLS:
                    continue
                out.append(_mk("H6", "emoji", n, m.group()))
                break
        if cfg.get("exclaim_policy") != "allow" and "exclaim" not in markers:
            m = RE_EXCLAIM.search(line)
            if m:
                out.append(_mk("H7", "exclaim", n, "!"))
        if "placeholder" not in markers:
            m = RE_PLACEHOLDER.search(line)
            if m:
                out.append(_mk("H8", "placeholder", n, m.group()))
    return out


# ─── 소프트 산문 룰 S1~S18 ───────────────────────────────────────────────────
def _parse_slides(clean):
    slides = []
    cur = []
    started = False
    for line in clean:
        if line.strip() == "---":
            if started or cur:
                slides.append(cur)
            cur = []
            started = True
            continue
        cur.append(line)
    if cur:
        slides.append(cur)
    return [s for s in slides if any(x.strip() for x in s)]


def _list_groups(clean):
    groups = []
    count = 0
    for line in clean:
        if RE_LIST_ITEM.match(line):
            count += 1
        else:
            if count:
                groups.append(count)
            count = 0
    if count:
        groups.append(count)
    return groups


def _soft_prose(clean, text, path, cfg, fm, markers):
    out = []
    is_deck = str(path).lower().endswith(".deck.md")
    doc_type = str(fm.get("doc_type", ""))
    tone_deck = str(fm.get("tone_deck", cfg.get("tone_deck", "개조식")))

    def add(code, name, line, snippet):
        if name in markers:
            return
        out.append(_mk(code, name, line, snippet, tier="soft", severity="warn"))

    # S1 rule-of-three
    groups = _list_groups(clean)
    if len(groups) >= 3:
        threes = sum(1 for g in groups if g == 3)
        if threes / len(groups) >= 0.8:
            add("S1", "rule-of-three", 1, f"목록 {len(groups)}개 중 {threes}개가 3항목")

    # 파일 합계·라인 룰
    bold_labels = 0
    vague = 0
    can_stack = 0
    colon = 0
    over_gloss = 0
    for idx, line in enumerate(clean):
        n = idx + 1
        if not line.strip():
            continue
        if RE_BOLD_LABEL.match(line):
            bold_labels += 1
        if RE_CLOSER.match(line):
            add("S3", "closer", n, line.strip())
        vague += len(RE_VAGUE.findall(line))
        can_stack += len(RE_CAN_STACK.findall(line))
        if RE_COLON_LEADIN.search(line):
            colon += 1
        if RE_GENERIC_HEADING.match(line):
            add("S8", "generic-heading-en", n, line.strip())
        if RE_PERFECT_NUMBER.search(line):
            add("S14", "perfect-number", n, RE_PERFECT_NUMBER.search(line).group())
        over_gloss += len(RE_OVER_GLOSS.findall(line))
    if bold_labels >= 4:
        add("S2", "bold-label", 1, f"굵은 라벨 목록 {bold_labels}회")
    if vague >= 3:
        add("S4", "vague-adverb", 1, f"모호한 부사 {vague}회")
    if can_stack >= 5:
        add("S5", "can-stack", 1, f"'할 수 있다' {can_stack}회")
    if colon >= 3:
        add("S7", "colon-leadin", 1, f"'다음과 같습니다' {colon}회")
    if over_gloss >= 10:
        add("S15", "over-gloss", 1, f"영문 병기 {over_gloss}회")

    # S6 same-starter: 섹션(제목 사이)별
    section_start = 0
    sections = []
    for idx, line in enumerate(clean):
        if RE_HEADING.match(line):
            sections.append((section_start, idx))
            section_start = idx + 1
    sections.append((section_start, len(clean)))
    for a, b in sections:
        body = " ".join(clean[a:b])
        sentences = re.split(r"[.。!?\n]+", body)
        for conn in CONNECTIVES:
            c = sum(1 for s in sentences if s.strip().startswith(conn))
            if c >= 3:
                add("S6", "same-starter", a + 1, f"'{conn}' 문장 시작 {c}회")
                break

    # S13 unsourced-number: 브리프·검토보고서에서 문단별
    if doc_type in ("브리프", "검토보고서"):
        para = []
        para_line = 1
        blocks = []
        for idx, line in enumerate(clean):
            if line.strip():
                if not para:
                    para_line = idx + 1
                para.append(line)
            elif para:
                blocks.append((para_line, " ".join(para)))
                para = []
        if para:
            blocks.append((para_line, " ".join(para)))
        for ln, block in blocks:
            if RE_PCT.search(block) and not RE_SOURCE_HINT.search(block):
                add("S13", "unsourced-number", ln, "출처 없는 수치")

    # S16 honorific-mix: 표·목록 제외 산문
    formal = plain = 0
    for line in clean:
        if "|" in line or RE_LIST_ITEM.match(line) or RE_HEADING.match(line):
            continue
        formal += len(RE_FORMAL_END.findall(line))
        plain += len(RE_PLAIN_END.findall(line))
    plain_only = plain - formal
    if formal >= 3 and plain_only >= 3:
        add("S16", "honorific-mix", 1, f"존댓말 {formal}·평서문 {plain_only} 공존")

    # S17 date-mix
    joined = "\n".join(clean)
    if RE_DATE1.search(joined) and RE_DATE2.search(joined):
        add("S17", "date-mix", 1, "날짜 표기 두 종류 공존")

    # S18 glossary-term
    for term in cfg.get("_glossary_terms") or []:
        if term and term in joined:
            add("S18", "glossary-term", 1, term)

    # S9~S12 덱
    if is_deck:
        slides = _parse_slides(clean)
        for slide in slides:
            headlines = [x for x in slide if re.match(r"^##\s", x)]
            bullets = []
            for x in slide:
                bm = RE_LIST_ITEM.match(x)
                if bm and not re.match(r"^\s*\d", x):  # '- ' 계열만(번호 목록 제외)
                    bullets.append(x.strip()[1:].strip())
            sl_line = clean.index(slide[0]) + 1 if slide else 1
            # S11 headline
            if len(headlines) != 1:
                add("S11", "deck-headline", sl_line, f"헤드 메시지 {len(headlines)}개")
            else:
                htext = re.sub(r"^##\s+", "", headlines[0]).strip()
                if len(htext) > 60:
                    add("S11", "deck-headline", sl_line, f"헤드 {len(htext)}자")
            # S10 many bullets
            if len(bullets) >= 7:
                add("S10", "deck-many-bullets", sl_line, f"글머리표 {len(bullets)}개")
            # S9 long bullet / S12 sentence ending
            for b in bullets:
                if (_has_korean(b) and len(b) > 40) or (not _has_korean(b) and len(b) > 70):
                    add("S9", "deck-long-bullet", sl_line, b[:40])
                if tone_deck == "개조식" and re.search(r"(다|니다|요)\.$", b):
                    add("S12", "deck-sentence", sl_line, b[:40])
    return out


def _secrets(text):
    out = []
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for i, line in enumerate(raw):
        for m in RE_SECRET.finditer(line):
            if RE_SECRET_PLACEHOLDER.search(m.group()):
                continue
            out.append(_mk("H9", "secret", i + 1, m.group()[:30]))
            break
    return out


def lint(text, path, cfg=None, soft=True):
    """단일 진입점. docgen.lint_doc 가 이 함수를 그대로 import 한다(FR-14)."""
    cfg = {**DEFAULTS, **(cfg or {})}
    cls = classify(path)
    if cls == "skip":
        return []
    findings = _secrets(text)  # H9: 정책 파일·코드 포함 모든 텍스트 파일
    fm = parse_frontmatter(text)
    if cls != "prose" or str(fm.get("doc_lint", "")).strip().lower() == "off":
        return findings
    markers = collect_markers(text)
    clean = clean_prose_lines(text)
    findings += _hard_prose(clean, cfg, markers)
    if soft:
        findings += _soft_prose(clean, text, path, cfg, fm, markers)
    return findings


# ─── 출력 ────────────────────────────────────────────────────────────────────
FOOTER = (
    "규칙: 우회하지 말고 고친다. 예외가 꼭 필요하면 파일에 "
    "<!-- doc-lint-allow <룰>: <이유> --> 를 남기고 STYLE.md 6절에 기록한다 "
    "(먼저 사용자에게 1줄로 확인). 시크릿(H9)은 예외가 없다."
)
CHECKLIST = (
    "점검(정규식 밖):\n"
    "  - 결론(권고안)이 첫 화면 안에 있는가\n"
    "  - 사실·추론·권고가 표현으로 구분되는가 (~이다 / ~로 예상된다 / ~하는 것이 적절하다)\n"
    "  - 선택하지 않은 대안이 왜 밀렸는지 한 줄이라도 있는가\n"
    "  - 수치·모델명·금액·일정이 입력 자료와 같은가(만든 숫자 없는가)\n"
    "  - 문단 길이가 제각각인가. 마지막 문단이 앞 내용을 반복하지 않는가\n"
    "  - 표의 마지막 열이 '검토 의견'(판단)인가"
)


def format_findings(findings, max_n=8, edit=False):
    lines = []
    for f in findings[:max_n]:
        if f.get("file"):
            where = f"{f['file']}:{f['line']}"
        else:
            where = f"L{f['line']}{'(편집 내)' if edit else ''}"
        sev = "  (warn)" if f["severity"] == "warn" else ""
        lines.append(f"  {f['code']} {f['name']:<16} {where}  {f['snippet']}{sev}")
        lines.append("     → {}".format(f["fix"]))
    if len(findings) > max_n:
        lines.append(f"  … 외 {len(findings) - max_n}건")
    return "\n".join(lines)


def combine_soft(soft):
    """파일당 룰당 1건으로 합친다(7.2)."""
    seen = {}
    order = []
    for f in soft:
        key = (f.get("file", ""), f["name"])
        if key not in seen:
            seen[key] = dict(f)
            seen[key]["count"] = 0
            order.append(key)
        seen[key]["count"] += 1
    return [seen[k] for k in order]


def format_combined(combined, max_n=12):
    lines = []
    for f in combined[:max_n]:
        where = f"{f['file']}:{f['line']}" if f.get("file") else f"L{f['line']}"
        lines.append(f"  {f['code']} {f['name']:<16} {where}  {f['count']}건  {f['snippet']}")
        lines.append("     → {}".format(f["fix"]))
    if len(combined) > max_n:
        lines.append(f"  … 외 {len(combined) - max_n}종")
    return "\n".join(lines)


# ─── 안티 데드락 (7.5): 같은 파일·같은 룰 3회 연속 -> 4번째 통과 ───────────────
def _state_file(root):
    h = 0
    for ch in str(root):
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return Path(tempfile.gettempdir()) / (f"doc-lint-{h:08x}.json")


def _read_state(root):
    try:
        return json.loads(_read(_state_file(root)))
    except Exception:
        return {}


def _write_state(root, s):
    try:
        _state_file(root).write_text(json.dumps(s), encoding="utf-8")
    except Exception:
        pass


def _read(p):
    return Path(p).read_text(encoding="utf-8", errors="replace")


# ─── 모드 ────────────────────────────────────────────────────────────────────
def run_pre(input_obj, root):
    ti = input_obj.get("tool_input") or {}
    file = ti.get("file_path") or ti.get("path")
    if not file:
        return None
    abs_path = os.path.normpath(os.path.join(root, file)) if not os.path.isabs(file) else file
    rel = os.path.relpath(abs_path, root).replace("\\", "/")
    cfg = find_config(abs_path, root)
    if cfg is None:
        return None  # 미설치 프로젝트
    if is_office_binary(rel):
        return {
            "block": "[doc-lint] 차단: {}\n  H10 office-binary  {}\n     → {}\n{}".format(
                rel, rel, FIX["office-binary"], FOOTER
            )
        }
    if "content" in ti and isinstance(ti["content"], str):
        content = ti["content"]
    elif isinstance(ti.get("new_string"), str):
        content = ti["new_string"]
    elif isinstance(ti.get("edits"), list):
        content = "\n".join(e.get("new_string", "") for e in ti["edits"])
    else:
        return None
    if len(content.encode("utf-8")) > MAX_EDIT:
        return None
    existing = _read(abs_path) if os.path.isfile(abs_path) else ""
    markers = collect_markers(content) | collect_markers(existing)
    findings = [
        f
        for f in lint(content, rel, cfg, soft=False)
        if f["tier"] == "hard" and f["severity"] == "block" and f["name"] not in markers
    ]
    state = _read_state(root)
    if not findings:
        if rel in state:
            del state[rel]
            _write_state(root, state)
        return None
    sig = ",".join(sorted(f["name"] for f in findings))
    prev = state.get(rel, {}).get("n", 0) if state.get(rel, {}).get("sig") == sig else 0
    state[rel] = {"sig": sig, "n": prev + 1}
    _write_state(root, state)
    if prev >= 3:
        del state[rel]
        _write_state(root, state)
        return {
            "warn": f"[doc-lint] {rel}: 같은 위반({sig}) {prev}회 연속 차단 → 이번은 통과. "
            "예외면 마커 + STYLE.md 6절, 아니면 고치세요."
        }
    is_edit = "content" not in ti
    return {
        "block": f"[doc-lint] 차단: {rel} ({len(findings)}건)\n"
        f"{format_findings(findings, edit=is_edit)}\n{FOOTER}"
    }


def _git(root, args):
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return None


def changed_files(root):
    a = _git(root, ["diff", "--name-only", "HEAD"])
    if a is None:
        return None
    b = _git(root, ["ls-files", "--others", "--exclude-standard"]) or ""
    files = {x for x in (a + "\n" + b).split("\n") if x.strip()}
    return sorted(files)[:200]


def run_stop(input_obj, root):
    if input_obj.get("stop_hook_active"):
        return None
    cfg = load_config(root)
    if cfg is None:
        return None
    files = changed_files(root)
    if files is None:
        return None
    all_f = []
    checked = 0
    for f in files:
        p = Path(root) / f
        try:
            if not p.is_file() or p.stat().st_size > MAX_FILE:
                continue
            text = _read(p)
        except Exception:
            continue
        res = lint(text, f, cfg, soft=True)
        if classify(f) != "skip":
            checked += 1
        for x in res:
            x["file"] = f.replace("\\", "/")
            all_f.append(x)
    hard = [f for f in all_f if f["tier"] == "hard" and f["severity"] == "block"]
    warns = [f for f in all_f if f["tier"] == "hard" and f["severity"] == "warn"]
    soft = [f for f in all_f if f["tier"] == "soft"]
    if not hard and not warns and not soft:
        return {
            "json": {
                "systemMessage": f"[doc-lint] 변경 문서 {checked}개, 위반 0건. "
                "좋은 문서라는 뜻은 아닙니다. STYLE.md 를 계속 따르세요."
            }
        }
    parts = [f"[doc-lint] 종료 전 점검 (변경 문서 {checked}개)"]
    if hard:
        parts.append(f"하드 룰 {len(hard)}건, 고쳐야 합니다:\n{format_findings(hard, max_n=10)}")
    if warns:
        parts.append(f"경고 {len(warns)}건(정책상 차단 아님):\n{format_findings(warns, max_n=10)}")
    if soft:
        combined = combine_soft(soft)
        parts.append(f"소프트 룰 {len(combined)}종, 검토하세요:\n{format_combined(combined)}")
    parts.append(CHECKLIST)
    parts.append(FOOTER)
    parts.append("(한 번만 지적합니다. 고친 뒤 다시 종료하세요.)")
    return {"json": {"decision": "block", "reason": "\n".join(parts)}}


SKIP_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    "site-packages",
    "__pycache__",
    ".claude",
    "_build",
}


def _iter_files(root, paths):
    for p in paths:
        ap = p if os.path.isabs(p) else os.path.join(root, p)
        if os.path.isdir(ap):
            for dirpath, dirnames, filenames in os.walk(ap):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                for fn in filenames:
                    yield os.path.join(dirpath, fn)
        elif os.path.isfile(ap):
            yield ap


def run_all(cfg, paths, root):
    all_f = []
    nfiles = 0
    seen = set()
    for f in _iter_files(root, paths):
        rel = os.path.relpath(f, root).replace("\\", "/")
        if rel in seen or classify(rel) == "skip":
            continue
        seen.add(rel)
        try:
            if os.path.getsize(f) > MAX_FILE:
                continue
            text = _read(f)
        except Exception:
            continue
        res = lint(text, rel, cfg, soft=True)
        if res:
            nfiles += 1
        for x in res:
            x["file"] = rel
            all_f.append(x)
    hard = [f for f in all_f if f["tier"] == "hard" and f["severity"] == "block"]
    warns = [f for f in all_f if f["tier"] == "hard" and f["severity"] == "warn"]
    soft = [f for f in all_f if f["tier"] == "soft"]
    total_prose = len(seen)
    if not all_f:
        return f"[doc-lint] 위반 0건 · 검사 파일 {total_prose}개\n", 0
    density = round(len(all_f) / max(total_prose, 1), 2)
    lines = [
        f"[doc-lint] 하드 {len(hard)}건 · 경고 {len(warns)}건 · 소프트 {len(soft)}건 "
        f"/ 위반 파일 {nfiles}개 (파일당 {density:.2f}건)"
    ]
    if hard:
        lines.append(format_findings(hard, max_n=50))
    if warns:
        lines.append(format_findings(warns, max_n=20))
    if soft:
        lines.append(format_combined(combine_soft(soft), max_n=30))
    return "\n".join(lines) + "\n", (1 if hard else 0)


def _read_stdin():
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    mode = argv[0] if argv else "--pre"
    try:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")  # Windows cp949 방지
            except Exception:
                pass
        root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

        if mode == "--version":
            sys.stdout.write(VERSION + "\n")
            return 0
        if mode == "--all":
            paths = argv[1:] or [root]
            cfg = load_config(root) or dict(DEFAULTS)
            report, code = run_all(cfg, paths, root)
            sys.stdout.write(report)
            return code
        if mode == "--lint":
            target = argv[1]
            cfg = find_config(os.path.abspath(target), root) or dict(DEFAULTS)
            findings = lint(_read(target), target, cfg, soft=True)
            sys.stdout.write(json.dumps({"file": target, "findings": findings}, ensure_ascii=False))
            return 0

        try:
            input_obj = json.loads(_read_stdin() or "{}")
        except Exception:
            input_obj = {}

        if mode == "--pre":
            r = run_pre(input_obj, root)
            if not r:
                return 0
            if "warn" in r:
                sys.stdout.write(json.dumps({"systemMessage": r["warn"]}, ensure_ascii=False))
                return 0
            sys.stderr.write(r["block"] + "\n")
            return 2
        if mode == "--stop":
            r = run_stop(input_obj, root)
            if r and r.get("json"):
                sys.stdout.write(json.dumps(r["json"], ensure_ascii=False))
            return 0
        return 0
    except Exception as e:  # 세션을 절대 깨지 않는다
        sys.stderr.write(f"[doc-lint] internal error (ignored): {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
