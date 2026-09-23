# 변경 이력

이 파일은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고, 버전은 [유의적 버전](https://semver.org/lang/ko/)을 쓴다. 날짜는 `YYYY-MM-DD`.

## [0.3.1] - 2026-09-23

0.3.0 설치본을 실제로 확인하다 찾은 설정 문제 두 건을 고쳤다. 스킬 내용은 0.3.0과 같다.

### 수정

- `.mcp.json`: `LITELLM_MASTER_KEY` 기본값을 `${LITELLM_MASTER_KEY:-}`로 바꿨다. 환경변수가 없으면 `${LITELLM_MASTER_KEY}` 글자 그대로 `litellm-ops`에 넘어가 인증 헤더로 쓰였다. 이제 빈 값이 되어 헤더를 붙이지 않는다.
- `.claude-plugin/marketplace.json`: 마켓플레이스 설명을 넣어 `claude plugin validate` 경고를 없앴다.

## [0.3.0] - 2026-09-23

Claude Opus 5.5 출시(2026-09-22)를 계기로 스킬에 박힌 외부 사실을 공식 문서로 다시 확인하고 갱신했다. 스킬 수는 그대로 12개다.

### 변경

- 게이트웨이 `model_name`을 벤더 모델명(`gpt-4o`)에서 용도 별칭(`chat`, `claude`, `gemini`, `openai`, `internal-llm`, `embed`)으로 바꿨다. 모델을 교체해도 앱 설정은 그대로 둔다. `fastapi-service` 골격, `client_example.py`, `bench_llm.py`, `llm-mocking.md`의 기본 모델도 `chat`이다.
- 모델 ID를 현행으로 바꿨다: Azure `gpt-6-sol`(v1 API라 `api_version: "v1"`), Bedrock `global.anthropic.claude-sonnet-5`(서울 리전), Vertex `gemini-3.8-flash`(`global`), 사내 vLLM `qwen3.8-27b`. 제공자 참조에 데이터 처리 위치(Global Standard, global 프로파일)와 모델 종료 일정을 적었다.
- LiteLLM 이미지를 `v1.102.0`으로 고정했다(`main-latest` 금지). 운영 런북에 2026년 보안 권고와 PyPI 악성 배포 확인 절차를 넣었다.
- `model-serving`: vLLM 0.30 기준 인자(프리픽스 캐싱 기본 켜짐, `--reasoning-parser`, `--tool-call-parser`, `--kv-cache-dtype fp8`, `--runner pooling`), FP8·NVFP4·MXFP4 양자화와 llm-compressor, 서빙 대안(SGLang·Dynamo·llm-d, TGI 보관 처리), GPU 메모리 표·MoE 사이징·모델 라이선스 주의.
- `vram_estimate.py`가 `nvfp4`·`mxfp4`와 96·141·180GB 카드를 계산한다.
- `references/genai-patterns.md`: contextual retrieval·BM25·리랭크, 롱컨텍스트 대 RAG 판단, 제약 디코딩과 툴 검색, Rule of Two, 작업·평가 에이전트 분리, OWASP LLM 2026·Agentic Top 10, 인공지능기본법 표시 의무, pass^k, effort·캐시 순서·배치 API.
- `ai-trend-brief` 출처에 변경 이력(모델 종료 공지)과 국내 분류를 더했다. 33개 URL 응답을 확인했다.

### 제거

- 게이트웨이 `compose.yaml`의 Langfuse 서비스. v3부터 ClickHouse·Redis·S3가 필요해 단독 컨테이너로는 뜨지 않았다. 공식 compose로 따로 띄운다.

### 출처

- `docs/research/sources-2026-09-23.md`. 조사 에이전트 3개가 공식 문서·릴리스·PyPI를 직접 열어 확인했다.

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

[0.3.1]: https://github.com/sgustjd2/ai-work-skill/releases/tag/v0.3.1
[0.3.0]: https://github.com/sgustjd2/ai-work-skill/releases/tag/v0.3.0
[0.2.0]: https://github.com/sgustjd2/ai-work-skill/releases/tag/v0.2.0
[0.1.0]: https://github.com/sgustjd2/ai-work-skill/releases/tag/v0.1.0
