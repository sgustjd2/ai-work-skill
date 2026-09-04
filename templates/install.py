#!/usr/bin/env python
"""install.py - ai-work-skill 0.1 - MIT

ai-work-skill 을 대상 프로젝트에 설치한다. 순수 Python 표준 라이브러리, 의존성 0, 3.9 문법.

  python install.py --target <dir> [--org "데이타솔루션 기술연구소"] [--tone 서술식|경어]
                    [--theme datasolution] [--template-pptx <pptx>] [--template-docx <docx>]
                    [--logo <png>] [--with-ui] [--ui-skill-set <경로>]
                    [--no-python] [--update] [--force] [--uninstall]
                    [--gitlab-url https://gitlab.example.com]

병합/채우기 순수 함수는 export 되어 tests/test_install.py 가 검사한다. 파일 I/O 는 main() 에서만.
구조는 ui-skill-set/templates/install.mjs 에서 옮겼다(파일 복사 아님).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

CLAUDE_MARKER = "## 문서·코드 규약 (ai-work-skill)"

# FR-33: ui-skill-set 용 --ui-accent-100..900 램프. action 색을 기준으로 명도 보간.
_RAMP_STEPS = {
    100: 0.92,
    200: 0.82,
    300: 0.68,
    400: 0.5,
    500: 0.28,
    600: 0.12,
    700: 0.0,
    800: 0.18,
    900: 0.42,
}


def _mix(hex_a: str, hex_b: str, t: float) -> str:
    def rgb(h):
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    ra, ga, ba = rgb(hex_a)
    rb, gb, bb = rgb(hex_b)
    r, g, b = (round(a + (c - a) * t) for a, c in ((ra, rb), (ga, gb), (ba, bb)))
    return f"#{r:02X}{g:02X}{b:02X}"


def accent_ramp(theme: dict) -> str:
    """테마 dict → --ui-accent-100..900 CSS. 700 이하는 흰색, 800~900 은 ink 방향.
    색은 테마에서만 온다(소스에 hex 리터럴 없음)."""
    colors = theme.get("colors", {})
    base = colors.get("action") or colors.get("primary")
    white = colors.get("white")
    ink = colors.get("ink")
    if not (base and white and ink):
        raise ValueError("테마에 action(또는 primary)·white·ink 색이 필요합니다.")
    lines = ["/* ai-work-skill 테마에서 생성된 액센트 램프 (FR-33) */", ":root {"]
    for step, t in _RAMP_STEPS.items():
        hexv = _mix(base, white, t) if step <= 700 else _mix(base, ink, t)
        lines.append(f"  --ui-accent-{step}: {hexv};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def inject_accent_ramp(tokens_css: str, ramp_css: str) -> str:
    """tokens.css 의 --ui-accent-* 선언을 교체(없으면 램프를 앞에 붙인다)."""
    if "--ui-accent-100" not in tokens_css:
        return ramp_css + "\n" + tokens_css
    ramp_vals = dict(re.findall(r"(--ui-accent-\d+):\s*(#[0-9A-Fa-f]{6})", ramp_css))
    out = tokens_css
    for name, val in ramp_vals.items():
        out = re.sub(rf"{name}:\s*#[0-9A-Fa-f]{{6}}", f"{name}: {val}", out)
    return out


# (event, matcher, script, mode, timeout, python_only)
HOOKS = [
    ("PreToolUse", "Edit|Write|MultiEdit", "doc_lint.py", "--pre", 5, False),
    ("PostToolUse", "Edit|Write|MultiEdit", "py_format.py", "--post", 40, True),
    ("Stop", None, "doc_lint.py", "--stop", 20, False),
]

DOC_DIRS = ["arch", "adr", "deck", "trends", "assets", "_build"]
GLOSSARY_HEADER = (
    "# 용어집\n\n표준 표기와 금지 표기를 모은다. `doc_lint` 의 S18 이 '금지 표기' 열을 읽는다.\n\n"
    "| 표준 표기 | 금지 표기 | 비고 |\n|---|---|---|\n"
)

DEFAULT_PY_CANDIDATES = [["python"], ["python3"], ["py", "-3"]]


# ─── 테스트되는 순수 함수 ─────────────────────────────────────────────────────
def _hook_command(py, script, mode):
    return f"{py} -X utf8 .claude/hooks/{script} {mode}"


def merge_settings(existing_json, py, include_post=True):
    """기존 settings.json(문자열|None)에 훅을 병합. 스크립트+모드가 이미 있으면 건너뜀."""
    s = {}
    if existing_json:
        try:
            s = json.loads(existing_json)
        except Exception:
            s = {}
    s.setdefault("hooks", {})
    for event, matcher, script, mode, timeout, py_only in HOOKS:
        if py_only and not include_post:
            continue
        arr = s["hooks"].setdefault(event, [])
        suffix = f".claude/hooks/{script} {mode}"
        if any(suffix in (x.get("command") or "") for e in arr for x in (e.get("hooks") or [])):
            continue
        entry = {
            "hooks": [
                {"type": "command", "command": _hook_command(py, script, mode), "timeout": timeout}
            ]
        }
        if matcher:
            entry["matcher"] = matcher
        arr.append(entry)
    return json.dumps(s, ensure_ascii=False, indent=2) + "\n"


def remove_our_hooks(existing_json):
    """settings.json 에서 우리 command 항목만 제거(--uninstall)."""
    try:
        s = json.loads(existing_json)
    except Exception:
        return existing_json
    for event in list(s.get("hooks", {})):
        arr = s["hooks"][event]
        kept = []
        for e in arr:
            hooks = [
                h
                for h in (e.get("hooks") or [])
                if not re.search(r"\.claude/hooks/(doc_lint|py_format)\.py", h.get("command", ""))
            ]
            if hooks:
                e["hooks"] = hooks
                kept.append(e)
            elif not e.get("hooks"):
                kept.append(e)
        if kept:
            s["hooks"][event] = kept
        else:
            del s["hooks"][event]
    if not s.get("hooks"):
        s.pop("hooks", None)
    return json.dumps(s, ensure_ascii=False, indent=2) + "\n"


def fill_frontmatter(md, opts):
    """STYLE.md frontmatter 의 키 값을 opts 로 교체. 없는 키/ None 은 그대로."""
    m = re.match(r"^(---\r?\n)(.*?)(\r?\n---)", md, re.S)
    if not m:
        return md
    body = m.group(2)
    for k, v in opts.items():
        if v is None:
            continue
        rx = re.compile(rf"^({re.escape(k)}:\s*).*$", re.M)
        if rx.search(body):
            body = rx.sub(lambda mm, v=v: mm.group(1) + str(v), body)
    return md[: m.start()] + m.group(1) + body + m.group(3) + md[m.end() :]


def append_snippet(claude_md, snippet):
    """CLAUDE.md 에 스니펫을 멱등 추가. 이미 있으면 그대로."""
    if claude_md and CLAUDE_MARKER in claude_md:
        return claude_md
    base = (claude_md.rstrip() + "\n\n") if claude_md else ""
    return base + snippet.rstrip() + "\n"


def remove_snippet(claude_md):
    """CLAUDE.md 에서 우리 스니펫 블록만 제거(--uninstall). 마커부터 다음 제목/끝까지."""
    if not claude_md or CLAUDE_MARKER not in claude_md:
        return claude_md
    i = claude_md.index(CLAUDE_MARKER)
    nxt = re.search(r"\n#{1,6} ", claude_md[i + len(CLAUDE_MARKER) :])
    end = i + len(CLAUDE_MARKER) + nxt.start() + 1 if nxt else len(claude_md)
    return (
        (claude_md[:i].rstrip() + "\n" + claude_md[end:].lstrip()).strip() + "\n"
        if claude_md[:i].strip() or claude_md[end:].strip()
        else ""
    )


def merge_mcp_json(existing_json, gitlab_url=None):
    """.mcp.json 에 gitlab(공식, http) 항목 병합. 이미 있으면 그대로."""
    s = {}
    if existing_json:
        try:
            s = json.loads(existing_json)
        except Exception:
            s = {}
    s.setdefault("mcpServers", {})
    if "gitlab" not in s["mcpServers"]:
        url = gitlab_url or "${GITLAB_URL}"
        s["mcpServers"]["gitlab"] = {"type": "http", "url": url.rstrip("/") + "/api/v4/mcp"}
    return json.dumps(s, ensure_ascii=False, indent=2) + "\n"


def _probe_version(cmd):
    try:
        r = subprocess.run(cmd + ["--version"], capture_output=True, text=True, timeout=10)
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"(\d+)\.(\d+)", out)
        if r.returncode == 0 and m:
            return (int(m.group(1)), int(m.group(2)))
    except Exception:
        return None
    return None


def detect_python(candidates=None, probe=_probe_version):
    """python / python3 / py -3 중 3.9 이상인 첫 실행기 문자열. 없으면 None."""
    for cmd in candidates or DEFAULT_PY_CANDIDATES:
        v = probe(cmd)
        if v and v >= (3, 9):
            return " ".join(cmd)
    return None


def add_gitignore_line(existing, line):
    """멱등하게 한 줄 추가."""
    lines = existing.splitlines() if existing else []
    if line in lines:
        return existing if existing.endswith("\n") or not existing else existing + "\n"
    prefix = (existing.rstrip("\n") + "\n") if existing else ""
    return prefix + line + "\n"


# ─── 파일 I/O (main) ─────────────────────────────────────────────────────────
def _parse_args(argv):
    bools = {"with-ui", "no-python", "update", "force", "uninstall"}
    o = {}
    i = 0
    while i < len(argv):
        a = argv[i]
        if not a.startswith("--"):
            i += 1
            continue
        k = a[2:]
        if k in bools:
            o[k] = True
        else:
            i += 1
            o[k] = argv[i] if i < len(argv) else None
        i += 1
    return o


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Windows cp949 콘솔 방지
        except Exception:
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    a = _parse_args(argv)
    here = Path(__file__).resolve().parent  # templates/
    target = Path(a.get("target") or os.getcwd()).resolve()

    def log(msg):
        try:
            sys.stdout.write(msg + "\n")
        except UnicodeEncodeError:
            sys.stdout.write(msg.encode("ascii", "replace").decode("ascii") + "\n")

    def rd(p):
        return p.read_text(encoding="utf-8") if p.exists() else None

    def wr(p, text):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    is_python = (target / "pyproject.toml").exists() and not a.get("no-python")

    # 9-1. --uninstall
    if a.get("uninstall"):
        for name in ("doc_lint.py", "py_format.py"):
            f = target / ".claude" / "hooks" / name
            if f.exists():
                f.unlink()
                log(f"✓ 제거 .claude/hooks/{name}")
        sp = target / ".claude" / "settings.json"
        if sp.exists():
            wr(sp, remove_our_hooks(rd(sp)))
            log("✓ settings.json 훅 항목 제거")
        for name in ("CLAUDE.md", "AGENTS.md"):
            cp = target / name
            if cp.exists():
                wr(cp, remove_snippet(rd(cp)))
                log(f"✓ {name} 스니펫 제거")
        log("STYLE.md·docs/·.mcp.json 은 남겼습니다(데이터).")
        return 0

    # 1. 실행기 탐지
    py = detect_python()
    if py is None:
        py = "python"
        log("· Python 실행기를 찾지 못했습니다. 훅 명령을 'python' 으로 씁니다(경고).")
    else:
        log(f"✓ Python 실행기: {py}")

    # 2. 훅 복사(항상 갱신)
    shutil.copyfile(here / "doc_lint.py", _ensure(target / ".claude" / "hooks" / "doc_lint.py"))
    log("✓ .claude/hooks/doc_lint.py")
    if is_python:
        shutil.copyfile(
            here / "py_format.py", _ensure(target / ".claude" / "hooks" / "py_format.py")
        )
        log("✓ .claude/hooks/py_format.py")

    # 3. --update: 여기서 종료
    if a.get("update"):
        log("업데이트 완료(--update): 훅만 갱신. STYLE.md·settings·CLAUDE·docs 는 보존.")
        return 0

    # 4. STYLE.md
    style_path = target / "STYLE.md"
    if not style_path.exists() or a.get("force"):
        md = rd(here / "STYLE.md")
        md = fill_frontmatter(
            md,
            {
                "org": a.get("org"),
                "tone_doc": a.get("tone"),
                "theme": a.get("theme"),
                "template_pptx": a.get("template-pptx"),
                "template_docx": a.get("template-docx"),
            },
        )
        wr(style_path, md)
        log("✓ STYLE.md")
    else:
        log("· STYLE.md 이미 있음 (--force 로 덮어쓰기)")

    # 5. settings.json 병합
    sp = target / ".claude" / "settings.json"
    wr(sp, merge_settings(rd(sp), py, include_post=is_python))
    log("✓ .claude/settings.json (병합)")

    # 6. CLAUDE.md / AGENTS.md 스니펫
    snippet = rd(here / "CLAUDE.snippet.md")
    for name in ("CLAUDE.md", "AGENTS.md"):
        cp = target / name
        if name == "AGENTS.md" and not cp.exists():
            continue
        before = rd(cp) or ""
        after = append_snippet(before, snippet)
        if after != before:
            wr(cp, after)
            log(f"✓ {name} (규약 추가)")
        else:
            log(f"· {name} 규약 이미 있음")

    # 7. docs 골격 + glossary + .gitignore
    for d in DOC_DIRS:
        _ensure(target / "docs" / d / ".gitkeep").write_text("", encoding="utf-8")
    gl = target / "docs" / "glossary.md"
    if not gl.exists():
        wr(gl, GLOSSARY_HEADER)
    gi = target / ".gitignore"
    wr(gi, add_gitignore_line(rd(gi) or "", "docs/_build/"))
    log("✓ docs/{arch,adr,deck,trends,assets,_build}/, glossary.md, .gitignore")

    # 8. .mcp.json gitlab 병합
    mp = target / ".mcp.json"
    wr(mp, merge_mcp_json(rd(mp), a.get("gitlab-url")))
    log("✓ .mcp.json (gitlab 항목)")

    # 9. 로고
    if a.get("logo"):
        src = Path(a["logo"])
        if src.exists():
            shutil.copyfile(src, _ensure(target / "docs" / "assets" / "logo.png"))
            log("✓ docs/assets/logo.png (로고는 저장소가 아니라 프로젝트에만 둡니다)")

    # 10. --with-ui (FR-33): ui-skill-set 설치 + 테마 액센트 램프 주입
    if a.get("with-ui"):
        ui = Path(
            a.get("ui-skill-set")
            or os.environ.get("UI_SKILL_SET_ROOT")
            or str(target.parent / "ui-skill-set")
        )
        if not ui.exists():
            log("· ui-skill-set 미발견(--ui-skill-set 또는 UI_SKILL_SET_ROOT). 건너뜁니다.")
        else:
            node = shutil.which("node")
            stack = "react-tailwind4" if (target / "package.json").exists() else "react-css"
            if node:
                try:
                    subprocess.run(
                        [
                            node,
                            str(ui / "templates" / "install.mjs"),
                            "--target",
                            str(target),
                            "--mode",
                            "operate",
                            "--stack",
                            stack,
                            "--hue",
                            "blue",
                        ],
                        check=True,
                        capture_output=True,
                        timeout=60,
                    )
                    log(f"✓ ui-skill-set 설치(install.mjs, stack {stack})")
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    log(f"· install.mjs 실행 실패({e}). 수동으로 실행하세요.")
            else:
                log("· node 미발견. ui-skill-set/templates/install.mjs 를 수동 실행하세요.")
            # 테마 램프를 tokens.css 에 주입
            theme_file = here.parent / "themes" / f"{a.get('theme', 'datasolution')}.json"
            tokens = target / "src" / "styles" / "tokens.css"
            if theme_file.exists() and tokens.exists():
                theme = json.loads(theme_file.read_text(encoding="utf-8"))
                tokens.write_text(
                    inject_accent_ramp(tokens.read_text(encoding="utf-8"), accent_ramp(theme)),
                    encoding="utf-8",
                )
                log("✓ tokens.css 에 테마 액센트 램프 주입(문서·덱·UI 가 같은 파랑)")
            elif theme_file.exists():
                (target / "docs").mkdir(exist_ok=True)
                (target / "docs" / "ui-accent-ramp.css").write_text(
                    accent_ramp(json.loads(theme_file.read_text(encoding="utf-8"))),
                    encoding="utf-8",
                )
                log("· tokens.css 없음. docs/ui-accent-ramp.css 로 램프를 저장했습니다.")

    # 11. 다음 단계
    log("")
    log("다음 단계:")
    log("  1. STYLE.md 1절(조직과 독자)을 채운다")
    log(f"  2. {py} .claude/hooks/doc_lint.py --all docs/ 로 확인")
    log("  3. GitLab MCP 인증: /mcp (공식 서버, OAuth)")
    log("  4. LiteLLM 을 쓰면 LITELLM_BASE_URL 등을 환경변수로 설정")
    return 0


def _ensure(p):
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


if __name__ == "__main__":
    sys.exit(main())
