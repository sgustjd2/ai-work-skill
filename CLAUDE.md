# ai-work-skill 구현 규약

이 저장소는 데이타솔루션 생성형 AI 조직용 Claude Code 플러그인이다. 설계는 `docs/PRD.md`가 전부 담고 있으며, 코드는 그 PRD만 보고 만든다.

## 시작 전에 읽는 순서
1. `docs/PRD.md` §16(구현 지침) → §13(마일스톤) → 현재 마일스톤의 FR 행(§6) → 해당 §8~§11 절.
2. `docs/research/sources-2026-09-04.md`: 외부 사실(GitLab MCP, LiteLLM API, FastMCP, 브랜드 색)의 출처와 확인일. 현재 문서와 다르면 현재 문서를 따르고 차이를 여기에 한 줄 기록한다.
3. 포팅 원형: `../ui-skill-set/templates/design-lint.mjs`(훅 구조), `../ui-skill-set/templates/install.mjs`(병합 함수), `../품의서/.claude/skills/review-report-writer/references/writing-rules.md`(문체 규칙). 구조를 옮기되 파일을 복사하지 않는다.

## 의존성 정책
- `templates/`와 `skills/*/scripts/`는 **Python 표준 라이브러리만**, 3.9 문법(플러그인 설치만으로 어디서나 실행). 테스트가 import 목록을 검사한다.
- 서드파티는 `mcp/docgen`, `mcp/litellm_ops`(uv 프로젝트, Python 3.12)에만. 허용 목록은 PRD §9.2. 새 의존성은 추가하지 않는다.
- 렌더러·훅 소스에 hex 색 리터럴 금지. 색·폰트·치수는 `themes/*.json`에만(테스트가 grep으로 강제).

## 코드 규약
- 순수 함수와 `main()` 분리. 테스트는 순수 함수를 부르고, subprocess 테스트는 CLI 모드당 1개.
- 훅은 절대 세션을 깨지 않는다: 최상위 `try/except` → `exit 0` + stderr 한 줄.
- Windows 우선 검증: `pathlib`, `sys.stdout/stderr.reconfigure(encoding="utf-8")`, 심링크·bash·jq 사용 금지, 테스트는 `tmp_path`.
- MCP 툴은 절대 경로를 반환하고 `warnings: []`를 항상 포함한다. 시크릿은 마스킹 외 어떤 형태로도 반환·로그하지 않는다.
- 문서(`docs/`, `README.md`, `skills/**/SKILL.md`)는 우리 도구로 검사한다: em-dash·상투어·이모지 없음. 규칙 목록을 담은 파일은 frontmatter `doc_lint: off`.

## 검증 명령
```bash
uv run pytest
```
```bash
python -X utf8 templates/doc_lint.py --all docs skills README.md
```
```bash
uv run ruff check . && uv run ruff format --check .
```

## 작업 단위와 기록
- 커밋 메시지 접두사는 FR 번호: `feat(FR-3): doc_lint --pre 하드 룰`. 한 커밋에 FR 하나.
- FR 완료 = 코드 + 테스트 + PRD 완료 조건 확인. 완료 시 `docs/traceability.md`의 해당 행에 테스트 파일명과 결과를 적는다.
- 마일스톤 종료 시 갱신: `docs/PRD.md` 상단 상태 표와 §13 표, `README.md` 상태 줄(테스트 수·골든 결과·미해결 결정).
- 결정이 필요하면 PRD §14의 추천값으로 진행하고 README 상태 줄에 "추천값 적용"으로 남긴다. 사용자에게 묻기 위해 멈추지 않는다.

## 하지 않는 것
PRD에 없는 스킬·툴 추가, 프롬프트 평가 프레임워크, 컴포넌트 라이브러리, K8s 매니페스트 생성기, 자체 GitLab MCP, 회사 로고·실명·내부 URL 커밋, `.env` 값 기록, python-docx/python-pptx를 스킬에서 직접 호출하는 예시.
