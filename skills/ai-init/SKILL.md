---
name: ai-init
description: >
  ai-work-skill 을 현재 프로젝트에 설치한다. STYLE.md(문서 계약)·doc_lint 훅·py_format 훅·CLAUDE 규약·docs 골격·
  GitLab MCP 항목을 넣는다. "프로젝트 세팅", "문서 규약 설치", "스타일 가이드 설치", "ai-work-skill 설치",
  신규 저장소 온보딩, 기존 설치 갱신(--update), 프론트엔드가 있는 프로젝트의 UI 규약 동시 설치(--with-ui)에 쓴다.
  문서나 코드를 직접 만들지는 않는다.
version: 0.1.0
user-invocable: true
argument-hint: "[--update | --with-ui | --logo <경로> | --no-python]"
allowed-tools:
  - Bash(python */templates/install.py *)
  - Bash(python .claude/hooks/doc_lint.py *)
---

# ai-init

프로젝트에 문서·코드 규약을 설치한다. 설치기(`templates/install.py`)를 부르고, 결과를 사람에게 전달한다. 문서나 코드는 만들지 않는다.

## 실행 경로

플러그인 설치 시 설치기는 `${CLAUDE_PLUGIN_ROOT}/templates/install.py`, 저장소 클론 시 `templates/install.py` 다. 아래 예시의 경로를 환경에 맞게 고른다.

## 절차

1. 상태 확인. `STYLE.md` 가 이미 있으면 `--update` 인지 물어 확인하고, 없으면 신규 설치다. `--uninstall` 이면 훅 파일과 settings 항목, CLAUDE 스니펫만 지우고 `STYLE.md` 와 `docs/` 는 남긴다.
2. 질문은 최대 3개를 한 번에 묻는다. 답이 없으면 기본값으로 진행한다.
   - 조직 표기(기본 `데이타솔루션`)
   - 문서 톤(`서술식`(~다) 기본, `경어`(~습니다))
   - 회사 공식 템플릿(pptx·docx) 파일이 있는지. 있으면 경로.
   Python 프로젝트 여부는 `pyproject.toml` 존재로 자동 판단한다.
3. 설치기를 실행한다.

   플러그인:
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/templates/install.py" --target . --org "데이타솔루션 기술연구소" --tone 서술식
   ```
   클론:
   ```bash
   python templates/install.py --target . --org "데이타솔루션 기술연구소" --tone 서술식
   ```
   회사 템플릿 경로를 받았으면 `--template-pptx`·`--template-docx` 로 넘긴다. 이어서 `python -m docgen theme-from-pptx <경로> --name company --out-dir docs` 로 `docs/theme.json` 을 만든다(docgen 환경이 없으면 명령만 안내한다). 이 단계는 M1 에서 docgen 이 준비된 뒤 동작한다.
4. 설치기 출력의 "다음 단계" 를 사람에게 전달하고, 확인 검사를 돌린다.
   ```bash
   python .claude/hooks/doc_lint.py --all docs
   ```
   로고는 `--logo <파일>` 로 받아 `docs/assets/logo.png` 로 복사만 한다. 로고를 저장소에 넣지 않는 이유(상표)를 한 줄로 안내한다. `AGENTS.md` 가 있으면 같은 스니펫이 거기에도 들어간다.

## 설치되는 것

- `.claude/hooks/doc_lint.py`, Python 프로젝트면 `py_format.py`
- `.claude/settings.json`(훅 병합, 탐지한 Python 실행기로 치환)
- `STYLE.md`(문서 계약), `CLAUDE.md` 스니펫
- `docs/{arch,adr,deck,trends,assets,_build}/`, `docs/glossary.md`, `.gitignore` 에 `docs/_build/`
- `.mcp.json` 의 GitLab(공식, http) 항목

## 하지 않는 것

- 문서·덱·코드를 직접 만들기(각각 `doc-write`, `deck-write`, `fastapi-service` 가 한다)
- 회사 로고·실명·내부 URL 을 저장소에 넣기(프로젝트에만 복사)
- 사용자 확인 없이 기존 `STYLE.md` 를 덮어쓰기(`--force` 가 있을 때만)
