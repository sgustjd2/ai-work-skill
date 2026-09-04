#!/usr/bin/env python3
"""ci_lint.py — .gitlab-ci.yml 검사 (FR-21). 표준 라이브러리만.

환경변수 GITLAB_URL·GITLAB_TOKEN·CI_PROJECT_ID 가 모두 있으면 GitLab CI Lint API 로 정식 검사한다.
없으면 로컬에서 문법·구조를 가볍게 본다(탭 금지, 정의되지 않은 stage 참조). 정식 검사는 API 가 한다.

  python ci_lint.py [.gitlab-ci.yml]
종료코드: 오류가 있으면 1, 없으면 0.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

RESERVED = {
    "stages",
    "variables",
    "default",
    "include",
    "workflow",
    "image",
    "services",
    "before_script",
    "after_script",
    "cache",
    "pages",
}
BUILTIN_STAGES = {".pre", ".post"}


def local_check(text: str) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    lines = text.splitlines()

    for i, line in enumerate(lines, 1):
        if "\t" in line:
            errors.append(f"{i}행: 탭 문자 사용(YAML 은 공백만).")

    stages = _stage_list(lines)
    if not stages:
        warnings.append("stages 정의가 없습니다. 잡 순서가 불명확할 수 있습니다.")
    known = set(stages) | BUILTIN_STAGES
    for i, val in _job_stage_refs(lines):
        if val not in known:
            errors.append(f"{i}행: 정의되지 않은 stage '{val}' 참조(stages: {stages}).")

    if "script:" not in text and "trigger:" not in text and "run:" not in text:
        warnings.append("실행 script 가 있는 잡이 없어 보입니다.")
    return {"mode": "local", "valid": not errors, "errors": errors, "warnings": warnings}


def _stage_list(lines: list[str]) -> list[str]:
    out: list[str] = []
    in_stages = False
    for line in lines:
        if re.match(r"^stages:\s*$", line):
            in_stages = True
            continue
        if in_stages:
            m = re.match(r"^\s*-\s*['\"]?([A-Za-z0-9_.\-]+)['\"]?\s*$", line)
            if m:
                out.append(m.group(1))
            elif line.strip() and not line.startswith(" "):
                break
    # inline: stages: [build, test]
    for line in lines:
        m = re.match(r"^stages:\s*\[([^\]]*)\]", line)
        if m:
            out += [s.strip().strip("'\"") for s in m.group(1).split(",") if s.strip()]
    return out


def _job_stage_refs(lines: list[str]) -> list[tuple[int, str]]:
    refs = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"^\s+stage:\s*['\"]?([A-Za-z0-9_.\-]+)['\"]?\s*$", line)
        if m:
            refs.append((i, m.group(1)))
    return refs


def api_lint(url: str, token: str, project: str, text: str) -> dict:
    endpoint = f"{url.rstrip('/')}/api/v4/projects/{project}/ci/lint"
    data = json.dumps({"content": text}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=data,
        method="POST",
        headers={"PRIVATE-TOKEN": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {
            "mode": "api",
            "valid": False,
            "errors": [f"CI Lint API {e.code}: {e.reason}"],
            "warnings": [],
        }
    except urllib.error.URLError as e:
        return {
            "mode": "api",
            "valid": False,
            "errors": [f"CI Lint API 연결 실패: {e.reason}"],
            "warnings": [],
        }
    return {
        "mode": "api",
        "valid": body.get("valid", False),
        "errors": body.get("errors", []),
        "warnings": body.get("warnings", []),
    }


def check(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    url, token, project = (
        os.environ.get("GITLAB_URL"),
        os.environ.get("GITLAB_TOKEN"),
        os.environ.get("CI_PROJECT_ID"),
    )
    if url and token and project:
        return api_lint(url, token, project, text)
    return local_check(text)


def main(argv=None):
    path = (argv or sys.argv[1:] or [".gitlab-ci.yml"])[0]
    if not Path(path).exists():
        sys.stderr.write(f"[ci-lint] 파일 없음: {path}\n")
        return 1
    r = check(path)
    tag = "GitLab API" if r["mode"] == "api" else "로컬(참고용, 정식 검사는 GitLab CI Lint API)"
    sys.stdout.write(f"[ci-lint] {tag} · {'통과' if r['valid'] else '오류'}\n")
    for e in r["errors"]:
        sys.stdout.write(f"  오류: {e}\n")
    for w in r["warnings"]:
        sys.stdout.write(f"  경고: {w}\n")
    return 0 if r["valid"] else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    raise SystemExit(main())
