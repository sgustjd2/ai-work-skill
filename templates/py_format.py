#!/usr/bin/env python
"""py_format.py - ai-work-skill 0.1 - MIT

PostToolUse(Edit|Write|MultiEdit): 편집된 .py 파일에 ruff check --fix + ruff format.
ruff 가 없으면 조용히 통과. 남은 오류만 block 으로 보고. 어떤 오류도 세션을 깨지 않는다.
규격: docs/PRD.md 7.6.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"
MAX_BYTES = 512 * 1024
TIMEOUT = 30


def detect_ruff(root):
    """(1) 프로젝트에 ruff 선언 + uv 존재 -> uv run ruff. (2) PATH 의 ruff. (3) 없음 -> None."""
    text = ""
    for name in ("pyproject.toml", "uv.lock"):
        p = Path(root) / name
        if p.exists():
            try:
                text += p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass
    if "ruff" in text and shutil.which("uv"):
        return ["uv", "run", "--project", str(root), "ruff"]
    if shutil.which("ruff"):
        return ["ruff"]
    return None


def is_target(file_path, root):
    """.py 이고 프로젝트 안이며 존재하고, migrations/·*_pb2.py·512KB 초과가 아닐 때만."""
    if not file_path or not str(file_path).endswith(".py"):
        return False
    p = Path(file_path)
    if not p.is_absolute():
        p = Path(root) / file_path
    try:
        if not p.is_file() or p.stat().st_size > MAX_BYTES:
            return False
    except Exception:
        return False
    rel = str(p).replace("\\", "/")
    if "/migrations/" in rel or rel.endswith("_pb2.py"):
        return False
    return True


def _run(cmd):
    return subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT
    )


def format_file(ruff, file_path):
    """고치고 포맷한 뒤 남은 오류 문자열을 반환(없으면 '')."""
    _run(ruff + ["check", "--fix", "--quiet", file_path])
    _run(ruff + ["format", "--quiet", file_path])
    r = _run(ruff + ["check", "--output-format", "concise", file_path])
    if r.returncode != 0 and r.stdout.strip():
        return r.stdout.strip()
    return ""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
        if argv and argv[0] == "--version":
            sys.stdout.write(VERSION + "\n")
            return 0
        root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        try:
            data = json.loads((sys.stdin.read() if not sys.stdin.isatty() else "") or "{}")
        except Exception:
            data = {}
        fp = (data.get("tool_input") or {}).get("file_path")
        if not is_target(fp, root):
            return 0
        ruff = detect_ruff(root)
        if ruff is None:
            return 0
        remaining = format_file(ruff, fp)
        if remaining:
            sys.stdout.write(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": f"[py-format] ruff 미해결:\n{remaining}\n"
                        "→ 규칙을 지켜 고치거나 `# noqa: <코드>` 에 이유를 단다",
                    },
                    ensure_ascii=False,
                )
            )
        return 0
    except Exception as e:
        sys.stderr.write(f"[py-format] internal error (ignored): {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
