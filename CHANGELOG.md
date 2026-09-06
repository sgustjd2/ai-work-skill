# 변경 이력

이 파일은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고, 버전은 [유의적 버전](https://semver.org/lang/ko/)을 쓴다. 날짜는 `YYYY-MM-DD`.

## [0.2.0] - 2026-09-06

산출물을 사람 글로 되돌리는 스킬과 독립 HTML 다이어그램 도구를 더했다. 스킬 11개에서 12개로 늘었다.

### 추가

- `humanize` 스킬(FR-39): AI 티가 나는 산출물을 문체·재료·판단 3축으로 진단하고, 사용자의 재료를 받아 다시 쓴다. 모드는 세 가지다. `사전`은 산출물 전에 핵심 3줄과 재료 표를 받고, `진단`은 확인 후보 표(수치·출처·인용·고유명사·제도)와 부족한 축을 보고하며, `재작성`은 그 축만 채운다. 표면 신호는 기존 훅이 이미 막으므로 이 스킬은 재료·판단·근거만 본다.
- `humanize_scan.py`: 확인 후보, 과한 일반화, 교훈형 마무리, 균일 문단, 불릿 비율, 반복 종결, 재료 밀도를 찾는 스크립트. 표준 라이브러리만 쓰고 종료 코드는 항상 0이다.
- archify 연동(FR-40): `tt-a1i/archify`를 벤더링하지 않고 `/ai-init --with-archify`로 사용자 전역에 설치한다. 아키텍처·워크플로·시퀀스·데이터 흐름·상태를 검증된 독립 HTML로 그린다. 언제 docgen 구성도 대신 쓰는지는 `references/diagram-tools.md`가 정한다.
- 골든 프롬프트 09(사람화)와 10(archify)을 `eval/prompts/`에 추가했다.
- README에 스킬 12개의 슬래시 커맨드 호출표를 넣었다.

### 변경

- `install.py`에 `--with-archify` 플래그와 순수 함수 `archify_install_cmd`, `archify_home`을 더했다.
- `doc-write`, `deck-write`, `arch-doc-types.md`, `preflight-doc.md`, 설치되는 CLAUDE 스니펫이 `humanize`와 `diagram-tools.md`를 가리킨다.
- PRD를 0.3으로 올렸다. 사람화(§8.14, FR-39, D15, 부록 G)와 archify 연동(§5.6, FR-40, D16)을 담았다.
- 테스트가 179개에서 180개로 늘었다. `doc_lint --all` 자기 검사는 104파일 하드 위반 0이다.

### 출처

- 사람화 3축은 위키독스 "누구나 할 수 있는 AI 글쓰기" 02장에서 가져왔다. archify 메타와 동작은 실제 설치 후 확인했다. 둘 다 `docs/research/sources-2026-09-06.md`에 기록했다.

## [0.1.0] - 2026-09-04

첫 배포. 생성형 AI 서비스 개발 조직의 일을 회사 표준대로 해내는 스킬 11개, MCP 서버 2개, 훅 2개.

### 추가

- 스킬 11개: `ai-init`, `doc-write`, `deck-write`, `fastapi-service`, `gitlab-ci`, `py-review`, `py-test`, `py-refactor`, `llm-gateway`, `model-serving`, `ai-trend-brief`.
- MCP 서버 2개: `docgen`(마크다운을 docx·pptx로, 구성도·차트, 미리보기, 양식 추출), `litellm-ops`(게이트웨이 상태·비용·키·config 검증 12툴). GitLab 공식 MCP는 설정만.
- 훅 2개: `doc_lint.py`(편집 전 AI 문체 차단 H1~H10, 종료 전 점검 S1~S18), `py_format.py`(편집 후 ruff).
- `STYLE.md` 문서 계약, `themes/datasolution.json` 팔레트, 골든 프롬프트 8개와 `eval/check_output.py`.
- 벤더 중립 층: `.codex-plugin/`, `AGENTS.md`, `docs/hosts.md`. Codex CLI에서 두 MCP 서버 호출을 실제로 확인했다.

[0.2.0]: https://github.com/sgustjd2/ai-work-skill/releases/tag/v0.2.0
[0.1.0]: https://github.com/sgustjd2/ai-work-skill/releases/tag/v0.1.0
