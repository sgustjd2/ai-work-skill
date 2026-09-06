# ai-work-skill

생성형 AI 서비스 개발 조직(데이타솔루션)에서 매일 하는 일을 Claude Code가 회사 표준대로 해내게 하는 스킬 세트.
FastAPI 서비스 골격, GitLab CI/CD, 코드 리뷰·테스트·리팩토링, LiteLLM 게이트웨이 운영, 아키텍처 문서(docx)·덱(pptx) 생성, AI 트렌드 브리프, AI 초안 사람화(3축 진단·확인 후보)를 다룬다.
문서는 데이타솔루션 팔레트와 한국 기업 문서체로 나오고, AI 문체는 훅이 파일에 닿기 전에 차단한다.

- 설계 문서: [docs/PRD.md](docs/PRD.md) · 구현 규약: [CLAUDE.md](CLAUDE.md) · 골든 재현 결과: [eval/results.md](eval/results.md) · 외부 사실 출처: [docs/research/sources-2026-09-04.md](docs/research/sources-2026-09-04.md)
- 합류 첫 주 확인 목록(공식 템플릿·GitLab 버전·게이트웨이 등 실환경 값): [PRD 부록 F](docs/PRD.md#부록-f-합류-첫-주-확인-목록-결정값을-실제로-바꿀-정보)
- 상태: **완성** (2026-09-04, M5 사람화 2026-09-06). M0~M5 전체 구현. 스킬 12개 + MCP 서버 2개(docgen·litellm-ops) + 훅 2개. 검증: `uv run pytest` 179 PASS(+manual 1), `ruff check`·`format --check` clean, `doc_lint --all` 하드 위반 0(103파일). 생성 FastAPI 골격이 그대로 `uv run pytest` 통과, `config.example.yaml` 이 `config_validate` 통과, 설계서 docx·덱 pptx 가 실제 렌더되고 `check_output` PASS. 골든 프롬프트 8개 재현 결과는 [eval/results.md](eval/results.md) 를 본다(09 사람화는 스킬 세션에서 재현). 선행 자산: `../ui-skill-set`(구조·훅 원형), `../품의서/.claude/skills/review-report-writer`(문체 규칙 원형), 위키독스 "누구나 할 수 있는 AI 글쓰기" 02장(3축 개념, [docs/research/sources-2026-09-06.md](docs/research/sources-2026-09-06.md)).

## 구성

| 계층 | 내용 |
|---|---|
| 에셋 | `templates/STYLE.md`(문서 계약), `themes/datasolution.json`(팔레트·폰트·치수), `skills/fastapi-service/assets/`(예제 서비스), `skills/llm-gateway/assets/config.example.yaml` |
| 룰 | 스킬 12개: `ai-init` `doc-write` `deck-write` `fastapi-service` `gitlab-ci` `py-review` `py-test` `py-refactor` `llm-gateway` `model-serving` `ai-trend-brief` `humanize` |
| 하네스 | `templates/doc_lint.py`(편집 전 AI 문체 차단·종료 전 점검), `templates/py_format.py`(편집 후 ruff) |
| 도구 | MCP `docgen`(md → docx/pptx, 구성도·차트, 미리보기, 양식 추출), `litellm-ops`(게이트웨이 상태·비용·키·config 검증 12툴), GitLab 공식 MCP(설정만), archify(외부 스킬, 독립 HTML 다이어그램, `/ai-init --with-archify` 로 전역 설치, 규칙은 `references/diagram-tools.md`) |

## 설치

플러그인으로:

```bash
claude plugin marketplace add sgustjd2/ai-work-skill
```

그다음 `/plugin install ai-work-skill@ai-work-skill`. MCP 서버(`docgen`·`litellm-ops`)는 `uv` 가 필요하다. 프로젝트에 훅·`STYLE.md`·규약을 넣으려면 `/ai-init` 을 실행한다(문서 스킬은 `STYLE.md` 가 있어야 동작한다). 시퀀스·데이터 흐름·상태 다이어그램이나 공유용 HTML 구성도가 필요하면 `/ai-init --with-archify` 로 [archify](https://github.com/tt-a1i/archify)(MIT, Node 18+)를 사용자 전역에 설치한다. 본문 구성도는 여전히 docgen 이 회사 테마로 그린다.

## 사용 예시

설치한 뒤에는 특별한 명령이 필요 없다. Claude Code 에게 평소 말로 부탁하면 맞는 스킬이 뜬다. 아래는 무슨 말이 어떤 스킬로 이어지고 무엇이 나오는지다.

| 하고 싶은 일 | 이렇게 말한다 | 나오는 것 |
|---|---|---|
| 설계서 | "LLM 게이트웨이 도입 설계서 docx 로 써줘" | `docs/arch/*.doc.md` 와 렌더된 docx(표지·목차·구성도·표) |
| 덱 | "이 설계서를 경영진 10장 덱으로" | `docs/deck/*.deck.md` 와 pptx(헤드 메시지·네이티브 차트·편집 가능한 구성도) |
| 서비스 골격 | "문서 요약 API 서비스 골격 잡아줘. 게이트웨이 경유, 테스트·Docker 포함" | 실행되는 FastAPI 프로젝트(그대로 `uv run pytest` 통과) |
| CI | "이 프로젝트에 GitLab CI 만들어줘" | `.gitlab-ci.yml`·MR 템플릿·CODEOWNERS |
| 코드 리뷰 | "MR !42 리뷰해줘" | 심각도·파일:줄·수정안 형식 리뷰(게시는 승인 후) |
| 게이트웨이 설정 | "Azure 두 리전에 Bedrock 폴백으로 litellm config 만들어줘" | 검증을 통과하는 `config.yaml` |
| 트렌드 | "이번 주 AI 트렌드 브리프" | `docs/trends/YYYY-Www.md`(항목마다 출처·영향·적용) |
| AI 초안 사람화 | "이 초안 AI 티 나는데 내 재료로 고쳐줘" | 3축(문체·재료·판단) 진단 보고와 확인 후보 표, 재료를 받은 뒤 재작성 |
| 독립 다이어그램 | "게이트웨이 호출 시퀀스를 HTML 로 그려줘" | archify JSON(`docs/diagrams/`) → 검증된 독립 HTML(`docs/_build/diagrams/`), 필요하면 PNG 로 문서 첨부 |

### 스킬 호출 명령 (슬래시 커맨드)

말로 부탁하면 스킬이 자동으로 뜨지만, 슬래시 커맨드로 직접 부를 수도 있다. 모든 스킬은 `user-invocable` 이라 Claude Code 에서 `/<스킬 이름>` 으로 호출한다. 대괄호는 선택 인수다(없으면 스킬이 되묻거나 기본값으로 진행한다). 트리거 어휘 전체는 [skills/llms.txt](skills/llms.txt) 에 있다.

| 스킬 | 호출 | 인수 | 하는 일 |
|---|---|---|---|
| `ai-init` | `/ai-init [--update \| --with-ui \| --with-archify \| --logo <경로> \| --no-python]` | 설치 옵션 | 프로젝트에 STYLE.md·훅·CLAUDE 규약·docs 골격·GitLab MCP 설치. `--with-ui` 는 ui-skill-set, `--with-archify` 는 archify 를 함께 |
| `doc-write` | `/doc-write [문서 유형과 주제 \| 수정할 파일 \| 리뷰할 파일]` | 주제 또는 파일 | 설계서·검토보고서·가이드·런북·ADR·회의록·브리프를 한국 기업 문서체로 쓰고 docx 렌더 |
| `deck-write` | `/deck-write [덱 목적·독자·장수 \| 원본 .doc.md 경로]` | 목적·장수 또는 원본 | 경영진·기술·교육 슬라이드를 헤드 메시지·개조식·회사 테마로 pptx |
| `fastapi-service` | `/fastapi-service [서비스 이름과 기능 한 줄]` | 서비스 한 줄 | 게이트웨이 경유 FastAPI 골격 생성(테스트·Docker·CI) |
| `gitlab-ci` | `/gitlab-ci [생성 \| 진단 <pipeline id\|MR> \| 배포 대상]` | 모드·대상 | GitLab CI/CD 파이프라인 생성·진단·운영 |
| `py-review` | `/py-review [MR 번호 \| 브랜치 \| 경로 \| (없으면 작업 트리 diff)]` | 대상 | 심각도·파일:줄·수정안 형식 코드 리뷰(게시는 승인 후) |
| `py-test` | `/py-test [대상 모듈·함수 \| 실패 로그]` | 대상 | pytest 테스트 작성·정리(respx 모킹, live_llm 격리) |
| `py-refactor` | `/py-refactor [대상 패키지·모듈]` | 대상 | 모듈화·순환 import·레이어 정리 계획과 안전한 수행(ADR) |
| `llm-gateway` | `/llm-gateway [구축 \| 모델 추가 \| 키 발급 \| 장애 진단 \| 비용]` | 모드 | LiteLLM 게이트웨이 설계·구축·운영(config 검증 후 배포) |
| `model-serving` | `/model-serving [모델 이름 \| GPU 사양 \| 벤치 대상 URL]` | 모델·사양 | vLLM 서빙·VRAM 산정·양자화·벤치 |
| `ai-trend-brief` | `/ai-trend-brief [주간 \| 월간 \| 주제]` | 기간·주제 | AI 트렌드를 우리 서비스 영향·적용까지 담아 브리프 |
| `humanize` | `/humanize [사전 \| 진단 <파일> \| 재작성 <파일>]` | 모드·파일 | AI 초안을 3축(문체·재료·판단)으로 진단하고 확인 후보 표를 뽑아 재작성 |

archify 는 이 플러그인의 스킬이 아니라 `/ai-init --with-archify` 로 설치하는 외부 스킬이다. 설치 뒤에는 "게이트웨이 시퀀스 HTML 로 그려줘" 처럼 말로 부르거나 `node ~/.claude/skills/archify/bin/archify.mjs` 를 직접 쓴다(규칙은 [references/diagram-tools.md](references/diagram-tools.md)).

### 문서 한 편을 끝까지

설계서를 부탁하면 스킬이 `STYLE.md` 를 읽고 한 줄로 방향을 선언한 뒤 `.doc.md` 로 초안을 쓴다. 그다음 렌더링한다.

```bash
uv run --project mcp/docgen python -m docgen render-docx docs/arch/gateway.doc.md --out docs/_build/gateway.docx
```

편집 도중 em-dash 나 상투어, 이모지를 쓰려 하면 훅이 저장 직전에 막는다. 색은 데이타솔루션 팔레트만 나온다.

### 직접 실행하는 도구

스킬을 거치지 않고 스크립트나 MCP 를 바로 부를 수도 있다.

```bash
# 서비스 골격(옵션: --with-db --with-redis --with-sse --with-auth --with-rag --with-jobs --with-otel)
uv run python skills/fastapi-service/scripts/scaffold.py --name summ_api --target ./summ_api --with-sse

# 게이트웨이 설정 검증(V1~V8)
uv run --project mcp/litellm_ops python -m litellm_ops config-validate config.yaml

# 순환 import·레이어 위반 검사
uv run python skills/py-refactor/scripts/import_graph.py summ_api

# 서빙 VRAM 산정
uv run python skills/model-serving/scripts/vram_estimate.py --params 32 --dtype fp16 --ctx 32768 --batch 8

# 초안의 확인 후보(수치·출처·인용·고유명사·제도)·평균값 신호·재료 밀도
uv run python skills/humanize/scripts/humanize_scan.py docs/arch/gateway.doc.md

# 독립 다이어그램(archify, /ai-init --with-archify 로 설치한 뒤)
node ~/.claude/skills/archify/bin/archify.mjs validate architecture docs/diagrams/gateway.architecture.json --quality showcase --json
node ~/.claude/skills/archify/bin/archify.mjs deliver architecture docs/diagrams/gateway.architecture.json docs/_build/diagrams/gateway.html --quality showcase --json
```

MCP 로 쓸 때는 `docgen` 이 문서·덱·구성도를, `litellm-ops` 가 게이트웨이 상태·비용·키·설정 검증을 툴로 노출한다. 키 발급·차단은 `LITELLM_OPS_ALLOW_WRITE=true` 일 때만 동작한다.

> 위 예시는 저장소 기준 명령이다. 실제 사내 환경(공식 문서 템플릿, GitLab 버전, 게이트웨이 주소)에 맞춘 확인은 PRD 부록 F 를 따른다.

## 다른 에이전트에서 쓰기

Claude Code 플러그인이 기본이지만, 표준을 써서 Codex·Gemini·Grok 에도 붙일 수 있다. MCP 서버(`docgen`·`litellm-ops`)는 MCP 를 지원하는 어느 호스트에서도 같은 툴을 노출하고, 스크립트는 표준 라이브러리 CLI 라 셸에서 바로 돌아간다. 스킬은 마크다운이라 호스트가 지시로 읽는다. 호스트에 묶이는 것은 편집 직전 자동 차단(훅)뿐이고, 그 검사도 CI 나 pre-commit 으로 대체된다.

Codex CLI(0.153.3)에서는 실제 에이전트가 두 MCP 서버를 호출하는 것까지 확인했다(`docgen/theme_export`·`litellm-ops/config_validate`). Gemini CLI(0.58.0)는 `gemini mcp list` 에서 두 서버가 `Connected` 로 붙는 것을 확인했고(에이전트 턴은 로그인 필요), Antigravity IDE 용 MCP 설정도 넣었다. 호스트별 설정과 검증 상태는 [docs/hosts.md](docs/hosts.md), 벤더 중립 진입 문서는 [AGENTS.md](AGENTS.md) 를 본다. 저장소 루트에 Claude 용 `.claude-plugin/` 과 Codex 용 `.codex-plugin/` 을 함께 두었다.

## 개발

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run python -X utf8 templates/doc_lint.py --all docs skills references README.md
```

구조·규약은 [CLAUDE.md](CLAUDE.md), 검증 기준선은 [eval/results.md](eval/results.md), 요구사항 추적은 [docs/traceability.md](docs/traceability.md) 를 본다.
