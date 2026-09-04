---
doc_lint: off
---

# ai-work-skill PRD

| | |
|---|---|
| 버전 | 0.2 (초안, 구현 전). 0.1의 누락 점검 결과 반영: MCP 경로 해석(§9), H6 한국 문서 기호 예외·H9 자리표시자 예외·H10 렌더러 우회 차단(§7.1), S18 용어 통일(§7.2), GenAI 패턴·RAG·프롬프트 관리(§8.4, §8.12), 팀 예산 툴(§9.1), 차트 DSL·docx 템플릿 모드·결과물 위치(§10), 구현자용 `CLAUDE.md`(§11.9), 금지 표현 사전 전문(부록 B), 추적표(부록 E), 합류 첫 주 확인 목록(부록 F) |
| 작성일 | 2026-09-04 |
| 진행 | **M0~M3 완료**(2026-09-04). M0 골격·훅, M1 docgen(문서·덱), M2 개발 스킬(fastapi-service+scaffold 외), M3 LLM 운영(llm-gateway·litellm-ops MCP 12툴·model-serving·ai-trend-brief). 167 테스트 PASS(+manual 1), ruff clean, 자기 검사 하드 0(98문서). 생성 FastAPI 골격 실제 pytest 통과, config.example 검증 통과, 설계서 docx·덱 pptx 실제 렌더. 남은 것은 M4(배포·매니페스트·eval·ui 연동) |
| 작성 | Claude Fable 5.1 (PRD 전담) |
| 구현 | Claude Opus 4.8. **이 문서만 보고** 코드를 만든다. 결정이 필요한 곳은 §14의 추천값으로 진행한다 |
| 저장소 | `E:\workspace\ai-work-skill` (플러그인 이름 `ai-work-skill`, 배포 시 `sgustjd2/ai-work-skill`) |
| 선행 자산 | `E:\workspace\ui-skill-set` (3계층 구조·훅·설치기 원형, MIT) · `E:\workspace\품의서\.claude\skills\review-report-writer` (한국 기업 문서체 규칙 원형) · `E:\workspace\agent-harness` (플러그인 검증 규약) |
| 대상 조직 | 데이타솔루션(Datasolution Inc.) 생성형 AI 서비스 개발 조직. 사용자는 2026년 9월 합류 예정 |

---

## 0. 한 줄 요약

생성형 AI 서비스 개발 조직에서 매일 하는 일, 즉 **FastAPI 서비스 구축 · GitLab CI/CD · 코드 리뷰/단위 테스트/리팩토링 · LiteLLM 게이트웨이 운영 · 아키텍처 문서와 덱 작성 · AI 트렌드 조사**를 Claude Code가 "회사 표준대로" 해내게 하는 **스킬 11개 + MCP 서버 2개 + 훅 2개**. 문서는 데이타솔루션 색과 한국 기업 문서체로 나오고, "AI가 쓴 티"(em-dash·상투어·굵은 라벨 목록·이모지·요약 반복)는 설득이 아니라 **파일에 닿기 전에 차단**한다. 구조는 ui-skill-set의 3계층(에셋·룰·하네스)을 그대로 쓰고, 문서 생성기와 게이트웨이 운영 도구를 MCP로 얹는다.

---

## 1. 배경과 문제

### 1.1 맥락: 채용 공고와 이 문서의 대응

| 공고 항목 | 실제로 하게 될 일 | 이 PRD의 대응 |
|---|---|---|
| FastAPI 기반 개발 환경 구축 | 새 서비스 골격, 설정·로깅·테스트·Docker 표준 | `fastapi-service` 스킬 (§8.4) |
| GitLab 기반 CI/CD 빌드/배포 | `.gitlab-ci.yml`, 컨테이너 레지스트리, 환경별 배포, 파이프라인 장애 대응 | `gitlab-ci` 스킬 + GitLab 공식 MCP (§8.5, §9.3) |
| 코드 모듈화·구조개선·리팩토링 | 순환 import 해소, 레이어 분리, 안전한 이동 | `py-refactor` 스킬 + `import_graph.py` (§8.8) |
| 코드 리뷰 및 Unit 테스트 | MR 리뷰, pytest 표준, LLM 호출 모킹 | `py-review` · `py-test` 스킬 (§8.6, §8.7) |
| 개발 스택 가이드·교육 | 온보딩 가이드, 런북, 교육 덱 | `doc-write` · `deck-write` 스킬 (§8.2, §8.3) |
| 생성형 AI 서비스 분석/설계/개발/유지보수 | 설계서, 구성도, AS-IS/TO-BE, 인터페이스 정의, RAG·에이전트·프롬프트 관리·비동기 작업 패턴 | `doc-write` + `docgen` MCP (§8.2, §9.2, §10), `references/genai-patterns.md` (§8.12), `fastapi-service --with-rag` (§8.4) |
| API·오픈소스 활용 서비스 개발 | LiteLLM·vLLM·Langfuse 등 조합 | `llm-gateway` · `model-serving` (§8.9, §8.10) |
| 최신 AI 기술 트렌드 조사·적용 | 주간 브리프, 적용 아이디어 | `ai-trend-brief` 스킬 (§8.11) |
| LLM 이해·API 사용 / 모델 최적화·서빙 | 게이트웨이 클라이언트 패턴, 양자화·VRAM 산정·벤치 | `llm-gateway` · `model-serving` |
| 클라우드(Azure/AWS/GCP) | Azure OpenAI·Bedrock·Vertex 라우팅, 컨테이너 배포 | `llm-gateway/references/{azure,bedrock,vertex}.md`, `gitlab-ci/references/deploy-targets.md` |
| LiteLLM·LLM Gateway·API Gateway 구축 | config.yaml, 가상 키, 예산, 폴백, 관측 | `llm-gateway` 스킬 + `litellm-ops` MCP (§9.1) |

### 1.2 증상

- **개발**: 세션마다 프로젝트 골격이 다르다. 어떤 날은 `app/main.py` 한 파일, 어떤 날은 6단 레이어. 테스트는 있다가 없다가 하고, LLM 호출은 벤더 SDK로 직접 붙었다가 게이트웨이로 붙었다가 한다. CI 파일은 매번 처음부터 쓴다.
- **게이트웨이 운영**: LiteLLM `config.yaml`이 손으로 자라난다. 폴백이 없는 모델명을 가리키고, 키가 yaml에 박히고, "지금 어느 엔드포인트가 죽었는지"는 curl 여러 번을 쳐야 안다.
- **문서**: Claude가 쓴 보고서는 읽는 사람이 3초 안에 안다. em-dash(—), "혁신적인·차세대·시너지", `**굵은 라벨**: 설명` 목록, 항목이 정확히 3개인 리스트, 제목의 이모지, 마지막의 "결론적으로" 요약. 색은 보라나 Office 기본 파랑이고 회사 색이 아니다. 덱은 제목 + 글머리표 6개의 벽이다.
- **트렌드 조사**: 링크 나열로 끝나고 "우리 서비스에 무엇을 바꿔야 하는가"가 없다.

### 1.3 원인

ui-skill-set PRD §1.2의 결론이 문서와 코드에도 그대로 적용된다.

1. LLM은 **통계적 기본값**을 가진다. UI에서 보라 그라데이션이 나오듯, 문서에서는 em-dash와 3항목 리스트가, 코드에서는 "한 파일에 다 넣기"가 나온다. 브리프를 읽기 전에 기본값으로 점프한다.
2. **프롬프트만으로는 못 막는다.** "가급적 쓰지 마라"는 무시된다. 이진 규칙("0개")과 기계적 강제가 있어야 지켜진다 (ui-skill-set 실측: 골든 프롬프트 5개 하드 위반 0, 코어 일치 100%는 훅이 있을 때의 수치다).
3. **일관성의 실체는 계약 파일**이다. UI에서 tokens.css가 그 역할을 했다. 문서에서는 **STYLE.md + 테마 JSON**, 코드에서는 **골격 템플릿 + pyproject 규약**, 게이트웨이에서는 **검증된 config.yaml**이 그 역할을 한다.
4. 문서 생성은 텍스트 생성과 다르다. docx·pptx는 XML이라 모델이 직접 쓰면 깨지거나 기본 테마가 남는다. **결정적 렌더러**(Markdown DSL → python-docx/python-pptx)가 있어야 색·폰트·여백이 매번 같다.

### 1.4 결론

네 겹이 동시에 있어야 한다.

| 계층 | 무엇 | 하는 일 |
|---|---|---|
| ① 에셋 | `STYLE.md` + `themes/datasolution.json` + 서비스 골격 템플릿 + `config.example.yaml` | 무엇이 "우리 회사 것"인지 |
| ② 룰 | 스킬 11개 | 절차와 판단. 언제 무엇을 읽고 어떤 순서로 만드는지 |
| ③ 하네스 | `doc_lint.py`(편집 전 차단 + 종료 전 점검), `py_format.py`(편집 후 포맷) | 어겼을 때 무엇이 일어나는지 |
| ④ 도구 | `docgen` MCP(문서 렌더링·린트·미리보기·기존 양식 추출), `litellm-ops` MCP(게이트웨이 상태·비용·키·설정 검증), GitLab 공식 MCP | 모델이 직접 못 하는 결정적 작업 |

---

## 2. 목표 / 비목표

### 목표

- G1. `/ai-init` 한 번으로 프로젝트에 `STYLE.md` · 훅 · `.claude/settings.json` · CLAUDE.md 규약 · `docs/` 골격이 설치된다. 5분 안에 커밋 가능한 상태.
- G2. "설계서 써줘", "덱 만들어줘", "서비스 골격 잡아줘", "CI 만들어줘", "이 MR 리뷰해줘", "litellm 설정" 같은 요청에서 스킬이 **이름을 몰라도** 자동으로 뜬다 (10개 프롬프트 중 9개 이상).
- G3. 문서의 AI 티(§7.1 하드 룰 10종)는 **파일에 닿기 전에 차단**되고, 소프트 룰(§7.2)은 종료 전 한 번 지적된다. 예외는 마커와 이유가 있어야 통과한다.
- G4. 생성된 docx·pptx는 **데이타솔루션 팔레트(부록 A)와 지정 폰트만** 쓴다. 생성물 XML에 테마 밖 색이 0개. Office에서 복구 프롬프트 없이 열린다.
- G5. 같은 프롬프트를 3번 돌려도 문서 구조(섹션 순서·표 열·덱 레이아웃)와 코드 골격(디렉터리·설정 방식·테스트 배치)이 같다.
- G6. LiteLLM `config.yaml`은 배포 전에 검증된다(폴백 참조 무결성, 인라인 시크릿 0, 환경변수 참조 존재). 게이트웨이 상태·비용·키는 curl 없이 MCP 툴 한 번으로 본다.
- G7. FastAPI 골격은 생성 직후 `uv run pytest` 통과, `docker build` 성공, `.gitlab-ci.yml`이 GitLab CI Lint를 통과한다.
- G8. 팀 규모와 무관하게 동작한다. 플러그인 없는 작업자도 저장소에 커밋된 훅과 `STYLE.md` 때문에 같은 검사를 받는다. Windows와 Linux에서 동일하게 동작한다.

### 비목표

- 회사 전용 정보(내부 시스템명, 실제 고객사, 사내 URL)를 저장소에 넣는 것. 전부 `STYLE.md`·환경변수·프로젝트 파일에서 들어온다. 회사 로고도 저장소에 넣지 않는다(`/ai-init --logo <경로>`로 프로젝트에만 복사).
- 주간보고 xlsx 작성. `E:\workspace\weekly-report`의 스킬이 이미 하며 회사마다 양식이 다르다.
- 프론트엔드 UI 규약. `ui-skill-set`이 담당한다. 이 프로젝트는 `/ai-init --with-ui`로 그것을 **호출**만 한다(§5.5).
- 자체 LLM 게이트웨이 구현. LiteLLM을 쓴다. 자체 GitLab MCP 구현. 공식 MCP를 쓴다.
- Kubernetes 매니페스트 생성기. 배포 대상은 참조 문서(§8.5 `deploy-targets.md`)로만 다룬다.
- 프롬프트 평가 프레임워크 자체 구현. `py-test`의 골든 파일·`live_llm` 계약 테스트까지만 하고, 대규모 평가는 promptfoo 같은 외부 도구를 `references/genai-patterns.md`에서 안내한다.
- 기존 docx·pptx의 서식 보존 편집(라운드트립). 기존 문서는 `docx_to_md`/`pptx_to_md`로 읽어 구조를 배우고 새로 렌더링한다. 회사 양식은 템플릿 모드(§10.5, §10.6)로 재사용한다.

---

## 3. 재사용 자산 분석

"무엇을 가져오고 무엇을 버리는지"만 적는다. 경로는 이 PC 기준이며 Opus는 구현 시 해당 파일을 직접 열어 본다.

### 3.1 로컬 자산

| 자산 (경로) | 가져올 것 | 버릴 것 | 라이선스 |
|---|---|---|---|
| **ui-skill-set** (`E:\workspace\ui-skill-set`) | 3계층 구조와 PRD 형식. `templates/design-lint.mjs`의 **훅 I/O 계약**(`--pre` exit 2 + stderr, `--stop` 1회 block + `stop_hook_active` 가드, `--all` CI, 최상위 catch → exit 0, 128KB 스킵, 민감 파일 스킵), **안티 데드락**(같은 파일·같은 룰 3회 → 4번째 통과), **마커 문법**(`allow <rule>: <이유>`, 이유 필수). `templates/install.mjs`의 `mergeSettings`/`fillFrontmatter`/`appendSnippet` 로직(멱등 병합). `skills/ui-design/references/banned.md`·`korean-typography.md`의 문서 관련 규칙(em-dash 금지, 상투어, 존댓말 통일, 숫자·날짜·통화 표기, 느낌표 금지). `eval/` 골든 프롬프트 + 고정 요소 + 일관성 측정 방식. `skills/llms.txt`, `.claude-plugin/` 매니페스트 형식 | CSS 토큰·Tailwind 브릿지·Figma 동기화·Playwright 감사(전부 UI 전용). **Node 런타임**: 이 프로젝트의 훅은 Python 표준 라이브러리로 다시 쓴다(§14 D1). 정규식과 구조는 옮기되 파일은 복사하지 않는다 | MIT (같은 작성자) |
| **review-report-writer** (`E:\workspace\품의서\.claude\skills\review-report-writer`) | `references/writing-rules.md`의 **사실·추론·권고 구분** 표현, **AI식 표현 11개**, 좋은 예/나쁜 예 쌍, 비교표 규칙("검토 의견" 열 필수, 임의 점수화 금지). `SKILL.md`의 **결론 7항목**, 질문 최대 3개, `[확인 필요]`·`[금액 입력 필요]` 마커, 출력 형태 5종. `references/report-structure.md`의 16단계 구조와 **통합 원칙**("억지로 채우지 않는다"). `quality-checklist.md` | 장비 구매 특화 평가 기준 19개(참조로만 링크). 템플릿 3개는 `doc-write`의 문서 유형 표에 흡수 | 사용자 소유 |
| **weekly-report** (`E:\workspace\weekly-report`) | 스킬을 "인터뷰 → 정리 → 최종 검토"로 쪼개고 CLAUDE.md가 순서를 지정하는 방식. `.docx`의 실제 폰트(**맑은 고딕**, 본문 `w:eastAsia` 지정) | 주간보고 xlsx 자체(비목표) | 사용자 소유 |
| **agent-harness** (`E:\workspace\agent-harness`) | **런타임 zero-dependency 원칙**(훅·설치기는 표준 라이브러리만), 검증은 authoritative 라이브러리(PyYAML·jsonschema·pytest)로, **안정적 진단 코드**(테스트는 코드로 assert, 문구 아님), 실험 기록에 시크릿 금지, `pyproject.toml`의 pytest 마커 3종(deterministic/host_cli/manual) | 오케스트레이션·플랜 구조(다른 문제) | 사용자 소유 |

### 3.2 외부 자산 (2026-09-04 확인)

| 자산 | 사용 방식 | 확인된 사실 | 라이선스 |
|---|---|---|---|
| **GitLab 공식 MCP 서버** | 설정만. 자체 구현 안 함 | GitLab 인스턴스의 `/api/v4/mcp` 엔드포인트. Beta. GitLab 19.2부터 **Free 티어 포함**. OAuth 2.0(Claude Code에서 `/mcp`로 브라우저 승인). GitLab Duo 활성화 + beta 기능 허용 필요. 툴 40여 개: `get_merge_request`, `get_merge_request_diffs`, `save_note`, `save_merge_request_review`, `get_pipeline`, `get_pipeline_jobs`, `get_job`(트레이스 포함), `save_pipeline`(retry/cancel), `get_repository_file`, `add_commit`, `list_work_items`, `search` 등. 인스턴스가 18.3 미만이거나 beta 비활성이면 커뮤니티 `@zereight/mcp-gitlab`(PAT) 폴백 | GitLab 문서 |
| **LiteLLM Proxy** | 게이트웨이. `llm-gateway` 스킬과 `litellm-ops` MCP의 대상 | v1.85.0(2026-03) 이후. config 최상위 키: `model_list`, `litellm_settings`(`fallbacks`, `context_window_fallbacks`, `num_retries`, `request_timeout`, `success_callback`, `cache`), `router_settings`(`routing_strategy`, `model_group_alias`, redis), `general_settings`(`master_key`, `database_url`, `background_health_checks`, `health_check_interval`, `alerting`), `environment_variables`, `credential_list`, `guardrails`, `mcp_servers`. 시크릿은 `os.environ/NAME` 참조. Admin API: `GET /health`, `/health/readiness`, `/health/liveliness`, `/model/info`, `POST /key/generate`, `GET /key/info`, `POST /key/update`, `/key/block`, `/key/unblock`, `GET /spend/logs`, `GET /global/spend/report?group_by=`, `/team/new`, `/team/info`. 비용 헤더 `x-litellm-response-cost`. 인증 `Authorization: Bearer <master_key>` | MIT |
| **FastMCP** | MCP 서버 2개의 프레임워크 | 4.0.1(2026-09-02). MCP 프로토콜 2026-07-28(세션리스) + 구버전 협상. `@mcp.tool`, stdio 기본, `ToolError`. Python ≥ 3.10 | Apache-2.0 |
| **python-docx 1.2 / python-pptx 1.0** | docx·pptx 렌더러 | East Asian 폰트는 `w:eastAsia` / `a:ea` 를 직접 지정해야 한글이 지정 폰트로 나온다(§10.5 함정 목록) | MIT |
| **markdown-it-py + mdit-py-plugins** | `.doc.md`/`.deck.md` 파싱 | `MarkdownIt("gfm-like")`로 표·취소선 지원, `front_matter_plugin` | MIT |
| **Pillow** | 구성도 PNG 렌더러(docx 삽입용) | 한글 폰트 파일을 찾아 `ImageFont.truetype`로 로드해야 함. 기본 폰트는 한글 없음 | HPND |
| **Pretendard** (`E:\workspace\Pretendard-1.3.9`) | 웹 UI 기본 폰트(ui-skill-set과 동일). Office 문서는 기본 **맑은 고딕**(§14 D3) | 데이타솔루션 웹사이트 body 폰트도 Pretendard | OFL |

---

## 4. 사용자와 시나리오

**사용자**: 데이타솔루션 생성형 AI 서비스 개발 조직의 개발자·아키텍트. 한국어. Windows 개발 PC + Linux 서버. GitLab(자체 호스팅 가정), Azure/AWS/GCP 혼용, Claude Code가 주 도구. 문서는 결재권자(비개발자)와 개발자 둘 다 읽는다.

| # | 시나리오 | 흐름 | 성공 조건 |
|---|---|---|---|
| SC-1 | 신규 프로젝트 세팅 | `/ai-init` → 질문 3개(조직 표기, 문서 톤, Python 프로젝트 여부) → `STYLE.md`, `.claude/hooks/doc_lint.py`(+`py_format.py`), `.claude/settings.json` 병합, `CLAUDE.md` 스니펫, `docs/{adr,arch,trends}/`, `.mcp.json`에 GitLab 항목 | 5분 내 커밋 가능 |
| SC-2 | 설계서 작성 | "LLM 게이트웨이 도입 설계서 docx로" → `doc-write` 자동 로드 → `STYLE.md` 읽음 → **문서 리드 1줄** → `.doc.md` 작성(구성도는 ` ```diagram ` 블록) → 훅 통과 → `docgen.render_docx` → 미리보기 PNG 확인 → `docs/arch/llm-gateway-설계서.docx` | 하드 위반 0, 테마 밖 색 0, 표지·개정이력·목차·머리글·쪽번호 있음 |
| SC-3 | 경영진 덱 | "위 설계서를 10장 덱으로" → `deck-write` → `.deck.md`(슬라이드당 헤드 메시지 1개, 개조식, ≤ 6줄) → `docgen.render_pptx` → 회사 템플릿(.pptx)이 있으면 그 마스터 사용 | 슬라이드마다 주장 문장 헤드라인, 글머리표 벽 없음, 구성도는 편집 가능한 도형 |
| SC-4 | 서비스 골격 | "문서 요약 API 서비스 골격, LiteLLM 경유, 테스트·Docker·CI 포함" → `fastapi-service` → `scaffold.py` → `gitlab-ci` → `py-test` | `uv run pytest` 통과, `docker build` 성공, CI Lint 통과, LLM 호출은 게이트웨이 경유만 |
| SC-5 | MR 리뷰 | "MR !42 리뷰" → `py-review` → GitLab MCP `get_merge_request_diffs` → 체크리스트 기반 리뷰 → 사용자 승인 후 `save_merge_request_review` | 심각도·파일:줄·수정안 형식. 승인 없이 코멘트 게시 안 함 |
| SC-6 | 게이트웨이 설정 | "Azure gpt-4o 두 리전 + Bedrock Claude 폴백 + 팀별 예산" → `llm-gateway` → `config.yaml` → `litellm-ops.config_validate` → 배포 → `gateway_health` | 검증 오류 0, 시크릿 인라인 0, 폴백 참조 무결 |
| SC-7 | 장애 대응 | "gpt-4o 응답이 느려" → `litellm-ops.gateway_health` + `test_completion` → 죽은 엔드포인트 식별 → 폴백 동작 확인 → 런북대로 조치 | curl 없이 3 툴 호출 안에 원인 위치 |
| SC-8 | 리팩토링 | "services 모듈 순환 import 정리" → `py-refactor` → `import_graph.py` → 특성화 테스트 → 이동 계획(ADR) → 작은 MR 단위 | 순환 0, 레이어 위반 0, 동작 변화 0 |
| SC-9 | 트렌드 브리프 | "이번 주 AI 트렌드" → `ai-trend-brief` → 출처 5~7개 → `docs/trends/2026-W36.md` (사실/영향/적용/확인 필요) | 모든 항목에 URL·날짜, 상투어 0, 적용 아이디어에 대상 서비스 명시 |
| SC-10 | 기존 회사 양식 재사용 | "이 회사 템플릿 pptx 스타일로" → `docgen.theme_from_pptx` → `themes/company.json` 생성 → 이후 렌더링에 사용 | 회사 마스터의 색·폰트·레이아웃 이름이 그대로 쓰임 |

---

## 5. 아키텍처: 3계층 + 도구층

```
┌─ 프로젝트 (설치 결과, 저장소에 커밋) ─────────────────────────────────────┐
│  STYLE.md                   ← 문서 계약. frontmatter는 린터가 읽음          │ ① 에셋
│  docs/theme.json (선택)      ← 회사 템플릿에서 추출한 테마 (기본은 플러그인 것)│
│  CLAUDE.md (+스니펫)         ← "@STYLE.md 읽고 해당 스킬 절차를 따름"        │
│  .claude/settings.json      ← PreToolUse(차단) + Stop(점검) + PostToolUse   │ ③ 하네스
│  .claude/hooks/doc_lint.py  ← Python 표준 라이브러리, 의존성 0              │
│  .claude/hooks/py_format.py ← ruff 있으면 포맷, 없으면 no-op                │
│  .mcp.json                  ← gitlab(공식, http) 항목                        │ ④ 도구
└─────────────────────────────────────────────────────────────────────────┘
┌─ ai-work-skill 저장소 (플러그인) ──────────────────────────────────────────┐
│  skills/*/SKILL.md          ← 절차 11개. 각 ≤ 200줄, references는 필요할 때 │ ② 룰
│  references/                ← 스킬 공용: writing-rules-ko, python-conventions│
│  themes/datasolution.json   ← 팔레트·폰트·치수 (부록 A)                     │ ① 에셋
│  templates/                 ← /ai-init이 프로젝트에 복사하는 원본            │
│  mcp/docgen                 ← 문서 렌더러 + MCP 서버 (python-docx/pptx)     │ ④ 도구
│  mcp/litellm_ops            ← 게이트웨이 운영 MCP 서버                       │
│  .mcp.json                  ← 위 두 서버 (uv run --project ${CLAUDE_PLUGIN_ROOT}/…)│
│  eval/                      ← 골든 프롬프트 + 자동 검사                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.1 ① 에셋

- **`STYLE.md`**는 사람이 읽는 문서 계약이자 린터의 설정 파일이다. YAML frontmatter(기계용, §11.4) + 본문 6섹션(사람용). ui-skill-set의 `DESIGN.md`와 같은 역할.
- **테마 JSON**(`themes/datasolution.json`, §10.4)은 문서에서 원색(hex)·폰트·치수를 가질 수 있는 **유일한 파일**이다. 렌더러는 테마 밖 색을 쓰지 않는다. 회사 공식 템플릿(.pptx)이 생기면 `docgen.theme_from_pptx`로 추출해 프로젝트 `docs/theme.json`으로 덮는다. 테마 이름 해석 순서: ① 절대·상대 경로 ② 프로젝트 `docs/theme.json` ③ `DOCGEN_THEME_DIR` ④ 플러그인 `themes/`.
- **원본과 결과물 분리**: 커밋하는 것은 `.doc.md`·`.deck.md`·구성도 DSL이다. 렌더링 결과(docx·pptx·png)는 기본으로 `docs/_build/`(`.gitignore`)에 두고, 제출본만 `STYLE.md`의 `filename_pattern`(기본 `{title}_v{version}_{date:%Y%m%d}`)으로 이름 붙여 `--out`으로 뺀다(D11). 바이너리 diff가 저장소를 더럽히지 않고, 같은 원본은 항상 같은 결과를 낸다.
- **서비스 골격**(`skills/fastapi-service/assets/`)과 **`config.example.yaml`**(`skills/llm-gateway/assets/`)은 코드와 게이트웨이의 "우리 것"이다.

### 5.2 ② 룰

- 스킬은 **절차와 판단**만 담는다. 색 값·폰트·회사명 같은 사실은 `STYLE.md`와 테마가 원본이다. 스킬에 복사하지 않는다.
- 모든 문서 스킬은 코드를 쓰기 전에 **문서 리드 1줄**을 선언한다(§8.2). UI 스킬의 "디자인 리드"와 같은 장치다. 모델이 기본값으로 점프하는 것을 막는다.
- 스킬 description은 일부러 길고 구체적이다(ui-skill-set 근거: 발견률 68% → 90%). 한국어 트리거 어휘를 열거한다.
- **한정된 패스**: 다 만들고 → `preflight` 한 번 → 한 번에 고치고 → 끝. 무한 셀프 QA 금지.
- **브리프가 이긴다**: 사용자가 명시한 것은 룰보다 우선. 단 예외는 `STYLE.md` §6 표에 기록.

### 5.3 ③ 하네스

- **PreToolUse `Edit|Write|MultiEdit`** → `doc_lint.py --pre`: 대상이 산문 파일(§7.4)이면 하드 룰 H1~H8, 텍스트 파일이면 H9(시크릿), `.docx/.pptx/.xlsx`면 H10(렌더러 우회). 위반 시 `exit 2` + stderr 수정 안내. 파일에 닿기 전에 막힌다.
- **Stop** → `doc_lint.py --stop`: 변경된 산문 파일에 소프트 룰 S1~S17 + 체크리스트. `{"decision":"block","reason":…}` **한 번만**. `stop_hook_active`면 통과.
- **PostToolUse `Edit|Write`** (`.py`만) → `py_format.py --post`: `ruff check --fix` + `ruff format`. ruff가 없으면 no-op. 고칠 수 없는 오류만 `{"decision":"block"}`.
- 순수 Python 표준 라이브러리, 의존성 0, Python ≥ 3.9 문법. 설치기가 `python`/`python3`/`py -3` 중 동작하는 실행기를 탐지해 `settings.json`에 쓰고, 한글 메시지가 cp949 콘솔에서 깨지지 않게 `-X utf8`을 붙인다(Windows 대응). 훅 파일 머리에 버전 문자열이 있고 `--version`으로 출력한다(`/ai-init --update`가 비교).
- 훅 스크립트는 **프로젝트에 커밋**된다. 플러그인은 설치기와 스킬을 제공할 뿐 강제의 주체가 아니다.

### 5.4 ④ 도구 (MCP)

MCP는 "모델이 직접 하면 틀리거나 위험한 결정적 작업"에만 둔다. 각 서버의 툴은 모두 같은 Python 패키지의 함수를 얇게 감싼 것이고, 같은 함수가 CLI(`python -m docgen …`)로도 노출된다. 스킬은 Bash로 CLI를 부르거나 MCP 툴을 부르거나 둘 다 되며, 어느 쪽이든 결과가 같다.

| 서버 | 이유 | 툴 요약 (§9) |
|---|---|---|
| `docgen` | docx·pptx XML을 모델이 직접 쓰면 깨진다. 테마 강제는 렌더러에서만 가능하다 | `render_docx`, `render_pptx`, `render_diagram`, `diagram_from_compose`, `lint_doc`, `preview`, `docx_to_md`, `pptx_to_md`, `theme_from_pptx`, `layouts`, `theme_export` |
| `litellm-ops` | 게이트웨이 상태·비용·키 조회는 여러 admin API를 조합해야 하고 시크릿 마스킹이 필요하다 | `gateway_health`, `list_models`, `test_completion`, `spend_summary`, `key_info`, `key_create`, `key_block`, `key_unblock`, `team_info`, `team_create`, `config_validate`, `config_diff` |
| GitLab (공식) | 구현 안 함. 설정만 | MR 조회·리뷰·노트, 파이프라인·잡 로그, 파일·커밋, 이슈 |

### 5.5 ui-skill-set 연동

생성형 AI 서비스에는 채팅 UI·관리 화면이 따라온다. 프론트엔드가 있는 프로젝트에서는 `/ai-init --with-ui`가 ui-skill-set의 `install.mjs`를 호출해 같은 팔레트로 UI 규약을 설치한다.

- 테마 JSON의 `primary`(#133F91)·`action`(#1366E3)에서 **`--ui-accent-100…900` 램프**를 생성해 `tokens.css`에 주입한다(`docgen theme export --tokens-css`, §10.4). 웹 UI와 문서·덱이 같은 파랑을 쓴다.
- `brand_hue: blue`로 설치하므로 AI-purple 룰(R2)이 그대로 산다.
- ui-skill-set 경로는 `--ui-skill-set <경로>` 또는 환경변수 `UI_SKILL_SET_ROOT`, 둘 다 없으면 `../ui-skill-set`을 찾고, 없으면 건너뛰고 안내만 한다.

---

## 6. 기능 요구사항

| ID | 요구사항 | 우선순위 | 마일스톤 |
|---|---|---|---|
| FR-1 | `templates/STYLE.md`: frontmatter 스키마(§11.4) + 6섹션 본문. 데이타솔루션 기본값 채워짐 | P0 | M0 |
| FR-2 | `themes/datasolution.json`(§10.4, 부록 A) + `themes/theme.schema.json`(JSON Schema) + 검증 테스트 | P0 | M0 |
| FR-3 | `templates/doc_lint.py --pre`: 하드 룰 H1~H9, exit 2, 수정 안내, 마커·정책 예외, 스킵 목록, 안티 데드락 | P0 | M0 |
| FR-4 | `tests/test_doc_lint.py`: 룰별 양성/음성 케이스, CLI 모드 3종 subprocess 테스트 | P0 | M0 |
| FR-5 | `templates/install.py`: settings.json 병합, Python 실행기 탐지, CLAUDE.md(있으면 AGENTS.md도) 스니펫 멱등 추가, `docs/` 골격 + `.gitignore`에 `docs/_build/`, `.mcp.json` GitLab 항목 병합, `--update`/`--force`/`--with-ui`/`--logo`/`--no-python`/`--uninstall` | P0 | M0 |
| FR-6 | `skills/ai-init/SKILL.md`: 질문 3개 → `install.py` 실행 → 다음 단계 안내 | P0 | M0 |
| FR-7 | `skills/doc-write/SKILL.md` + `references/`(writing-rules-ko, doc-types, korean-format, preflight-doc): Markdown 문서 작성 절차. 렌더링 전 단계까지 | P0 | M0 |
| FR-8 | `templates/CLAUDE.snippet.md`, `templates/settings.json` | P0 | M0 |
| FR-9 | `mcp/docgen`: `.doc.md`/`.deck.md` 파서(§10.1~10.2), frontmatter, 블록 모델 | P0 | M1 |
| FR-10 | `render_docx`(§10.5): 표지·개정이력·목차·머리글/바닥글·쪽번호·제목 스타일·표·코드·그림·캡션·마커 강조, 어절 단위 줄바꿈, **회사 docx 템플릿 모드**(스타일·머리글·여백 유지, 본문 교체) | P0 | M1 |
| FR-11 | `render_pptx`(§10.6): 레이아웃 10종(chart 포함), 헤드 메시지, 바닥글, 발표자 노트, 회사 템플릿 모드 | P0 | M1 |
| FR-12 | 구성도 DSL(§10.3) + 렌더러 3종: mermaid(md), 네이티브 도형(pptx), PNG(docx, Pillow). `timeline`·`chart` 블록 포함(chart는 pptx 네이티브 차트, docx·md는 데이터 표) | P0 | M1 |
| FR-13 | `docgen` MCP 서버 + 동일 기능 CLI(`python -m docgen …`) (§9.2) | P0 | M1 |
| FR-14 | `docgen.lint_doc`가 `templates/doc_lint.py`를 **그대로 import**(단일 구현). 테스트로 드리프트 금지 | P0 | M1 |
| FR-15 | `preview`: LibreOffice(`soffice`) 있으면 PDF→PNG, 없으면 안내 후 건너뜀 | P1 | M1 |
| FR-16 | `docx_to_md`, `pptx_to_md`, `theme_from_pptx`(theme1.xml → 테마 JSON) | P1 | M1 |
| FR-17 | `skills/deck-write/SKILL.md` + `references/`(slide-rules, layouts) | P0 | M1 |
| FR-18 | `doc_lint.py --stop`: 소프트 룰 S1~S18(덱 룰 S9~S12, 용어 통일 S18 포함), 체크리스트, 1회 block. `--all` CI 모드 | P1 | M1 |
| FR-19 | `references/arch-doc-types.md`: 설계서·AS-IS/TO-BE·인터페이스 정의서·구성도 규약(C4 수준 3단계) | P1 | M1 |
| FR-20 | `skills/fastapi-service`: SKILL.md + `assets/`(완전한 예제 서비스, 프롬프트 파일 로더 포함) + `scripts/scaffold.py`(`--with-db/--with-redis/--with-sse/--with-auth/--with-rag/--with-jobs/--with-otel`) + `scripts/route_table.py`(`--openapi`, `--md`) | P0 | M2 |
| FR-21 | `skills/gitlab-ci`: SKILL.md + `assets/`(.gitlab-ci.yml, MR·이슈 템플릿, CODEOWNERS) + `scripts/ci_lint.py` + `references/`(deploy-targets, gitlab-mcp-playbook, pipeline-recipes) | P0 | M2 |
| FR-22 | `skills/py-test`: SKILL.md + `references/`(pytest-conventions, llm-mocking) + `scripts/test_gaps.py` | P0 | M2 |
| FR-23 | `skills/py-review`: SKILL.md + `references/checklist.md` + MR 리뷰 흐름(GitLab MCP) | P0 | M2 |
| FR-24 | `skills/py-refactor`: SKILL.md + `scripts/import_graph.py`(순환·레이어 위반 탐지) | P1 | M2 |
| FR-25 | `templates/py_format.py --post` + 테스트 | P1 | M2 |
| FR-26 | `references/python-conventions.md`(공용: 레이어 규칙, 예외·로깅·설정·비동기 규약) | P0 | M2 |
| FR-27 | `skills/llm-gateway`: SKILL.md + `assets/`(config.example.yaml, compose.yaml, .env.example, client_example.py) + `references/`(azure, bedrock, vertex, vllm, observability, security, ops-runbook) | P0 | M3 |
| FR-28 | `mcp/litellm_ops`: 툴 12종(§9.1, 팀 예산 툴 포함) + `httpx.MockTransport` 테스트 + 쓰기 게이트 | P0 | M3 |
| FR-29 | `skills/model-serving`: SKILL.md + `scripts/vram_estimate.py` + `scripts/bench_llm.py` + `references/`(vllm, quantization, sizing) | P2 | M3 |
| FR-30 | `skills/ai-trend-brief`: SKILL.md + `assets/sources.yaml` + `assets/brief-template.md` | P1 | M3 |
| FR-31 | 플러그인 매니페스트(`.claude-plugin/plugin.json`, `marketplace.json`), `.mcp.json`, `skills/llms.txt`, README(ko), LICENSE(MIT)·NOTICE, `.gitignore` | P1 | M4 |
| FR-32 | `eval/`: 골든 프롬프트 8개 + `eval/check_output.py`(테마 밖 색 스캔, 덱 룰, `doc_lint --all`) + 기준선 기록 | P1 | M4 |
| FR-33 | ui-skill-set 연동: `docgen theme export --tokens-css`, `install.py --with-ui` | P2 | M4 |
| FR-34 | 저장소 CI(GitHub Actions, ubuntu + windows): `uv run pytest`, `doc_lint.py --all docs/`, 렌더러 소스 hex 리터럴 0 검사 | P1 | M4 |
| FR-35 | `references/genai-patterns.md`(§8.12): RAG 파이프라인, 프롬프트 파일 관리·버전, 구조화 출력·툴 호출, 비동기 작업(202+폴링), 가드레일, 평가 기초. `fastapi-service`의 `--with-rag`(pgvector `/ingest`·`/ask`)와 `--with-jobs` 모듈이 이 문서를 구현한다 | P0 | M2 |
| FR-36 | `docgen.diagram_from_compose(compose.yaml)`: 서비스·의존(`depends_on`)·포트·이미지에서 구성도 DSL 초안 생성(현행 구성도 자동화) | P2 | M1 |
| FR-37 | 저장소 루트 `CLAUDE.md`(구현자 규약, §11.9)와 `docs/research/`(사실 확인 출처). PRD 작성 시점에 이미 존재하며 Opus는 유지·갱신만 한다 | P0 | M0 |
| FR-38 | 부록 E 추적표를 `docs/traceability.md`로 옮겨 마일스톤마다 "테스트·골든 결과" 열을 갱신 | P1 | M0~M4 |

---

## 7. 룰셋 (doc_lint)

룰은 두 종류다. **하드**(PreToolUse, 편집 차단)는 객관적이고 고치는 법이 하나인 것만. **소프트**(Stop, 1회 지적)는 정규식으로 잡히지만 맥락에 따라 정당할 수 있는 것. 모든 패턴은 Python `re` 문법이며 별도 표기 없으면 플래그 없음. 정규식은 초안이고 Opus는 테스트 케이스(§12.1)가 통과하도록 다듬는다. 룰 이름은 안정적 ID이며 테스트와 마커가 이 ID를 쓴다.

### 7.1 하드 룰 (PreToolUse, exit 2)

| ID | 이름 | 패턴 (초안) | 예외 | 메시지 요지 (→ 고치는 법) |
|---|---|---|---|---|
| **H1** | `dash` | `[—–]` (em/en dash) | `STYLE.md` `dash_policy: allow` | "em-dash는 AI 문체의 첫 번째 신호. 범위는 `~`, 구분은 `,`·`·`·괄호·줄바꿈으로" |
| **H2** | `buzzword-ko` | `혁신적\|차세대\|획기적\|최첨단\|패러다임\|게임\s?체인저\|시너지\|극대화\|최적의\s?(?:솔루션\|방안\|선택)\|경쟁력을?\s?(?:강화\|확보)\|효율성을?\s?(?:극대화\|제고\|향상)\|생산성을?\s?향상\|다양한\s?활용이\s?가능\|안정적인\s?운영이\s?가능\|확장성이\s?우수\|지속적인\s?고도화가\s?가능\|전반적으로\s?우수한\s?것으로` | `buzzword_policy: warn`(차단 대신 경고) · `allow_terms`에 포함된 어구 | "상투어. 무엇이 구체적으로 가능해지는지로 바꾼다: 대상 + 현재 한계 + 도입 후 가능한 작업 (review-report-writer 좋은 예 참조)" |
| **H3** | `buzzword-en` | `\b(?:seamless(?:ly)?\|leverag(?:e\|es\|ed\|ing)\|cutting[- ]edge\|state[- ]of[- ]the[- ]art\|game[- ]?chang(?:er\|ing)\|delve(?:s\|d)?\|tapestry\|unleash(?:es\|ed\|ing)?\|supercharg\w*\|next[- ]gen(?:eration)?\|best[- ]in[- ]class\|revolutioni[sz]\w*\|synerg\w*\|paradigm)\b` (re.I) | 위와 같음 | "영어 상투어. 구체 동사·명사로" |
| **H4** | `ai-phrase-ko` | `알아보(?:겠\|도록 하겠)습니다\|살펴보(?:겠\|도록 하겠)습니다\|하는 것이 (?:매우 \|무엇보다 )?중요합니다\|주목할 만한 점은\|다음과 같은 (?:이점\|장점\|특징)이 있습니다` | 없음 | "블로그 문체. 보고서는 결론을 먼저 단정문으로 쓴다" |
| **H5** | `ai-phrase-en` | `\b(?:in conclusion\|it(?:'s\| is) (?:important\|worth) (?:to note\|noting)\|let'?s (?:dive\|explore\|delve)\|in today'?s (?:fast-paced\|rapidly\|ever)\|as an ai\|i hope this helps\|great question\|certainly!\|in summary,\|to summarize,)` (re.I) | 없음 | "ChatGPT 관용구. 삭제하거나 내용으로 대체" |
| **H6** | `emoji` | `[\U0001F1E6-\U0001F1FF\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF\U0001FA70-\U0001FAFF☀-➿⭐⭕]️?` **단, 한국 기업 문서의 관용 기호는 제외**: `★☆`(U+2605~2606) `☞☜`(U+261C~261E) `☐☑☒`(U+2610~2612) `✓✔`(U+2713~2714) `※`(U+203B, 범위 밖) `○●◎◇◆□■△▲▽▼`(U+25xx, 범위 밖) `→←↔`(U+21xx, 범위 밖). 구현은 "범위 매치 후 허용 집합 제외" | `emoji_policy: allow` | "기업 문서에 이모지 없음. 제목은 텍스트로, 상태는 `완료/진행/보류` 같은 단어로. 강조 기호는 ※·★·☞처럼 관용 기호만" |
| **H7** | `exclaim` | `(?<=[가-힣A-Za-z0-9)\]"'”’])!(?![\[=(])` (줄 시작이 `!`인 이미지 문법과 `> [!NOTE]`는 제외) | `exclaim_policy: allow` | "느낌표 없음. 마침표로" |
| **H8** | `placeholder` | `lorem ipsum\|홍길동\|john doe\|\bTBD\b\|\bTODO\b\|\[(?:insert\|여기에\|내용 입력)[^\]]*\]\|\bXXX+\b` (re.I) | 없음. 빈 자리는 `STYLE.md`의 `placeholder_marker`(기본 `[확인 필요]`)로 | "가짜 채움 금지. 모르는 값은 `[확인 필요]`·`[금액 입력 필요]`·`[일정 확인 필요]`로 표시하고 계속 쓴다" |
| **H9** | `secret` | `sk-[A-Za-z0-9_-]{20,}\|AKIA[0-9A-Z]{16}\|-----BEGIN (?:RSA \|EC \|OPENSSH )?PRIVATE KEY\|ghp_[A-Za-z0-9]{30,}\|glpat-[A-Za-z0-9_-]{20,}\|xox[bp]-[A-Za-z0-9-]{20,}\|AIza[0-9A-Za-z_-]{35}` **자리표시자 제외**: 매치 문자열에 같은 문자 6개 이상 연속(`xxxxxx`)·`example`·`your[_-]`·`placeholder`·`<…>`·`changeme`가 있으면 시크릿이 아님 | **없음. 마커로도 못 푼다.** 적용 범위는 §7.4의 텍스트 파일 전체(코드·yaml·env 포함) | "시크릿 인라인 금지. `os.environ/NAME` 또는 `${NAME}` 참조로, 값은 `.env`(git 제외)에" |
| **H10** | `office-binary` | 대상 파일 확장자가 `.docx .pptx .xlsx .pdf`인 Write/Edit 자체 | 없음 | "Office 파일은 직접 쓰지 않는다. `.doc.md`/`.deck.md`를 고치고 `docgen`으로 렌더링" |

H1·H6·H7은 "AI 티"의 80%를 잡는다(ui-skill-set의 R1/R2에 해당). H2~H5는 문장 단위 상투어. H8은 review-report-writer의 "확인되지 않은 내용을 사실처럼 쓰지 않는다"를 기계화한 것. H9는 문서 스킬이 게이트웨이 설정을 다루기 때문에 필요한 안전 레일이다. H10은 "렌더러 우회 금지"를 프롬프트가 아니라 훅으로 강제한다(모델이 python-docx를 직접 호출하거나 바이너리를 쓰려는 순간 막힌다).

### 7.2 소프트 룰 (Stop, 1회 block)

메시지에 "정당하면 `<!-- doc-lint-allow <id>: <이유> -->`를 남기고 통과"를 포함한다. 파일당 룰당 1건으로 합쳐 보고한다(건수 표기).

| ID | 이름 | 판정 (초안) | 메시지 요지 |
|---|---|---|---|
| S1 | `rule-of-three` | 파일의 목록(연속 `- `/`* `/`1. ` 줄 묶음)이 3개 이상이고 그중 80% 이상이 정확히 3항목 | "항목이 늘 3개면 기계 티. 실제 개수대로. 2개면 2개, 5개면 5개" |
| S2 | `bold-label` | `^\s*(?:[-*+]\|\d+[.)])\s+\*\*[^*\n]{1,30}\*\*\s*[:：]` 4회 이상 | "굵은 라벨+콜론 목록은 ChatGPT 서식. 문장으로 풀거나 표로" |
| S3 | `closer` | `^\s*(?:결론적으로\|요약하자면\|종합하자면\|마무리하자면\|정리하자면\|In summary\|To summarize\|Overall,)` | "요약 문단은 앞 내용을 반복한다. 삭제하거나 '종합 검토 의견'처럼 새 판단만 남긴다" |
| S4 | `vague-adverb` | `다양한\|효과적으로\|체계적으로\|적극적으로\|원활하게\|안정적으로\|지속적으로\|효율적으로` 파일 합계 3회 이상 | "대상·수치 없는 부사. '무엇을·얼마나'로" |
| S5 | `can-stack` | `할 수 (?:있습니다\|있다)\.` 문장 종결 5회 이상 | "'할 수 있다'가 반복되면 가능성만 나열한 것. 실제로 하는 것·한 것으로" |
| S6 | `same-starter` | 같은 섹션(제목 사이)에서 `또한\|그리고\|이를 통해\|따라서\|한편\|먼저\|마지막으로\|Additionally\|Furthermore\|Moreover` 중 하나가 문장 시작에 3회 이상 | "접속사 반복. 문장을 합치거나 순서를 바꾼다" |
| S7 | `colon-leadin` | `다음과 같(?:습니다\|다)[:：]?\s*$` 3회 이상 | "'다음과 같습니다:' 반복. 바로 목록·표로 들어간다" |
| S8 | `generic-heading-en` | `^#{1,6}\s*(?:Introduction\|Overview\|Conclusion\|Summary\|Key (?:Takeaways\|Points)\|Final Thoughts)\s*$` (re.I) | "영어 문서의 빈 제목. 주장이 담긴 제목으로" (한국어 `개요/배경`은 관례라 대상 아님) |
| S9 | `deck-long-bullet` | `.deck.md`에서 글머리표 텍스트가 한글 포함 40자 초과, 라틴만 70자 초과 | "슬라이드 글머리표는 한 줄. 40자 안에서 명사형으로" |
| S10 | `deck-many-bullets` | `.deck.md` 슬라이드당 글머리표 7개 이상 | "6개 넘으면 두 장으로 나누거나 표로" |
| S11 | `deck-headline` | `.deck.md` 슬라이드에 `##`가 없거나 2개 이상, 또는 60자 초과 | "슬라이드마다 헤드 메시지(주장 문장) 정확히 1개, 60자 이내" |
| S12 | `deck-sentence` | `tone_deck: 개조식`일 때 `.deck.md` 글머리표가 `다\.\|니다\.\|요\.`로 끝남 | "덱은 개조식. '~구축', '~필요', '~예정'처럼 명사형 종결, 마침표 없음" |
| S13 | `unsourced-number` | frontmatter `doc_type`이 `브리프`·`검토보고서`일 때 `\d+(?:\.\d+)?\s?%`가 있는 문단에 `http\|출처\|source\|\[\d+\]` 없음 | "수치에는 출처. 사실/추론 구분" |
| S14 | `perfect-number` | `\b(?:99\.9+\|100)\s?%` 또는 `100%\s?(?:달성\|보장\|해결)` | "완벽한 숫자는 근거 없는 확정. 실측치나 범위로" |
| S15 | `over-gloss` | `[가-힣]+\s?\([A-Za-z][A-Za-z0-9 ./-]{1,40}\)` 파일 10회 이상 | "영문 병기는 첫 등장 1회만" |
| S16 | `honorific-mix` | 산문 문단(표·목록·덱 제외)에서 `(?:습니다\|입니다)\.` 종결과 그 외 `[가-힣]다\.` 종결이 각각 3회 이상 공존 | "존댓말/평서문 섞임. `STYLE.md tone_doc`대로 하나로" |
| S17 | `date-mix` | `\d{4}\.\s?\d{1,2}\.\s?\d{1,2}\.?`와 `\d{4}-\d{2}-\d{2}`가 한 파일에 공존 | "날짜 표기 하나로 (`STYLE.md date_format`)" |
| S18 | `glossary-term` | `STYLE.md glossary`가 가리키는 `docs/glossary.md`의 표(`\| 표준 표기 \| 금지 표기 \| 비고 \|`)에서 "금지 표기" 열의 어구가 산문에 등장 (예: `쿠버네티스`→`Kubernetes`, `라마`→`Llama`, `챗GPT`→`ChatGPT`) | "용어는 용어집 표기로: `<금지>` → `<표준>`" |

### 7.3 체크리스트 (Stop 메시지에 첨부, 정규식 불가 항목)

- 결론(권고안)이 문서 첫 화면 안에 있는가. 검토 개요 3~5줄만 읽어도 맥락이 잡히는가
- 사실 · 추론 · 권고가 표현으로 구분되는가 (`~이다` / `~로 예상된다` / `~하는 것이 적절하다`)
- 선택하지 않은 대안이 왜 밀렸는지 한 줄이라도 있는가. 장점만 나열하지 않았는가
- 모든 수치·모델명·금액·일정이 입력 자료와 같은가. 만든 숫자는 없는가
- 제목이 주장인가 (덱). "게이트웨이 선정"이 아니라 "LiteLLM이 운영 부담 대비 기능이 가장 넓다"
- 문단 길이가 제각각인가 (전부 3문장이면 기계 티). 마지막 문단이 앞 내용을 반복하지 않는가
- 한 화면(덱 1장 / 문서 1절)에 새 정보가 있는가. 없으면 삭제
- 표의 마지막 열이 "검토 의견"(판단)인가, 값 나열로 끝나지 않았는가
- `[확인 필요]` 항목이 "추가 확인사항" 절에 모여 있는가
- 회사 색·폰트만 썼는가 (렌더링 결과는 `eval/check_output.py`가 확인)

### 7.4 적용 범위

- **산문 파일**(H1~H8, S1~S18): `*.md` `*.markdown` `*.mdx` `*.txt` `*.rst` `*.adoc`, 그리고 `*.doc.md` `*.deck.md`. 덱 룰 S9~S12는 `*.deck.md`만.
- **텍스트 파일 전체**(H9만): 위 + `*.py *.js *.ts *.json *.yaml *.yml *.toml *.cfg *.ini *.env *.env.*`.
- **Office 바이너리**(H10만): `*.docx *.pptx *.xlsx *.pdf`에 대한 Write/Edit.
- **항상 스킵**: `node_modules/` `.git/` `.venv/` `venv/` `dist/` `build/` `site-packages/` `docs/_build/` `.claude/`(훅·스킬 자신) `CHANGELOG*` `LICENSE*` `NOTICE*` lock 파일, 256KB 초과 파일. **정책 파일도 스킵**(설정이자 규칙 목록이므로): `STYLE.md` `CLAUDE.md` `AGENTS.md` `docs/glossary.md`. H9는 이들도 검사한다.
- **줄 단위 스킵**: 펜스 코드 블록(```` ``` ```` / `~~~`) 내부, 인라인 코드(`` ` ``) 내부, HTML 주석, YAML frontmatter, URL(`https?://\S+`), 링크 대상(`](…)`). H9는 이 스킵을 적용하지 않는다(코드 블록 안의 키도 잡는다).
- frontmatter `doc_lint: off`인 파일은 H9만 검사한다 (이 PRD, 룰 참조 문서, 금지어 사전이 그 예).
- `--pre`는 `tool_input.content`(Write) 또는 `new_string`(Edit) 또는 `edits[].new_string`(MultiEdit)만 본다. 기존 파일 내용의 마커는 예외 판단에 쓴다(ui-skill-set과 동일).

### 7.5 예외 메커니즘

- 파일 마커: `<!-- doc-lint-allow <rule-id>: <이유> -->`. **이유 필수**(콜론 뒤 공백 아닌 문자 1개 이상). 파일 단위로 해당 룰을 끈다. 여러 룰은 마커 여러 개.
- `STYLE.md` frontmatter 정책: `dash_policy` `emoji_policy` `exclaim_policy` `buzzword_policy` `allow_terms`.
- `STYLE.md` §6 "허용 예외" 표에 기록. 스킬은 예외를 추가하기 전에 사용자에게 1줄로 묻는다.
- 안티 데드락: 같은 파일·같은 룰 조합으로 3회 연속 차단되면 4번째는 `systemMessage` 경고와 함께 통과. 상태는 `tempfile.gettempdir()/doc-lint-<프로젝트 해시>.json`.
- H9(`secret`)는 어떤 방법으로도 풀리지 않는다.

### 7.6 py_format (PostToolUse, `.py`)

| 항목 | 규격 |
|---|---|
| 트리거 | `PostToolUse`, matcher `Edit\|Write\|MultiEdit`, `tool_input.file_path`가 `.py`이고 프로젝트 안이며 존재할 때만 |
| ruff 탐지 | ① `pyproject.toml`/`uv.lock`에 `ruff` 문자열이 있고 `uv`가 있으면 `uv run ruff` ② PATH의 `ruff` ③ 없으면 조용히 `exit 0` |
| 동작 | `ruff check --fix --quiet <file>` → `ruff format --quiet <file>`. 각 30초 타임아웃 |
| 출력 | 남은 오류가 있으면 stdout `{"decision":"block","reason":"[py-format] ruff 미해결 N건:\n<E501 …>\n→ 규칙을 지켜 고치거나 `# noqa: <코드>`에 이유를 단다"}`. 없으면 출력 없음 |
| 실패 | 어떤 내부 오류도 `exit 0`. 세션을 깨지 않는다 |
| 제외 | `migrations/`, `*_pb2.py`, 512KB 초과 |

---

## 8. 스킬 명세

공통 규칙:
- SKILL.md 본문 ≤ 200줄. 사실(색·폰트·회사명·토큰)은 복사하지 않고 `STYLE.md`·테마·references를 가리킨다.
- description은 한국어 트리거 어휘를 열거하고 "~에는 쓰지 않는다"로 경계를 긋는다. 첫 1,536자가 목록에 노출되므로 앞부분에 핵심 트리거를 둔다.
- 스크립트는 전부 `python <스킬경로>/scripts/<이름>.py` 형태이며 `--help`가 있다. 플러그인 설치 시 경로는 `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/…`, 클론 시 저장소 상대 경로. SKILL.md는 두 경우를 모두 적는다(ui-init 방식).
- 문서·덱을 만드는 스킬은 파일을 **Edit/Write 도구로** 쓴다. Bash 리다이렉트로 쓰면 훅을 우회하므로 금지.
- 모든 스킬은 끝에 "하지 않는 것" 절을 둔다.

### 8.1 `ai-init` (설치)

```yaml
---
name: ai-init
description: >
  ai-work-skill을 현재 프로젝트에 설치한다. STYLE.md(문서 계약)·doc_lint 훅·py_format 훅·CLAUDE 규약·docs 골격·
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
```

절차: ① `STYLE.md`가 이미 있으면 `--update` 여부 확인, 없으면 신규. `--uninstall`이면 훅 파일·settings 항목·CLAUDE 스니펫만 제거하고 `STYLE.md`·`docs/`는 남긴다 ② 질문 최대 3개를 한 번에: 조직 표기(기본 `데이타솔루션`), 문서 톤(`서술식`(~다) 기본 / `경어`(~습니다)), 회사 공식 템플릿(pptx·docx) 파일이 있는지(있으면 경로). Python 프로젝트 여부는 `pyproject.toml` 존재로 자동 판단 ③ `install.py` 실행(§11.6 계약). 템플릿 경로를 받았으면 이어서 `python -m docgen theme-from-pptx <경로> --name company --out-dir docs`를 실행해 `docs/theme.json`을 만들고 `STYLE.md`의 `theme`·`template_pptx`를 채운다(docgen 환경이 없으면 명령만 안내) ④ 설치기 출력의 "다음 단계"를 전달하고 `python .claude/hooks/doc_lint.py --all docs/`로 확인. 로고는 `--logo`로 받은 파일을 `docs/assets/logo.png`로 복사만 한다(저장소에 로고를 넣지 않는 이유를 한 줄 안내). `AGENTS.md`가 있으면(Codex 병행 팀) 같은 스니펫을 거기에도 넣는다.

### 8.2 `doc-write` (문서: md → docx)

```yaml
---
name: doc-write
description: >
  기업·연구개발 조직의 문서를 한국 기업 문서체로 쓴다. 아키텍처 설계서, 기술 검토서, 검토보고서, 개발 가이드,
  온보딩 가이드, 운영 런북, ADR(설계 결정 기록), 인터페이스 정의서, 회의록, 기술 브리프, README, 교육 자료.
  "설계서 써줘", "문서 만들어줘", "가이드 작성", "런북", "ADR", "검토보고서", "docx로", "워드로", "보고서 초안",
  "AS-IS/TO-BE", "구성도 포함 문서" 요청에 반드시 쓴다. STYLE.md와 테마만 따르고 AI 문체(상투어·em-dash·이모지·
  굵은 라벨 목록)를 피한다. 결과는 Markdown(.doc.md)이며 docx가 필요하면 docgen으로 렌더링한다.
  기존 문서의 수정, 동료 문서에 대한 리뷰 의견, 경영진용 1쪽 요약, 검토 의견에 대한 답변도 이 스킬이 한다.
  슬라이드·덱은 deck-write, 주간보고 xlsx는 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[문서 유형과 주제 | 수정할 파일 | 리뷰할 파일]"
allowed-tools:
  - Bash(python .claude/hooks/doc_lint.py *)
  - Bash(uv run --project * python -m docgen *)
  - Bash(python -m docgen *)
  - mcp__docgen
---
```

본문 순서:
0. **모드 판정**(한 줄): `신규` / `수정`(기존 `.doc.md` 또는 docx→`docx_to_md`로 읽은 뒤 바뀐 부분만 다시 쓴다, 원본 구조 유지) / `리뷰 의견`(동료 문서를 §7.3 체크리스트와 `writing-rules-ko.md`로 읽고 `수정 필요 / 확인 필요 / 개선 제안` 순으로 파일:절 참조와 함께 보고. 문서를 직접 고치지 않는다) / `요약`(1쪽: 배경·핵심 문제·비교 결과·위험·권고) / `질의 답변`(직접 답 → 근거 → 대응 계획 → 남은 위험). 이하 절차는 `신규`·`수정` 기준.
1. **읽기**: `STYLE.md` 전체(없으면 `/ai-init` 안내 후 중단). `docs/glossary.md`가 있으면 용어. 같은 유형의 기존 문서가 `docs/`에 있으면 하나 열어 구조를 기준으로 삼는다(새로 발명하지 않는다). `template_docx`가 있으면 렌더링 시 그 양식을 쓴다는 것을 리드에 적는다.
2. **문서 리드 1줄**(코드·본문 전, 정확히 한 줄): `문서: <제목> · 유형 <설계서|검토보고서|가이드|런북|ADR|정의서|회의록|브리프|README|교육> · 독자 <결재권자|개발자|고객|혼합> · 톤 <서술식|경어> · 분량 <n쪽>`. 브리프가 두 갈래면 질문 **하나**만. 정보가 부족해도 초안을 먼저 쓰고 빈 곳은 `[확인 필요]`로 표시한다(질문 최대 3개, review-report-writer 원칙).
3. **골격**: `references/doc-types.md`의 유형별 골격을 가져와 내용 없는 절은 **통합·삭제**한다. 항상 남는 절: 개요(결론 포함), 본문, 권고/결정, 추가 확인사항.
4. **쓰기** 직전에 `references/writing-rules-ko.md`를 로드한다(계획 단계에서는 로드하지 않는다). 아키텍처 문서면 `../../references/arch-doc-types.md`도. 규칙 요약: 결론 먼저 · 사실/추론/권고 구분 · 수치에 출처 · 문단 길이 변화 · 접속사 남발 금지 · 마지막 요약 금지 · 비교표 마지막 열은 "검토 의견" · 모르는 값은 마커. 구성도는 ` ```diagram ` 블록(§10.3)으로 쓴다. 그림을 말로 설명하지 않는다.
5. **파일**: `docs/<영역>/<제목>.doc.md`. frontmatter(§10.1) 채움. `date`는 오늘, `version` 0.1, `history` 1행.
6. **렌더링**(요청 시): `python -m docgen render-docx <파일>`(기본 출력 `docs/_build/<filename_pattern>.docx`, 제출본은 `--out <경로>`, 회사 양식은 `--template <docx>` 또는 `STYLE.md template_docx`) → `preview`가 되면 첫 3쪽 PNG를 보고 표·그림 잘림만 확인(한 번). 렌더 오류는 DSL 위반이므로 `.doc.md`를 고친다. python-docx를 직접 호출하지 않는다(H10이 막는다). 인터페이스 정의서라면 `route_table.py --md`의 표를 그대로 붙인다(손으로 옮겨 쓰지 않는다).
7. **점검**: `references/preflight-doc.md` 한 번 → 한 번에 고침 → 끝. 세 번째 패스 없음. 종료 시 `doc_lint --stop`이 소프트 룰을 본다.
8. **브리프가 이긴다**: 사용자가 특정 표현·이모지·구조를 명시하면 우선. 하드 룰에 걸리면 먼저 1줄 확인 → 승인 시 마커 + `STYLE.md` §6 기록.

references: `writing-rules-ko.md`(문체·표현·비교표, review-report-writer 규칙을 흡수·확장), `doc-types.md`(유형 10종 골격과 통합 조합, 결론 7항목), `korean-format.md`(번호 체계, 날짜·단위·통화·용어 병기, 표·그림 캡션 `[표 1]`·`[그림 1]`, 개조식/서술식 정의), `preflight-doc.md`(§7.3 체크리스트 + 유형별 추가 항목).

하지 않는 것: 회사명·고객명·금액을 지어내기 · 출처 없는 수치 · 한 문서에 톤 섞기 · 렌더러 우회(python-docx 직접 호출) · Bash 리다이렉트로 문서 쓰기.

### 8.3 `deck-write` (덱: md → pptx)

```yaml
---
name: deck-write
description: >
  경영진 보고·기술 공유·제안·교육용 슬라이드를 만든다. "덱 만들어줘", "PPT", "pptx", "발표자료", "장표",
  "보고용 슬라이드", "10장으로 요약", "아키텍처 발표", "교육 자료 슬라이드", "설계서를 덱으로" 요청에 반드시 쓴다.
  슬라이드마다 헤드 메시지 1개, 개조식, 회사 테마(또는 회사 템플릿 pptx)만 쓰며 구성도는 편집 가능한 도형으로
  넣는다. 결과는 .deck.md이고 docgen이 pptx로 렌더링한다. 설계서(.doc.md)를 입력으로 받아 덱으로 바꾸는 것도 한다.
  문서(docx)는 doc-write가 담당한다.
version: 0.1.0
user-invocable: true
argument-hint: "[덱 목적·독자·장수 | 원본 .doc.md 경로]"
allowed-tools:
  - Bash(python .claude/hooks/doc_lint.py *)
  - Bash(uv run --project * python -m docgen *)
  - Bash(python -m docgen *)
  - mcp__docgen
---
```

본문 순서:
1. 읽기: `STYLE.md`, 테마 이름, `template_pptx`(회사 템플릿 경로, 있으면 그 레이아웃 이름을 `python -m docgen layouts <pptx>`로 확인). 입력이 `.doc.md`면 그 문서의 개요(결론)·비교표·구성도·권고안을 스토리라인의 재료로 뽑는다(내용을 새로 만들지 않는다).
2. **덱 리드 1줄**: `덱: <제목> · 목적 <보고|제안|공유|교육> · 독자 <경영진|개발팀|고객> · 장수 <n> · 결론 <한 문장>`. 결론 문장이 덱의 마지막 슬라이드 헤드 메시지가 된다.
3. **스토리라인 먼저**: 슬라이드 제목(`#`)과 헤드 메시지(`##`)만 n장 나열해 사용자에게 보인다(한 번). 흐름: 배경·문제 → 목표 → 대안/아키텍처 → 비교·근거 → 계획·일정 → 위험 → 결론·요청 사항. 교육용은 목표 → 개념 → 실습 단계 → 정리.
4. 쓰기 직전에 `references/slide-rules.md` 로드. 규칙: 헤드 메시지는 **주장 문장**(≤ 60자, "게이트웨이 선정"이 아니라 "LiteLLM이 운영 부담 대비 기능이 가장 넓다") · 본문 ≤ 6줄, 줄당 ≤ 40자, 명사형 종결 · 슬라이드당 그림 1개 또는 표 1개 · 같은 크기 카드 3개 나열 금지 · 아이콘 없음(테마에 없다) · 출처는 바닥글 · 첫 장에 결론 요약, 마지막 장에 요청 사항(결정·예산·일정) · 애니메이션·전환 없음.
5. 레이아웃 선택은 `references/layouts.md`(§10.6의 10종) 기준. 구성도는 ` ```diagram `, 일정은 ` ```timeline `, 수치 비교(비용·처리량·사용량)는 ` ```chart `(§10.3, pptx 네이티브 차트라 발표 중 수정 가능), 정성 비교는 표. 차트 하나에 시리즈 ≤ 4, 값에는 단위와 출처.
6. 파일 `docs/deck/<제목>.deck.md` → `python -m docgen render-pptx <파일> --out <제목>.pptx [--template <회사.pptx>]` → `preview`로 전 장 썸네일 1회 확인(넘침·겹침만). 오류는 `.deck.md`를 고친다.
7. 점검: `slide-rules.md`의 체크 8개 한 번 → 끝. 발표자 노트(`<!-- note: -->`)에 말할 내용을 2~3문장 넣는다(경영진 덱만).

하지 않는 것: 글머리표 벽 · 제목만 있는 슬라이드 · "감사합니다" 단독 장(마무리 장은 요청 사항 + 연락처) · 그라데이션·그림자·클립아트 · python-pptx 직접 호출.

### 8.4 `fastapi-service` (서비스 골격)

```yaml
---
name: fastapi-service
description: >
  FastAPI 기반 생성형 AI 서비스의 프로젝트 골격을 만들거나 기존 서비스를 표준 구조로 맞춘다. "서비스 골격",
  "FastAPI 프로젝트 생성", "API 서버 만들어줘", "요약/챗/RAG API", "LLM 호출 서비스", "개발 환경 구축",
  "Dockerfile·compose", "설정·로깅 표준", "SSE 스트리밍 엔드포인트", "헬스체크" 요청에 반드시 쓴다.
  LLM 호출은 LiteLLM 게이트웨이 경유만 허용하고, 설정은 환경변수, 테스트·Docker·CI를 함께 만든다.
  프론트엔드·데이터 파이프라인·모델 학습 코드는 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[서비스 이름과 기능 한 줄]"
allowed-tools:
  - Bash(python */skills/fastapi-service/scripts/*.py *)
  - Bash(uv *)
  - Bash(docker build *)
---
```

절차: ① 기존 프로젝트면 구조 진단(`route_table.py`로 라우트·의존성 덤프)만 먼저 하고 바꿀 것을 표로 제안 ② 신규면 **서비스 리드 1줄**: `서비스: <이름> · 기능 <한 줄> · 패턴 <채팅|요약|RAG|에이전트|배치> · 외부 의존 <LLM 게이트웨이|DB|Redis|없음> · 배포 <컨테이너> · 인증 <없음|API 키|SSO>` ③ `scaffold.py --name <pkg> [--with-db] [--with-redis] [--with-sse] [--with-auth] [--with-rag] [--with-jobs] [--with-otel]` 실행 → 생성 트리 표시 ④ `../../references/python-conventions.md`와, 패턴이 RAG·에이전트·비동기면 `../../references/genai-patterns.md`를 로드해 기능 코드 작성. 프롬프트는 코드에 인라인하지 않고 `{{pkg}}/prompts/*.md`에 둔다 ⑤ `uv sync && uv run pytest` → `docker build` → `gitlab-ci` 스킬로 CI 추가(사용자가 원치 않으면 생략) ⑥ README에 실행법 4줄.

`assets/service/` (완전한 예제, 그대로 실행 가능):
```
{{pkg}}/
  main.py               create_app(), lifespan(게이트웨이 클라이언트·DB 풀 생성/종료), 라우터 등록, 미들웨어
  core/config.py        Settings(BaseSettings, env_prefix=APP_, .env 지원): app_name, env, log_level, llm_base_url, llm_api_key(SecretStr), llm_default_model, request_timeout_s=30, cors_origins
  core/logging.py       JSON 로그(stdlib logging + 커스텀 Formatter), request_id contextvar, 프롬프트/응답 본문은 DEBUG에서만·PII 마스킹 훅
  core/errors.py        AppError(code, status, detail) → RFC 9457 problem+json 핸들러, 422 통일, 예기치 못한 예외는 500 + request_id
  core/middleware.py    X-Request-ID 발급/전파, 처리 시간 헤더
  api/router.py         /api/v1 프리픽스, 태그
  api/v1/health.py      GET /healthz(항상 200), GET /readyz(게이트웨이·DB 핑)
  api/v1/chat.py        POST /chat(동기), POST /chat/stream(SSE, text/event-stream, event: delta|done|error)
  services/llm.py       LLMClient: httpx.AsyncClient(base_url=게이트웨이, timeout, 재시도 2회 지수 백오프, 429/5xx만), chat(), stream(), embed(), usage·비용 헤더(x-litellm-response-cost) 파싱, 요청마다 user(호출 주체)·metadata.tags(서비스명·환경)·request_id를 게이트웨이에 전달(비용 귀속·추적), 구조화 출력(response_format json_schema) 헬퍼
  services/prompts.py   prompts/*.md 로더: frontmatter(name, version, model_hint, variables) + 본문 템플릿(string.Template `$var`), 시작 시 전부 로드·검증(누락 변수는 기동 실패), 렌더 결과는 골든 테스트 대상
  prompts/summarize.md  예시 프롬프트 1개(버전 1)
  core/security.py (옵션 --with-auth)   X-API-Key 헤더 의존성(키 목록은 env, 상수 시간 비교), 실패 401 problem+json. SSO/JWT는 references 안내
  api/v1/jobs.py + services/jobs.py (옵션 --with-jobs)   장기 작업: POST → 202 + job_id, GET /jobs/{id} 상태(queued|running|done|failed)·결과. 인프로세스 asyncio 큐(# ponytail: 단일 프로세스, 다중 워커면 Redis 큐/Arq로)
  api/v1/rag.py + services/rag.py + infra/vector.py (옵션 --with-rag, --with-db 포함)   POST /ingest(파일·텍스트 → 청크 → 게이트웨이 /embeddings → pgvector), POST /ask(검색 k개 → 프롬프트 조립 → 인용 포함 응답). 청크 크기·k·유사도 임계는 Settings
  core/telemetry.py (옵션 --with-otel)   OpenTelemetry FastAPI·httpx 계측, OTLP 엔드포인트 env, 트레이스 id를 로그와 게이트웨이 metadata에 전파
  schemas/chat.py       pydantic v2 요청/응답 모델, 예시 포함(OpenAPI)
  infra/db.py (옵션)    SQLAlchemy 2 async 엔진, 세션 의존성, alembic 초기 마이그레이션 1개
  infra/cache.py (옵션) redis.asyncio 클라이언트
tests/
  conftest.py           app 픽스처, `respx` 게이트웨이 모킹 픽스처, anyio backend=asyncio
  test_health.py, test_chat.py, test_chat_stream.py, test_llm_client.py(재시도·타임아웃)
pyproject.toml          [project] deps: fastapi, uvicorn[standard], pydantic-settings, httpx; [dependency-groups] dev: pytest, pytest-cov, anyio, respx, ruff, mypy 또는 pyright; [tool.ruff] line-length 100, select E,F,I,B,UP,ASYNC; [tool.pytest.ini_options] addopts "-q --strict-markers", markers deterministic/live_llm; [tool.ai-work] layers = ["api","services","infra"]
Dockerfile              multi-stage(uv → runtime python:3.12-slim), non-root, HEALTHCHECK /healthz, CMD uvicorn --workers 2
compose.yaml            app, litellm(config 마운트), postgres(옵션), redis(옵션), langfuse(옵션, 프로파일)
.env.example            APP_* 전부, 값은 플레이스홀더
.pre-commit-config.yaml ruff, ruff-format, end-of-file-fixer
README.md               실행·테스트·빌드 4줄
```

`scripts/scaffold.py --name <pkg> --target <dir> [--with-db] [--with-redis] [--with-sse] [--with-auth] [--with-rag] [--with-jobs] [--with-otel] [--force]`: `assets/service/`를 복사하며 `{{pkg}}`·`{{PKG}}`·`{{service_title}}`를 치환하고 옵션에 없는 모듈·compose 서비스·의존성·테스트를 제거한다(옵션 모듈 파일은 `# scaffold: with-rag` 첫 줄 주석으로 표시해 제거 대상을 판별). `--with-rag`는 `--with-db`를 함의하고 compose의 postgres 이미지를 `pgvector/pgvector`로 바꾼다. 표준 라이브러리만. 기존 파일은 `--force` 없이 덮지 않는다. `scripts/route_table.py [--app {{pkg}}.main:create_app] [--openapi out.json] [--md]`: 앱을 import해 메서드·경로·태그·의존성·응답 모델 표를 출력하고 openapi.json을 저장한다. `--md`는 인터페이스 정의서용 GFM 표(메서드·경로·요청·응답·오류·설명)를 출력한다.

규칙(python-conventions 요약): 핸들러에서 블로킹 I/O 금지 · 모든 외부 호출에 타임아웃+재시도 · 벤더 SDK 키를 앱에 두지 않음(게이트웨이만) · 로그에 프롬프트·PII 기본 미기록 · 설정은 env만 · 레이어 방향 api → services → infra(역방향 import 금지) · 상태 저장은 infra만 · 프롬프트는 파일(버전 필드)로, 변경은 MR 리뷰 대상 · LLM 출력은 스키마로 검증하고 실패 시 1회 재요청 후 오류 · 사용자 입력은 프롬프트의 데이터 슬롯에만(지시 슬롯에 넣지 않음).

### 8.5 `gitlab-ci` (CI/CD)

```yaml
---
name: gitlab-ci
description: >
  GitLab CI/CD 파이프라인을 만들고 고치고 운영한다. ".gitlab-ci.yml", "파이프라인", "CI 만들어줘", "빌드/배포 자동화",
  "컨테이너 레지스트리", "MR 파이프라인", "환경별 배포(dev/stg/prod)", "파이프라인 실패 원인", "잡 로그 확인",
  "MR 템플릿", "브랜치 전략" 요청에 반드시 쓴다. GitLab 공식 MCP(연결돼 있으면)로 파이프라인·잡·MR을 조회하고
  재시도한다. GitHub Actions·Jenkins는 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[생성 | 진단 <pipeline id|MR> | 배포 대상]"
allowed-tools:
  - Bash(python */skills/gitlab-ci/scripts/ci_lint.py *)
  - Bash(git *)
---
```

절차: ① 프로젝트 성격 파악(Python? Docker? 배포 대상?) ② **파이프라인 리드 1줄**: `CI: <프로젝트> · 스테이지 <lint,test,build,scan,deploy> · 배포 <compose 호스트|k8s|ACA|ECS|Cloud Run|없음> · 게이트 <dev 자동, stg/prod 수동>` ③ `assets/gitlab-ci.yml`을 복사해 변수만 채움(발명하지 않는다) ④ `ci_lint.py .gitlab-ci.yml`(GitLab API `POST /projects/:id/ci/lint`, `GITLAB_URL`·`GITLAB_TOKEN`·`CI_PROJECT_ID` env, 없으면 로컬 YAML 문법만 검사하고 안내) ⑤ MR·이슈 템플릿, CODEOWNERS 추가(있으면 건너뜀) ⑥ 진단 요청이면 `references/gitlab-mcp-playbook.md` 흐름: `get_pipeline` → 실패 잡 `get_job`(trace) → 원인 3분류(코드/환경/인프라) → 수정 → `save_pipeline retry`(사용자 확인 후).

`assets/gitlab-ci.yml` 필수 내용: `workflow.rules`(MR 파이프라인과 브랜치 파이프라인 중복 방지, 태그 파이프라인) · `stages: [lint, test, build, scan, deploy]` · `default.image python:3.12` · uv 캐시(`UV_CACHE_DIR`, `cache.key.files: [uv.lock]`) · lint 잡(`uv run ruff check`, `ruff format --check`) · test 잡(`--junitxml`, `--cov --cov-report=xml`, `artifacts.reports.junit/coverage_report(cobertura)`, `coverage` 정규식) · build 잡(kaniko, `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA` + main이면 `latest`, DinD 대안은 주석) · scan(`include: template: Security/SAST.gitlab-ci.yml`, `Container-Scanning`, 실패해도 파이프라인 안 깨는 `allow_failure`) · deploy 3환경(`environment.name/url`, dev는 main 자동, stg·prod는 `when: manual`, prod는 태그만, `resource_group`) · 배포 스크립트는 `references/deploy-targets.md`의 대상별 블록 중 하나를 include.

references: `pipeline-recipes.md`(모노레포 `rules.changes`, 스케줄 파이프라인, 캐시 vs 아티팩트, 시크릿은 CI 변수 masked/protected, 러너 태그), `deploy-targets.md`(compose 호스트 ssh, Kubernetes/Helm, Azure Container Apps, AWS ECS, Cloud Run: 각각 필요한 CI 변수·명령 블록), `gitlab-mcp-playbook.md`(연결: `claude mcp add --transport http gitlab https://<host>/api/v4/mcp` 또는 `.mcp.json`; 인증 `/mcp` OAuth; 툴 이름 매핑; 폴백 커뮤니티 서버), `branching.md`(trunk-based + 릴리스 태그 권장, gitflow 대안, MR 규칙: 작게, 리뷰어 1명, 스쿼시).

### 8.6 `py-review` (코드 리뷰)

```yaml
---
name: py-review
description: >
  Python·FastAPI·LLM 서비스 코드를 리뷰한다. "리뷰해줘", "MR 리뷰", "코드 봐줘", "PR 검토", "이 diff 문제 없나",
  "머지 전 확인", "보안 검토", "성능 검토" 요청에 반드시 쓴다. 로컬 diff나 GitLab MR(공식 MCP)을 읽고
  심각도·파일:줄·수정안 형식으로 보고한다. 코멘트 게시는 사용자가 승인했을 때만 한다. 리뷰 대상을 직접 고치지 않는다.
version: 0.1.0
user-invocable: true
argument-hint: "[MR 번호 | 브랜치 | 경로 | (없으면 작업 트리 diff)]"
allowed-tools:
  - Bash(git diff *)
  - Bash(git log *)
  - Bash(uv run pytest *)
  - Bash(uv run ruff *)
---
```

절차: ① 대상 확보(`git diff`, 또는 GitLab MCP `get_merge_request` + `get_merge_request_diffs`) ② 변경 의도 파악(MR 설명·커밋 메시지) ③ `references/checklist.md`를 로드해 **호출자까지 추적**(변경 함수의 호출자 grep; 증상만 고친 수정인지) ④ 테스트 실행 가능하면 실행 ⑤ 보고 형식 고정:

```
## 리뷰: <MR 제목 또는 브랜치>
판정: 승인 | 수정 후 승인 | 재작업
### 반드시 (block)
- [파일:줄] <문제> → <수정안> (근거: 체크리스트 항목 ID)
### 권장 (should)
### 참고 (nit)
### 확인 질문 (작성자에게)
```

⑥ 게시는 승인 후 `save_merge_request_review` 또는 `save_note`(MCP). 로컬 전용이면 `docs/reviews/<날짜>-<대상>.md`로 저장하지 않는다(요청 시만).

`references/checklist.md` 항목군(각 항목에 ID): 정확성(경계·None·예외 경로), 비동기(이벤트 루프 블로킹, `asyncio.gather` 예외, 취소), FastAPI(의존성 범위, 응답 모델, 상태 코드, 422 처리, 백그라운드 태스크), pydantic v2(validator 오용, `model_config`), LLM(프롬프트 인젝션 경로, 출력 검증, 타임아웃·재시도·폴백, 비용 상한, 스트리밍 오류 처리, 로그의 프롬프트·PII), 보안(시크릿, 경로 조작, SSRF, 권한), 데이터(트랜잭션, N+1, 마이그레이션), 테스트(변경에 대응하는 테스트 유무, 모킹 경계), 구조(레이어 방향, 순환, 중복), 운영(로그 수준, 메트릭, 설정 기본값). 각 항목은 "증상 → 확인 방법 → 전형적 수정".

### 8.7 `py-test` (단위 테스트)

```yaml
---
name: py-test
description: >
  Python·FastAPI·LLM 서비스의 pytest 테스트를 만들고 정리한다. "테스트 작성", "단위 테스트", "커버리지 올려줘",
  "테스트 없는 함수 찾아줘", "LLM 호출 모킹", "스트리밍 테스트", "골든 파일 테스트", "픽스처 정리", "테스트 실패 분석"
  요청에 반드시 쓴다. HTTP 경계에서 모킹(respx)하고 실제 LLM 호출은 live_llm 마커로 격리한다.
  성능 벤치마크는 model-serving이 담당한다.
version: 0.1.0
user-invocable: true
argument-hint: "[대상 모듈·함수 | 실패 로그]"
allowed-tools:
  - Bash(uv run pytest *)
  - Bash(python */skills/py-test/scripts/test_gaps.py *)
---
```

절차: ① `test_gaps.py <pkg>`로 공개 함수 중 테스트에서 참조되지 않는 것 목록 ② 우선순위: 서비스 로직 > API 계약 > 인프라 어댑터 ③ `references/pytest-conventions.md` 로드(AAA, 이름 `test_<동작>_<조건>_<기대>`, 파라미터화, 픽스처 범위, 마커 `deterministic`/`live_llm`, 커버리지 기준 services 80%) ④ LLM 관련이면 `references/llm-mocking.md`(respx로 `/chat/completions` 응답·스트림 청크 모킹, 골든 파일 `tests/golden/*.txt`로 프롬프트 렌더링 고정, 스트리밍 SSE 파서 테스트, 429/타임아웃/폴백 시나리오, 비용 헤더) ⑤ 실행 → 실패는 원인별로 고침(테스트를 약하게 만들지 않는다) ⑥ 결과 표(추가 테스트 수, 커버리지 전후).

`scripts/test_gaps.py <pkg> [--tests tests]`: stdlib `ast`로 공개 함수·메서드를 모으고 `tests/`에서 이름 참조를 찾아 미참조 목록을 파일별로 출력. 휴리스틱임을 출력 상단에 명시(`# ponytail: 이름 기반 매칭, 호출 그래프 필요하면 coverage로`).

### 8.8 `py-refactor` (모듈화·구조 개선)

```yaml
---
name: py-refactor
description: >
  Python 코드의 모듈화·구조 개선·리팩토링을 계획하고 안전하게 수행한다. "리팩토링", "구조 개선", "모듈 분리",
  "순환 import", "god 파일 쪼개기", "레이어 정리", "중복 제거", "기술 부채 정리", "패키지 재구성" 요청에 반드시 쓴다.
  동작 변화 없이 작은 단위로 옮기고, 이동 전 특성화 테스트를 만들며, 계획을 ADR로 남긴다. 기능 추가는 하지 않는다.
version: 0.1.0
user-invocable: true
argument-hint: "[대상 패키지·모듈]"
allowed-tools:
  - Bash(python */skills/py-refactor/scripts/import_graph.py *)
  - Bash(uv run pytest *)
  - Bash(git *)
---
```

절차: ① `import_graph.py <pkg>`로 순환·레이어 위반·팬인/팬아웃 상위 10개 ② **리팩토링 리드 1줄**: `리팩토링: <대상> · 목표 <순환 제거|레이어 분리|파일 분할|중복 제거> · 범위 <파일 n개> · 동작 변화 없음` ③ 특성화 테스트(현재 동작 고정) 먼저, 없으면 `py-test`로 ④ 이동 계획을 표로(무엇을 어디로, 순서, 각 단계 후 실행할 검증) → `docs/adr/NNNN-<제목>.md`(doc-write ADR 골격) ⑤ 단계마다 `pytest` + `import_graph.py` 재실행, 커밋 1개(사용자가 커밋을 원할 때) ⑥ 완료 보고: 전후 지표(순환 수, 위반 수, 최대 파일 길이).

`scripts/import_graph.py <pkg> [--layers api,services,infra] [--json]`: stdlib `ast`로 모듈 import 그래프 구성, Tarjan SCC로 순환 출력, `--layers`(없으면 `pyproject.toml [tool.ai-work].layers`) 순서를 위반하는 import(하위→상위) 출력, 모듈별 팬인/팬아웃, 300줄 초과 파일. 의존성 0.

규칙: 리팩토링 MR에 동작 변경 섞지 않기 · 공개 함수 시그니처 유지(어댑터로 감싸고 나중에 제거) · `__init__.py` 재수출로 호환 유지 후 호출자 이동 · 한 MR = 한 이동 · import는 항상 api → services → infra 방향.

### 8.9 `llm-gateway` (LiteLLM 게이트웨이)

```yaml
---
name: llm-gateway
description: >
  LiteLLM 프록시 기반 LLM 게이트웨이를 설계·구축·운영한다. "LiteLLM", "LLM 게이트웨이", "API 게이트웨이",
  "config.yaml", "모델 라우팅·폴백", "가상 키·팀별 예산", "Azure OpenAI/Bedrock/Vertex 연결", "vLLM 등록",
  "비용 추적", "Langfuse 연동", "게이트웨이 장애", "모델 교체", "레이트 리밋" 요청에 반드시 쓴다.
  설정은 검증(config_validate) 후에만 배포하고, 상태·비용·키는 litellm-ops MCP로 본다. 시크릿은 절대 yaml에 쓰지 않는다.
  모델 서빙(vLLM 자체 운영)은 model-serving이 담당한다.
version: 0.1.0
user-invocable: true
argument-hint: "[구축 | 모델 추가 | 키 발급 | 장애 진단 | 비용]"
allowed-tools:
  - Bash(uv run --project * python -m litellm_ops *)
  - Bash(docker compose *)
  - mcp__litellm-ops
---
```

절차: ① 요청 분류(구축/모델 추가/키·예산/장애/비용/관측) ② 구축이면 **게이트웨이 리드 1줄**: `게이트웨이: <환경> · 제공자 <azure,bedrock,vertex,openai,vllm 중> · 라우팅 <simple-shuffle|least-busy|latency> · 폴백 <있음> · 예산 <팀별> · 관측 <langfuse|otel|없음>` ③ `assets/config.example.yaml`을 복사해 채움(제공자별 블록은 `references/<provider>.md`) ④ `python -m litellm_ops config-validate config.yaml`(또는 MCP `config_validate`) 오류 0 ⑤ `assets/compose.yaml`로 기동(postgres 필수: 가상 키·비용) ⑥ `gateway_health` → `test_completion` ⑦ 팀 생성·예산(`team_create`) 후 팀 키 발급(`key_create`, 둘 다 쓰기 게이트 필요). 키 전체 값은 응답에 한 번만 나오므로 사용자에게 즉시 비밀 저장소에 넣도록 안내하고 대화에 다시 적지 않는다 ⑧ 앱 연결법 안내(`assets/client_example.py`: OpenAI SDK `base_url`, `user`·`metadata.tags`, 스트리밍, 구조화 출력, 재시도) ⑨ 장애면 `references/ops-runbook.md` 순서(health → 죽은 엔드포인트 → 폴백 확인 → 제공자 상태 → 키 예산 소진 → 레이트 리밋).

`assets/config.example.yaml` 요구: `model_list`에 azure 2리전(같은 `model_name`으로 로드밸런싱), bedrock claude, vertex gemini, `hosted_vllm/` 사내 모델, `openai/` 1개 · 모든 키·엔드포인트는 `os.environ/`, `.env.example`과 1:1 · `litellm_settings`: `drop_params`, `num_retries: 2`, `request_timeout`, `fallbacks`, `context_window_fallbacks`, `success_callback: ["langfuse"]`(주석), `cache`(redis, 주석) · `router_settings.routing_strategy` · `general_settings`: `master_key: os.environ/LITELLM_MASTER_KEY`, `database_url: os.environ/DATABASE_URL`, `background_health_checks: true`, `health_check_interval: 300`, `alerting`(주석) · `guardrails` 예시 1개(주석) · 각 블록에 "왜"를 한 줄 주석.

references: `azure.md`(리소스·배포명·api_version, 리전 이중화), `bedrock.md`(IAM·리전·모델 ID 형식), `vertex.md`(프로젝트·위치·서비스 계정), `vllm.md`(`hosted_vllm/` 등록, api_base), `observability.md`(Langfuse/OTel/Prometheus `/metrics`, 비용 헤더, 로그 보존), `security.md`(키 등급, 팀·예산 모델, 프롬프트 인젝션 기초, PII 마스킹 콜백, 감사 로그), `ops-runbook.md`(기동·헬스·모델 추가·키 회전·예산 알림·장애·업그레이드 절차, 각 단계의 MCP 툴/curl 대응표).

### 8.10 `model-serving` (모델 서빙·최적화)

```yaml
---
name: model-serving
description: >
  오픈소스 LLM·VLM을 vLLM 등으로 서빙하고 최적화한다. "vLLM", "모델 서빙", "자체 호스팅", "양자화(AWQ/GPTQ/FP8)",
  "GPU 메모리·VRAM 산정", "몇 장 필요해", "처리량·지연 벤치마크", "텐서 병렬", "컨텍스트 길이", "서빙 모델을
  게이트웨이에 등록" 요청에 반드시 쓴다. 모델 학습·파인튜닝은 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[모델 이름 | GPU 사양 | 벤치 대상 URL]"
allowed-tools:
  - Bash(python */skills/model-serving/scripts/*.py *)
---
```

절차: ① `vram_estimate.py --params 32 --dtype fp16|int8|int4 --ctx 32768 --batch 8 [--layers --heads --head-dim]` → 가중치+KV 캐시+여유 20% 표 ② `references/sizing.md`의 표(7B/14B/32B/70B × 정밀도 × 컨텍스트)로 GPU 수 결정 ③ `references/vllm.md`로 `vllm serve` 인자(`--dtype`, `--max-model-len`, `--tensor-parallel-size`, `--quantization`, `--gpu-memory-utilization`, `--enable-prefix-caching`) ④ `bench_llm.py --base-url <url> --model <m> --concurrency 1,4,16 --prompt-tokens 512 --max-tokens 256` → TTFT p50/p95, tokens/s, 실패율 ⑤ `llm-gateway`로 등록 ⑥ 결과를 `doc-write` 기술 검토서 골격으로 남길지 물음(한 번).

references: `vllm.md`, `quantization.md`(AWQ/GPTQ/FP8/GGUF 선택 기준, 품질 손실 확인법), `sizing.md`(산식과 표), `alternatives.md`(TGI, Ollama, SGLang 한 줄 비교).

### 8.11 `ai-trend-brief` (트렌드 조사)

```yaml
---
name: ai-trend-brief
description: >
  생성형 AI 기술 트렌드를 조사해 우리 서비스에 미치는 영향과 적용 아이디어까지 담은 브리프를 만든다.
  "AI 트렌드", "이번 주 동향", "최신 기술 조사", "새 모델 나왔나", "LiteLLM/vLLM 릴리스 노트", "경쟁사 동향",
  "월간 기술 동향 보고", "이 논문 우리한테 의미 있나" 요청에 반드시 쓴다. 모든 항목에 출처 URL과 날짜를 달고
  사실·추론·권고를 구분한다. 단순 뉴스 요약이나 링크 나열은 하지 않는다.
version: 0.1.0
user-invocable: true
argument-hint: "[주간 | 월간 | 주제]"
allowed-tools:
  - WebSearch
  - WebFetch
---
```

절차: ① 기간·주제 확정(기본 최근 7일) ② `assets/sources.yaml`(공식 블로그: OpenAI·Anthropic·Google·Meta·Microsoft·AWS, 릴리스: LiteLLM·vLLM·FastAPI·LangGraph, 논문: arXiv cs.CL/cs.AI 주간, 커뮤니티: HF blog·papers, GitHub trending python)에서 검색 ③ 후보 15개 → `docs/trends/`의 이전 브리프 제목·URL과 대조해 이미 다룬 항목은 "후속"으로만 표시 → **우리 관련도**(STYLE.md §1의 조직 설명·서비스 목록 기준)로 5~7개 선별 ④ 항목 형식 고정: 제목 / 출처(URL, 날짜) / 사실 3줄 / 우리에게 미치는 영향(추론, 대상 서비스 명시) / 적용 아이디어(권고, 다음 행동 1개) / 확인 필요 ⑤ `docs/trends/<YYYY>-W<주차>.md`(`assets/brief-template.md`) ⑥ 월간이면 `deck-write`로 5장 덱 제안(한 번만 묻는다).

### 8.12 공용 references (`references/`, 플러그인 루트)

| 파일 | 내용 | 쓰는 스킬 |
|---|---|---|
| `writing-rules-ko.md` | review-report-writer `writing-rules.md`를 흡수·확장: 문장 원칙 12개, AI식 표현 목록(§7의 H2~H5·S3~S7 어휘를 사람이 읽게 정리), 사실/추론/권고 표현, 비교표 규칙, 좋은 예/나쁜 예 쌍 10개(설계서·가이드·브리프·덱 각각), "사람이 쓴 것처럼"의 실체(결론 먼저, 구체 수치+출처, 판단 문장 1인칭 조직 주어 "~로 판단한다", 문단 길이 변화, 반복 없음, 요약 없음, 단점 명시) | doc-write, deck-write, ai-trend-brief |
| `python-conventions.md` | 레이어 규칙, 설정·로깅·예외·비동기·타임아웃·재시도 규약, 네이밍, 타입 힌트, 의존성 정책(uv, 잠금), 프롬프트 파일 규약(frontmatter·버전·변수·골든 테스트), 금지 목록(전역 상태, `print`, 광범위 `except`, 동기 requests in async, 인라인 프롬프트) | fastapi-service, py-review, py-test, py-refactor |
| `genai-patterns.md` | 생성형 AI 서비스 설계 패턴. **RAG**(수집→청킹(크기·겹침 기준)→임베딩(게이트웨이 `/embeddings`)→pgvector 저장→하이브리드 검색 선택 기준→프롬프트 조립(인용 형식)→응답 검증), **구조화 출력·툴 호출**(스키마 우선, 실패 재시도 1회), **에이전트**(단순 루프부터, 단계 수·비용 상한), **비동기 작업**(202+폴링, 멱등 키), **가드레일**(입력 길이·인젝션 패턴·출력 PII, 게이트웨이 guardrails와 역할 분담), **평가 기초**(골든 셋 20~50문항, 검색 적중률·정답 포함률·사람 스팟체크, promptfoo 안내), **비용·지연 설계**(모델 티어링, 캐시, 스트리밍 우선), 각 패턴의 설계서 TO-BE 구성도 예시(DSL) | fastapi-service, doc-write, deck-write, py-review |
| `arch-doc-types.md` | 아키텍처 문서 유형: 설계서(개요·요구사항·제약·AS-IS·TO-BE·구성도 3수준(컨텍스트/컨테이너/컴포넌트)·인터페이스·데이터·비기능(성능·가용성·보안·비용) 표·단계별 구축·위험), 인터페이스 정의서(엔드포인트 표: 메서드·경로·요청·응답·오류·SLA), 운영 런북(증상→확인→조치→에스컬레이션), ADR(맥락·결정·대안·결과, 상태), 구성도 규약(노드 종류 6종과 색 역할, 화살표 라벨은 프로토콜/데이터, 그룹은 경계, 좌→우 요청 흐름, 외부는 점선) | doc-write, deck-write |

### 8.13 `skills/llms.txt`

한 줄씩 11개. ui-skill-set 형식. 각 줄은 description의 첫 문장 + 트리거 어휘 5개.

---

## 9. MCP 서버 명세

공통:
- Python ≥ 3.11, FastMCP ≥ 4 (`fastmcp>=4,<5`), stdio 전송. 각 서버는 `mcp/<이름>/pyproject.toml`이 있는 독립 uv 프로젝트이고, 루트 `pyproject.toml`이 `[tool.uv.workspace] members = ["mcp/*"]`로 묶는다.
- 툴 함수는 `<pkg>/core.py`의 순수 함수를 감싼다. 같은 함수가 `python -m <pkg> <명령>`(argparse) CLI로 노출된다. MCP 계층에는 로직이 없다(테스트는 core만 대상으로 해도 충분하도록).
- 반환은 JSON 직렬화 가능한 dict. 오류는 `fastmcp.exceptions.ToolError("<코드>: <사람이 읽는 이유>")`. 스택 트레이스를 사용자에게 내지 않는다.
- 시크릿은 절대 반환하지 않는다. 키는 `sk-…{마지막 4자}` 형식으로 마스킹. 환경변수 값은 이름만 보고한다.
- 네트워크 타임아웃 기본 10초(`test_completion`만 60초). 재시도 없음(운영 도구는 실패를 그대로 보여야 한다).
- 로그는 stderr(stdio 전송에서 stdout은 프로토콜 전용).
- **경로 해석**: MCP 서버 프로세스의 cwd는 보장되지 않는다. 툴은 절대 경로를 권장하고, 상대 경로는 `DOCGEN_PROJECT_DIR`(`.mcp.json`에서 `${CLAUDE_PROJECT_DIR}`로 주입) → cwd 순으로 기준을 잡는다. 결과 dict에는 항상 절대 경로를 넣는다. `STYLE.md`·`docs/theme.json`·`docs/glossary.md`도 같은 기준 디렉터리에서 찾는다.
- 반환 dict에는 `warnings: [str]`을 항상 포함한다(없으면 빈 배열). 스킬은 경고를 사용자에게 전달한다.

### 9.1 `litellm-ops`

환경변수: `LITELLM_BASE_URL`(기본 `http://localhost:4000`), `LITELLM_MASTER_KEY`(admin 엔드포인트), `LITELLM_API_KEY`(선택, `test_completion`용 가상 키. 없으면 master), `LITELLM_OPS_ALLOW_WRITE`(`true`일 때만 쓰기 툴 동작), `LITELLM_CONFIG_PATH`(선택, `config_validate` 기본 경로).

| 툴 | 입력 | 동작 | 출력 |
|---|---|---|---|
| `gateway_health()` | 없음 | `GET /health/liveliness`, `GET /health/readiness`, `GET /health` 순서로 호출. 하나가 실패해도 나머지 진행 | `{liveness, readiness:{status, db}, healthy:[{model, api_base(host만)}], unhealthy:[…], checked_at}` |
| `list_models(include_params=false)` | | `GET /model/info` | `[{model_name, provider(접두사), model, api_base(host만), rpm, tpm, model_id}]` |
| `test_completion(model, prompt="ping", max_tokens=16)` | | `POST /chat/completions`(비스트리밍). 지연·비용 헤더·첫 60자 | `{model, latency_ms, cost_usd(헤더 `x-litellm-response-cost`), usage, sample}` |
| `spend_summary(start_date, end_date, group_by="api_key")` | ISO 날짜, `group_by ∈ {api_key, team, internal_user_id, customer}` | `GET /global/spend/report` | `{rows:[{group, spend_usd, tokens}], total_usd}`. 실패 시 `GET /spend/logs?summarize=true` 폴백 |
| `key_info(key)` | 키 문자열 또는 alias | `GET /key/info?key=` | `{key_masked, alias, models, spend, max_budget, budget_duration, expires, team_id, blocked}` |
| `key_create(alias, models, max_budget, budget_duration="1mo", team_id=None, metadata=None)` | | **쓰기 게이트**. `POST /key/generate` | `{key_masked, key_full_once}`: 전체 키는 이 응답 **한 번만** 포함하며 메시지에 "지금 저장하라"를 붙인다 |
| `key_block(key)` / `key_unblock(key)` | | 쓰기 게이트. `POST /key/block` / `/key/unblock` | `{key_masked, blocked}` |
| `team_info(team_id)` | | `GET /team/info?team_id=` | `{team_id, alias, spend, max_budget, budget_duration, models, keys_count}` |
| `team_create(alias, max_budget, budget_duration="1mo", models=None)` | | 쓰기 게이트. `POST /team/new` | `{team_id, alias, max_budget}` |
| `config_validate(path=None)` | 경로 없으면 `LITELLM_CONFIG_PATH` | 로컬 파일. 네트워크 없음. 규칙 V1~V8(아래) | `{ok, findings:[{code, level:error|warn, path, message}]}` |
| `config_diff(path_a, path_b)` | | 두 config의 `model_list`(model_name+model+api_base 키)·`fallbacks`·`router_settings`·`general_settings` 구조 diff | `{added:[…], removed:[…], changed:[{path, a, b}]}` |

`config_validate` 규칙:

| 코드 | 수준 | 내용 |
|---|---|---|
| V1 | error | YAML 파싱 실패 / 최상위가 매핑이 아님 |
| V2 | error | `model_list`가 비었거나 항목에 `model_name`·`litellm_params.model`이 없음 |
| V3 | warn | `litellm_params.model` 접두사가 알려진 목록(`azure/ openai/ anthropic/ bedrock/ vertex_ai/ gemini/ hosted_vllm/ ollama/ groq/ mistral/ cohere/ together_ai/ fireworks_ai/ deepseek/ xai/`) 밖 |
| V4 | error | `api_key`·`api_base`·`aws_secret_access_key`·`vertex_credentials`·`master_key`·`database_url` 값이 `os.environ/` 참조가 아니고 H9 시크릿 패턴이거나 20자 이상 토큰 모양 |
| V5 | warn | `os.environ/NAME`의 NAME이 프로세스 환경에도 `.env.example`(같은 디렉터리)에도 없음 |
| V6 | error | `litellm_settings.fallbacks`·`context_window_fallbacks`의 키·값이 `model_list`의 `model_name`(또는 `model_group_alias`)에 없음 |
| V7 | warn | `router_settings.routing_strategy`가 `simple-shuffle latency-based-routing least-busy usage-based-routing cost-based-routing` 밖 |
| V8 | warn | 같은 `model_name`이 같은 `api_base`·`model`로 중복(무의미한 복제) / `general_settings.master_key` 누락 / `background_health_checks` 미설정 |

쓰기 게이트: `LITELLM_OPS_ALLOW_WRITE`가 `true`가 아니면 `ToolError("WRITE_DISABLED: 읽기 전용 모드. .mcp.json env에 LITELLM_OPS_ALLOW_WRITE=true를 설정하고 재시작")`. 스킬은 이 오류를 받으면 우회하지 않고 사용자에게 설정을 요청한다.

테스트(`mcp/litellm_ops/tests/`): `httpx.MockTransport`로 각 엔드포인트 응답 픽스처(실제 응답 형태) → 툴별 정상·실패(401, 503, 타임아웃)·마스킹 assert. `config_validate`는 픽스처 yaml 8개(V1~V8 각 1개 양성 + 정상 1개). CLI는 `subprocess`로 `--help`와 `config-validate` 1회.

### 9.2 `docgen`

환경변수: `DOCGEN_THEME_DIR`(추가 테마 디렉터리, 선택), `DOCGEN_FONT_DIRS`(PNG 렌더용 폰트 탐색 경로 추가, 선택), `SOFFICE_PATH`(LibreOffice 실행 파일, 선택).

| 툴 | 입력 | 출력 |
|---|---|---|
| `render_docx(spec_path, out_path=None, theme=None, template_docx=None)` | `.doc.md` 경로. `theme` 없으면 frontmatter → `STYLE.md` → `datasolution` 순. `out_path` 없으면 `docs/_build/<filename_pattern>.docx`. `template_docx` 없으면 `STYLE.md template_docx` | `{out_path, pages_estimate, headings:[…], warnings:[…]}` |
| `render_pptx(spec_path, out_path=None, theme=None, template_pptx=None)` | `.deck.md` 경로. 기본 출력·템플릿 해석은 위와 같음 | `{out_path, slide_count, slides:[{index, title, layout}], warnings}` |
| `render_diagram(spec_path_or_text, out_path, format="png\|svg\|mermaid", theme=None)` | DSL(YAML) 파일 또는 문자열 | `{out_path, nodes, edges, warnings}` |
| `diagram_from_compose(compose_path, out_path=None)` | `compose.yaml` | 서비스→노드(`kind` 추론: 이미지 이름에 postgres/redis/mysql→data, litellm→gateway, vllm/ollama→llm, 나머지 service), `depends_on`→엣지, 포트 라벨, 프로필→그룹. DSL YAML 문자열 반환·저장. 현행(AS-IS) 구성도 초안용 |
| `lint_doc(path, mode="all")` | 산문 파일 | `doc_lint.lint()`의 findings 그대로 `{hard:[…], soft:[…]}` |
| `preview(path, pages="1-3", dpi=110)` | docx/pptx | LibreOffice로 PDF → PNG(`pdftoppm` 또는 `soffice --convert-to png`). 없으면 `{available:false, hint}` |
| `docx_to_md(path)` / `pptx_to_md(path)` | 기존 문서 | Markdown 문자열 + 구조 요약(제목 트리, 표 수, 그림 수). 회사 양식 학습용 |
| `theme_from_pptx(path, name, out_dir="themes")` | 회사 템플릿 | `theme1.xml`의 `clrScheme`(dk1 lt1 dk2 lt2 accent1~6 hlink)·`fontScheme`(major/minor latin+ea)·슬라이드 크기·레이아웃 이름 목록을 테마 JSON으로 저장. `layout_map`은 이름 유사도로 초안 작성 후 `warnings`에 "확인 필요" 표시 |
| `layouts(path)` | pptx | 레이아웃 이름·placeholder(idx, type, 위치) 목록 |
| `theme_export(name, format="tokens-css")` | | ui-skill-set용 `--ui-accent-100…900` CSS 스니펫(§10.4) |

CLI 동등 명령: `python -m docgen render-docx|render-pptx|render-diagram|lint|preview|docx-to-md|pptx-to-md|theme-from-pptx|layouts|theme-export`. 모든 명령은 `--json`으로 위 dict를 출력.

의존성(`mcp/docgen/pyproject.toml`): `fastmcp>=4,<5`, `python-docx>=1.2,<2`, `python-pptx>=1.0,<2`, `markdown-it-py>=3,<4`, `mdit-py-plugins>=0.4`, `PyYAML>=6,<7`, `Pillow>=10,<12`. 그 외 금지(특히 pandoc·LibreOffice는 선택 외부 도구로만).

### 9.3 GitLab 공식 MCP (설정만)

프로젝트 `.mcp.json`(설치기가 병합):
```json
{
  "mcpServers": {
    "gitlab": { "type": "http", "url": "${GITLAB_URL}/api/v4/mcp" }
  }
}
```
인증은 Claude Code에서 `/mcp` → gitlab 선택 → 브라우저 OAuth 승인. 전제: 인스턴스 18.3 이상(19.2부터 Free), GitLab Duo 및 beta 기능 켜짐. 안 되면 `references/gitlab-mcp-playbook.md`의 커뮤니티 서버 stdio 설정(`GITLAB_PERSONAL_ACCESS_TOKEN`)으로 폴백. 툴 이름은 스킬이 하드코딩하지 않고 `get_merge_request_diffs`·`get_job` 등 **공식 이름**을 우선 시도한 뒤 없으면 목록에서 유사 이름을 고른다.

---

## 10. 문서 생성 엔진 (docgen)

### 10.1 `.doc.md` (문서 DSL)

일반 Markdown(GFM 표 포함) + YAML frontmatter. 렌더러가 해석하는 것만 아래에 적는다. 나머지 Markdown은 표준대로.

```markdown
---
title: 사내 LLM Gateway 아키텍처 설계서
subtitle: LiteLLM 기반 공용 LLM API          # 선택
doc_type: 설계서                               # 설계서|검토보고서|가이드|런북|ADR|정의서|회의록|브리프|README|교육
org: 데이타솔루션 기술연구소
author: 민현성
date: 2026-09-04
version: 0.1
security: 대외비                               # 머리글 오른쪽. 없으면 생략
theme: datasolution                            # 이름 또는 JSON 경로. 생략 시 STYLE.md → datasolution
toc: true                                      # 목차 필드 삽입
history:
  - { version: 0.1, date: 2026-09-04, author: 민현성, note: 초안 }
approvers: [팀장, 본부장]                        # 선택. 표지 결재란
---
# 1. 개요
본문 문단…

## 1.1 목적
- 글머리표
1. 번호 목록

| 항목 | 대안 A | 대안 B | 검토 의견 |
|---|---|---|---|

```diagram
type: architecture
…(§10.3)
```

```timeline
…(§10.3)
```

```chart
…(§10.3)  → docx·md에서는 데이터 표 + 캡션으로 렌더링
```

![캡션 텍스트](images/x.png)          → 그림 + 캡션 "[그림 n] 캡션"
<!-- caption: 표 캡션 -->              → 바로 다음 표의 캡션 "[표 n] …"
<!-- pagebreak -->
> 인용/참고 박스(연한 배경)
`[확인 필요]`                            → placeholder_marker는 노란 형광
```

렌더 규칙: `#` H1 = 장(章) 제목, `##` H2, `###` H3까지 스타일. H4 이하는 굵은 본문. 제목 번호는 텍스트 그대로(자동 번호 없음, 결정적). 표지·개정이력·목차는 frontmatter만으로 자동 생성. 코드 펜스 → `Code` 스타일. 각주 `[^1]` → 문서 끝 "참고" 절.

### 10.2 `.deck.md` (덱 DSL)

```markdown
---
title: LLM Gateway 도입 아키텍처
subtitle: LiteLLM 기반 사내 공용 LLM API
org: 데이타솔루션 기술연구소
author: 민현성
date: 2026-09-04
theme: datasolution
template: null            # 회사 템플릿 .pptx 경로. 있으면 그 마스터·레이아웃 사용
agenda: true              # 목차 슬라이드 자동(각 슬라이드 # 제목에서, section 슬라이드 우선)
security: 대외비
footer: 데이타솔루션 기술연구소   # 바닥글 왼쪽. 오른쪽은 쪽번호 자동
---
# 배경
<!-- layout: message -->
## 모델별 API 키가 12개 팀에 흩어져 비용과 보안을 통제하지 못한다
- 팀별 OpenAI·Azure 키 개별 발급, 월 사용량 집계 불가
- 프롬프트·응답 로그 미보관, 장애 원인 추적 곤란
- 모델 교체 시 12개 서비스 코드 수정 필요
<!-- note: 현재 키 12개 중 3개는 담당자 퇴사로 소유자 불명 -->

---
# 목표 아키텍처
<!-- layout: diagram -->
## 게이트웨이 한 곳에서 인증·라우팅·비용을 처리한다
```diagram
…
```

---
# 대안 비교
<!-- layout: table -->
## LiteLLM이 운영 부담 대비 기능이 가장 넓다
| 항목 | LiteLLM | Kong AI Gateway | 자체 개발 | 검토 의견 |
|---|---|---|---|---|
| … |
<!-- source: 각 제품 공식 문서 2026-09 기준 -->

---
# 추진 일정
<!-- layout: timeline -->
## 10월 말 파일럿, 12월 전사 전환
```timeline
…
```

---
# 요청 사항
<!-- layout: closing -->
## 파일럿 예산 승인과 팀별 키 발급 정책 확정이 필요하다
- 결정 1: …
- 결정 2: …
```

규칙: 슬라이드 구분 `---` · `#` 슬라이드 제목(≤ 20자, 상단 작은 글자) · `##` 헤드 메시지(정확히 1개, ≤ 60자, 슬라이드에서 가장 큰 글자) · `<!-- layout: cover|agenda|section|message|two-col|diagram|table|timeline|image|closing -->`(생략 시 내용으로 추론: diagram 블록 → diagram, 표 → table, `<!-- col -->` → two-col, 나머지 message) · `<!-- note: -->` 발표자 노트 · `<!-- source: -->` 바닥글 출처 · 표지는 frontmatter로 자동, `agenda: true`면 2번째 장 자동.

### 10.3 구성도 DSL과 렌더러

YAML. ` ```diagram ` 펜스 안에 쓴다.

```yaml
type: architecture          # architecture | flow | deployment (동일 렌더러, 기본 스타일만 다름)
direction: LR               # LR | TB
groups:
  - { id: client, label: 사용자 채널 }
  - { id: platform, label: AI 플랫폼 (신규) , style: highlight }
  - { id: providers, label: 외부 모델 제공자 }
nodes:
  - { id: web, label: 웹 포털, kind: ui, group: client }
  - { id: api, label: 요약 API\n(FastAPI), kind: service, group: platform }
  - { id: gw, label: LiteLLM Proxy, kind: gateway, group: platform, note: 라우팅·예산·키 }
  - { id: pg, label: PostgreSQL, kind: data, group: platform }
  - { id: azure, label: Azure OpenAI, kind: external, group: providers }
  - { id: vllm, label: vLLM (사내 GPU), kind: llm, group: providers }
edges:
  - { from: web, to: api, label: HTTPS }
  - { from: api, to: gw, label: OpenAI 호환 API }
  - { from: gw, to: pg, label: 키·비용, style: dashed }
  - { from: gw, to: azure }
  - { from: gw, to: vllm, label: 폴백, style: dashed }
```

- `kind` 6종과 테마 역할: `ui`(surface_alt 채움·primary 테두리) `service`(white 채움·primary 테두리·primary 글자) `gateway`(primary 채움·white 글자, 강조 1개) `data`(surface 채움, 원통 대신 모서리 둥근 사각형) `external`(white 채움·점선 테두리·ink_muted 글자) `llm`(accent 10% 틴트 채움·accent 테두리). 색은 전부 테마에서. `group.style: highlight`는 accent 점선 경계.
- **레이아웃 알고리즘**(공통 모듈 `diagram/layout.py`): 그룹을 `direction` 순서로 열(LR) 또는 행(TB)에 배치. 그룹 안 노드는 세로(LR)로 균등 배치. 노드 크기 고정(w 1.9in × h 0.8in, 라벨 줄 수에 따라 +0.25in), 그룹 패딩 0.25in, 그룹 간격 0.6in. 엣지는 노드 중심 간 직선(같은 열이면 elbow). 겹침 최소화만 하고 최적화는 하지 않는다(`# ponytail: 열 기반 배치, 20노드 넘으면 grandalf 검토`). 노드 20개 초과·그룹 6개 초과면 경고.
- 렌더러 3종은 같은 레이아웃 결과(노드 사각형 좌표, 엣지 좌표)를 받는다:
  - `mermaid`: `flowchart LR` + `subgraph`, `classDef` 6종(테마 hex), 점선 `-.->`. GitLab이 md에서 바로 렌더링한다.
  - `pptx`: `MSO_SHAPE.ROUNDED_RECTANGLE`(adjust 0.12) + `add_connector(STRAIGHT|ELBOW)` + `a:tailEnd type="triangle"`, 라벨은 엣지 중점의 텍스트 상자(흰 배경). 그룹은 뒤에 깔린 사각형 + 좌상단 라벨. 도형 이름(`shape.name`)에 노드 id를 넣어 나중에 편집·추적 가능하게.
  - `png`(Pillow): 같은 좌표를 200dpi로. 폰트는 테마 `font_paths` → `malgun.ttf`(Windows) → NanumGothic → Apple SD Gothic 순 탐색, 없으면 경고 후 mermaid 텍스트 파일로 대체.
- 그룹이 없는 노드는 암묵적 그룹(라벨 없음)에 모아 배치한다. `kind` 생략 시 `service`. 라벨의 `\n`은 줄바꿈. 한글 라벨은 어절(공백) 단위로만 줄을 바꾼다(PNG 렌더러의 자체 줄바꿈 포함).
- PNG 렌더러가 한글 폰트를 찾지 못하면 docx에는 그림 대신 mermaid 소스를 코드 블록으로 넣고 `warnings`에 폰트 설치 안내를 남긴다(문서가 깨지지 않게).
- ` ```timeline `: `tasks: [{label, start, end, group?}]`, 날짜 또는 `W36` 주차 → pptx는 가로 막대(테마 primary/accent 교대), docx는 표(항목·시작·종료·비고), md는 `gantt`.
- ` ```chart `: `type: bar|line|pie|stacked`, `title`, `unit`, `categories: [...]`, `series: [{name, values: [...]}]`, `source`. pptx는 python-pptx 네이티브 차트(`add_chart`, 편집 가능. 시리즈 색은 테마 `colors` 순서 primary→accent→action→ink_subtle, 격자선 line_soft, 데이터 레이블 body_pt-2, 범례 하단, 3D·그림자·그라데이션 없음). docx·md는 같은 데이터를 표(`[표 n] title (unit)`)로 낸다(차트 이미지는 만들지 않는다: 의존성과 오탐 방지). 시리즈 5개 이상·카테고리 13개 이상은 경고.

### 10.4 테마 JSON (`themes/datasolution.json`)

```json
{
  "name": "datasolution",
  "source": "datasolution.kr CSS 변수(2026-09-04 측정) + CI 안내(C100 / C100 M85 K10). 공식 템플릿 확보 시 theme_from_pptx로 교체",
  "colors": {
    "primary": "#133F91", "primary_dark": "#002B96", "accent": "#00AEEF", "action": "#1366E3",
    "ink": "#222222", "ink_muted": "#666666", "ink_subtle": "#999999",
    "line": "#CDCDCD", "line_soft": "#E5E5E5", "surface": "#F7F7F7", "surface_alt": "#F6F7FB", "white": "#FFFFFF",
    "positive": "#0F8A5F", "warning": "#B26A00", "critical": "#C0392B", "highlight": "#FFF2AB"
  },
  "fonts": {
    "office_ko": "맑은 고딕", "office_latin": "맑은 고딕", "web_ko": "Pretendard", "mono": "Consolas",
    "font_paths": ["C:/Windows/Fonts/malgun.ttf", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"]
  },
  "docx": {
    "page": "A4", "margins_mm": [25, 20, 25, 20],
    "body_pt": 10.5, "line_spacing": 1.6, "para_after_pt": 6,
    "h1_pt": 16, "h2_pt": 13, "h3_pt": 11.5, "caption_pt": 9, "code_pt": 9, "table_pt": 9.5,
    "heading_color": "primary", "rule_color": "primary", "table_header_fill": "surface", "table_header_text": "primary"
  },
  "pptx": {
    "size": "16:9", "width_in": 13.333, "height_in": 7.5, "margin_in": 0.5,
    "title_pt": 14, "headline_pt": 22, "body_pt": 14, "caption_pt": 10, "footer_pt": 9,
    "headline_color": "primary", "title_color": "ink_muted", "accent_bar": true,
    "layout_map": {}
  }
}
```

- `theme.schema.json`으로 검증(필수 키, hex 형식). 렌더러는 `colors`·`fonts`·치수만 읽는다. **렌더러 코드에 hex 리터럴 금지**(테스트가 소스를 grep해 `#[0-9A-Fa-f]{6}` 0개를 assert).
- `layout_map`: 회사 템플릿 모드에서 우리 레이아웃 이름 → 템플릿 레이아웃 이름·placeholder idx 매핑. `theme_from_pptx`가 초안을 만든다.
- `theme_export --tokens-css`: `primary`와 `action`을 기준으로 OKLCH 보간(표준 라이브러리로 sRGB↔OKLab 변환 구현, 의존성 추가 금지)해 `--ui-accent-100…900`을 만들고 ui-skill-set `tokens.css`의 accent 블록과 같은 형식으로 출력. 700 단계가 흰 글자 대비 4.5:1을 넘는지 계산해 아니면 어둡게 조정한다.

### 10.5 docx 렌더링 규칙과 함정

- 페이지: A4, 여백 테마값. 머리글 왼쪽 `title`, 오른쪽 `security`. 바닥글 가운데 `PAGE / NUMPAGES` 필드(`w:fldSimple`).
- 표지: 상단 primary 색 가로줄(문단 하단 테두리 `w:pBdr` 또는 1행 표 음영), 제목(h1_pt+8, primary), 부제, 조직·작성자·일자·버전 표(테두리 없음), `approvers`가 있으면 결재란 표(빈 칸), 로고는 `docs/assets/logo.png`가 있을 때만 좌상단.
- 개정 이력 표(버전·일자·작성자·내용) → 목차(`TOC \o "1-3" \h \z \u` 필드 + `w:updateFields`로 열 때 갱신) → 페이지 나눔 → 본문.
- 스타일: `Normal`·`Heading 1~3`·`Caption`·`Code`·`Quote`·`TableText`를 **모두 명시 설정**. 기본 템플릿의 Calibri/테마색(#2F5496)이 남지 않게 `font.color.rgb`와 East Asian 폰트(`rPr.rFonts`의 `w:eastAsia`)를 지정한다. 본문 `line_spacing`, `para_after`. 제목 앞 여백 > 뒤 여백.
- 표: `Table Grid` 기반, 헤더 행 음영(`w:shd`)·글자색·굵게·반복(`w:tblHeader`), 셀 여백, 숫자 열 오른쪽 정렬(정규식으로 숫자 열 감지), 열 너비는 내용 길이 비례(최소 15%). 캡션은 표 **위** "[표 n] …", 그림 캡션은 **아래** "[그림 n] …".
- 코드: `Code` 스타일(mono, code_pt, surface 음영, line_soft 테두리), 줄 유지.
- 마커 강조: `placeholder_marker` 패턴 run에 `highlight_color = YELLOW`.
- 어절 단위 줄바꿈: 모든 본문 문단 `w:pPr`에 `<w:wordWrap w:val="0"/>`(Word의 "한글 단어 잘림 허용" 해제에 해당)를 넣는다. `[확인 필요]` 실제 Word 2021·LibreOffice에서 어절이 끊기지 않는지 픽스처로 확인하고, 다르면 `w:kinsoku`·`w:overflowPunct` 조합으로 조정한다.
- 파일명: `out_path`가 없으면 `STYLE.md filename_pattern`(기본 `{title}_v{version}_{date:%Y%m%d}`)으로 `docs/_build/`에 저장. 제목의 공백은 `_`, 파일 시스템 금지 문자는 제거.
- **템플릿 모드**(`template_docx`): 회사 양식 docx를 `Document(template)`로 열어 스타일·머리글/바닥글·구역 설정(용지·여백)·번호 체계를 그대로 두고 **본문 요소만 제거**(`body`의 `w:p`·`w:tbl`, 마지막 `w:sectPr`은 유지)한 뒤 우리 블록을 붙인다. 스타일 이름은 `layout_map.docx_styles`(예: `{"h1": "제목 1", "body": "본문", "table": "표 스타일"}`)로 매핑하고, 없으면 우리 스타일을 새로 추가한다. 템플릿에 표지가 있고 본문에 `{{title}}` `{{date}}` `{{author}}` `{{version}}` `{{org}}` `{{security}}` 자리표시자가 있으면 frontmatter 값으로 치환하고 우리 표지는 만들지 않는다. 테마 색은 표·구성도·마커에만 쓴다(양식의 글자색·머리글은 그대로).
- 함정: ① `w:eastAsia` 미지정 시 한글이 다른 폰트로 나온다 ② 목차 필드는 Word가 열 때 갱신하므로 LibreOffice 미리보기에는 비어 보일 수 있다(경고에 명시) ③ `add_picture` 폭은 본문 폭(`page - margins`)을 넘지 않게 ④ 표 안 문단의 `space_after`를 0으로 ⑤ 빈 문단으로 여백을 만들지 않는다.

### 10.6 pptx 렌더링 규칙과 레이아웃 10종

기본 모드(템플릿 없음): `Presentation()`에 16:9 크기 설정, 빈 레이아웃(index 6)에 도형을 직접 그린다. 모든 좌표는 테마 치수에서 계산.

공통 프레임: 상단 0.5in 여백 → 슬라이드 제목(`#`, title_pt, title_color) → 그 아래 헤드 메시지(`##`, headline_pt, bold, headline_color, 최대 2줄, 폭 = 슬라이드 폭 - 2 margin) → `accent_bar`면 헤드 메시지 아래 primary 0.03in 가로줄 → 본문 영역(헤드 메시지 아래 0.3in부터 바닥글 위 0.4in까지) → 바닥글(왼쪽 `footer`, 가운데 `source`, 오른쪽 쪽번호 `n / N`, footer_pt, ink_subtle).

| 레이아웃 | 본문 배치 |
|---|---|
| `cover` | 왼쪽 primary 세로 띠(0.35in), 제목(headline_pt+14, primary), 부제, 조직·작성자·일자, `security` 우상단 |
| `agenda` | 왼쪽 번호(primary 원 대신 primary 굵은 숫자) + 제목 목록, 최대 8개, 2열 자동 |
| `section` | 큰 번호 + 섹션 제목, primary 배경 없음(흰 바탕 + primary 글자) |
| `message` | 글머리표 본문(body_pt, 줄 간격 1.3, 불릿 기호 `·` 대신 짧은 primary 대시 도형), 2단계까지 |
| `two-col` | `<!-- col -->` 기준 좌우 48%씩. 각 열 첫 줄이 `###`이면 열 제목 |
| `diagram` | 구성도 도형을 본문 영역에 맞춰 스케일(비율 유지), 노트가 있는 노드는 작은 캡션 |
| `table` | 표 본문 폭 100%, 헤더 행 primary 채움·흰 글자, 본문 table_pt, 짝수 행 surface, "검토 의견" 열은 폭 30% |
| `timeline` | 좌측 항목 라벨, 우측 기간 막대, 월/주 눈금, 오늘 세로선(date 기준) |
| `chart` | ` ```chart ` 블록을 네이티브 차트로 본문 영역 폭 100%(두 번째 블록이 있으면 좌우 2개). 제목은 차트 위 캡션(caption_pt), 출처는 바닥글 가운데. 헤드 메시지가 차트의 결론을 말한다("A안이 3년 TCO 32% 낮다") |
| `image` | `![]()` 1장을 본문 영역에 맞춤 + 캡션 |
| `closing` | 헤드 메시지(요청·결정 사항) + 글머리표 + 하단 연락처(footer) |

템플릿 모드(`template_pptx`): `Presentation(template)`로 열고 기존 슬라이드를 모두 제거(`sldIdLst`에서 rel 포함 삭제), `layout_map`으로 레이아웃 선택, placeholder(`idx`)에 텍스트를 넣고 부족한 요소는 도형으로 보충. 마스터의 색·폰트를 그대로 두고 우리 테마 색은 도형(구성도·표)에만 쓴다. 매핑이 없는 레이아웃은 템플릿의 "제목 및 내용"류로 폴백하고 경고.

함정: ① 한글 폰트는 run마다 `a:latin`과 **`a:ea`** 둘 다 지정하고 `a:rPr lang="ko-KR"`을 넣는다(맞춤법 밑줄·자동 줄바꿈 규칙이 한국어로 적용됨). 한글 어절 잘림은 `a:pPr eaLnBrk="1" hangingPunct="1"`로 시작하고 `[확인 필요]` PowerPoint 2021 실측으로 확정 ② 텍스트 상자 `word_wrap=True`, `auto_size=NONE`, 넘침은 렌더러가 글자 수로 추정해 경고(S9·S10이 사전에 막는다) ③ 화살촉은 XML(`a:tailEnd`) ④ 표 스타일의 기본 밴딩은 `tblPr` 속성으로 끄고 셀마다 채움을 지정 ⑤ 발표자 노트는 `notes_slide.notes_text_frame` ⑥ 도형 이름에 id를 넣는다 ⑦ 슬라이드 번호는 텍스트 상자로 계산(필드 미사용).

### 10.7 미리보기

`soffice --headless --convert-to pdf --outdir <tmp> <file>` → `pdftoppm -png -r <dpi> -f a -l b`(있으면) 또는 `soffice --convert-to png`(첫 장만). 탐색 경로: `SOFFICE_PATH` → PATH → `C:\Program Files\LibreOffice\program\soffice.exe` → `/usr/bin/soffice` → `/Applications/LibreOffice.app/Contents/MacOS/soffice`. 없으면 `available:false`와 설치 안내. 결과 PNG 경로 목록 반환. 스킬은 이미지를 Read 도구로 본다.

### 10.8 추출 도구

- `docx_to_md`: 문단 스타일 이름(`Heading n`)→`#`, 목록 스타일→`-`, 표→GFM 표, 그림→`![그림](추출경로)`, 머리글/바닥글 텍스트를 frontmatter 후보로. 구조 요약 포함.
- `pptx_to_md`: 슬라이드별 `# 제목`, 본문 placeholder→글머리표, 표→GFM, 노트→`<!-- note -->`, 레이아웃 이름 주석. 회사 덱의 관용 구조를 스킬이 학습하는 용도.
- `theme_from_pptx`: §9.2. 색은 `srgbClr`·`sysClr(lastClr)` 처리. `accent1`→`primary`, `accent2`→`accent`, `dk1`→`ink`, `lt2`→`surface`, `hlink`→`action`로 초안 매핑, 나머지 기본값 유지, `warnings`에 매핑 근거.

### 10.9 CLI와 종료 코드

`python -m docgen <명령> … [--json]`. 성공 0, DSL 오류 2(파일:줄 + 규칙), 렌더 실패 1, 외부 도구 없음 3(미리보기만). DSL 오류 메시지는 "무엇을 어떻게 고치라"까지 쓴다(예: `deck.md:41 슬라이드 '대안 비교'에 헤드 메시지(##)가 없습니다. 주장 문장 1개를 ## 로 추가하세요`).

---

## 11. 하네스 세팅 (저장소와 설치되는 실제 파일)

### 11.1 저장소 구조

```
ai-work-skill/
├── .claude-plugin/
│   ├── plugin.json                # name, version, description, author, skills "./skills/", mcpServers "./.mcp.json"
│   └── marketplace.json           # plugins:[{name:"ai-work-skill", source:"./"}]
├── .mcp.json                      # docgen, litellm-ops (uv run --project ${CLAUDE_PLUGIN_ROOT}/mcp/…)
├── skills/
│   ├── ai-init/SKILL.md
│   ├── doc-write/{SKILL.md, references/{writing-rules-ko,doc-types,korean-format,preflight-doc}.md}
│   ├── deck-write/{SKILL.md, references/{slide-rules,layouts}.md}
│   ├── fastapi-service/{SKILL.md, assets/service/…, scripts/{scaffold,route_table}.py}
│   ├── gitlab-ci/{SKILL.md, assets/{gitlab-ci.yml, merge_request_templates/, issue_templates/, CODEOWNERS}, scripts/ci_lint.py, references/{pipeline-recipes,deploy-targets,gitlab-mcp-playbook,branching}.md}
│   ├── py-review/{SKILL.md, references/checklist.md}
│   ├── py-test/{SKILL.md, references/{pytest-conventions,llm-mocking}.md, scripts/test_gaps.py}
│   ├── py-refactor/{SKILL.md, scripts/import_graph.py}
│   ├── llm-gateway/{SKILL.md, assets/{config.example.yaml, compose.yaml, .env.example, client_example.py}, references/{azure,bedrock,vertex,vllm,observability,security,ops-runbook}.md}
│   ├── model-serving/{SKILL.md, scripts/{vram_estimate,bench_llm}.py, references/{vllm,quantization,sizing,alternatives}.md}
│   ├── ai-trend-brief/{SKILL.md, assets/{sources.yaml, brief-template.md}}
│   └── llms.txt
├── references/                    # 스킬 공용 (§8.12)
│   ├── writing-rules-ko.md
│   ├── python-conventions.md
│   └── arch-doc-types.md
├── themes/
│   ├── datasolution.json
│   └── theme.schema.json
├── templates/                     # /ai-init이 프로젝트에 복사
│   ├── STYLE.md
│   ├── doc_lint.py                # 훅 + CLI. 표준 라이브러리만
│   ├── py_format.py
│   ├── install.py                 # 설치기. 표준 라이브러리만
│   ├── settings.json
│   ├── CLAUDE.snippet.md
│   └── mcp.gitlab.snippet.json
├── mcp/
│   ├── docgen/{pyproject.toml, docgen/{__init__,__main__,server,core,parse,theme,docx_render,pptx_render,lint,preview,extract}.py, docgen/diagram/{layout,mermaid,pptx_shapes,png}.py, tests/, fixtures/}
│   └── litellm_ops/{pyproject.toml, litellm_ops/{__init__,__main__,server,core,validate}.py, tests/, fixtures/}
├── tests/                         # templates/·skills/scripts 테스트 (루트 pytest)
├── eval/{README.md, prompts/01…08.md, check_output.py, results.md}
├── docs/{PRD.md, traceability.md, research/sources-2026-09-04.md}
├── pyproject.toml                 # 루트: uv workspace + dev deps(pytest, ruff, jsonschema, PyYAML)
├── .python-version                # 3.12 (mcp/*). 훅·스크립트는 3.9 문법 유지
├── .github/workflows/ci.yml
├── CLAUDE.md                      # 구현자(Opus) 규약 (§11.9). PRD와 함께 이미 존재
├── .gitignore                     # .venv, __pycache__, docs/_build/, *.pptx·*.docx(fixtures 제외), .env
├── README.md · LICENSE(MIT) · NOTICE
```

루트 `pyproject.toml` 골격:
```toml
[project]
name = "ai-work-skill-dev"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = ["pytest>=8,<9", "pytest-cov>=5", "ruff>=0.6", "jsonschema>=4.20,<5", "PyYAML>=6,<7"]

[tool.uv.workspace]
members = ["mcp/docgen", "mcp/litellm_ops"]

[tool.pytest.ini_options]
testpaths = ["tests", "mcp/docgen/tests", "mcp/litellm_ops/tests"]
addopts = "-q --strict-markers --strict-config"
markers = ["deterministic: 어디서나 실행", "host_cli: claude CLI 필요", "manual: 사람·모델 필요, 자동 실행 안 함"]

[tool.ruff]
line-length = 100
target-version = "py39"          # templates/·skills/ 는 3.9 문법
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ASYNC"]
```

`skills/`가 단일 원천이다. 심링크 없음(Windows). 스킬 스크립트는 표준 라이브러리만 쓴다(플러그인 설치만으로 동작해야 하므로). 서드파티가 필요한 것은 전부 `mcp/` 아래 uv 프로젝트에 있다.

### 11.2 프로젝트에 설치되는 `.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit",
        "hooks": [ { "type": "command", "command": "python -X utf8 .claude/hooks/doc_lint.py --pre", "timeout": 5 } ] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write|MultiEdit",
        "hooks": [ { "type": "command", "command": "python -X utf8 .claude/hooks/py_format.py --post", "timeout": 40 } ] }
    ],
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python -X utf8 .claude/hooks/doc_lint.py --stop", "timeout": 20 } ] }
    ]
  }
}
```

`python` 부분은 설치기가 탐지한 실행기(`python` / `python3` / `py -3`)로 치환한다. `-X utf8`은 Windows cp949 콘솔에서 한글 stderr가 깨지는 것을 막는다. 기존 settings.json이 있으면 `hooks` 배열에 **병합**(같은 command면 건너뜀). `--no-python`이면 PostToolUse 항목을 넣지 않는다.

### 11.3 훅 I/O 계약

| 스크립트·모드 | 입력 (stdin JSON) | 동작 | 출력 |
|---|---|---|---|
| `doc_lint.py --pre` | `tool_name`, `tool_input.{file_path, content \| new_string \| edits[]}` | 대상이 산문 파일(§7.4)이면 H1~H8, 텍스트 파일이면 H9, Office 바이너리면 H10. `STYLE.md`는 파일 위치에서 프로젝트 루트(`CLAUDE_PROJECT_DIR`)까지만 올라가며 찾고, 없으면 no-op(exit 0) | 위반: stderr `[doc-lint] 차단: docs/x.doc.md (2건)\n  H1 dash  L12(편집 내)  —\n     → 범위는 ~, 구분은 ·\n…\n규칙: 우회 금지 …` + `exit 2`. 통과: 출력 없음, exit 0. 안티 데드락 통과: stdout `{"systemMessage": "…"}` |
| `doc_lint.py --stop` | `stop_hook_active`, `cwd` | `git diff --name-only HEAD` + untracked 중 산문 파일에 하드+소프트+체크리스트. `stop_hook_active`면 exit 0 | 발견: stdout `{"decision":"block","reason":"[doc-lint] 종료 전 점검 …(한 번만 지적합니다)"}`. 없음: `{"systemMessage":"[doc-lint] 변경 문서 n개, 위반 0건. 좋은 문서라는 뜻은 아닙니다. STYLE.md를 계속 따르세요."}` |
| `doc_lint.py --all [경로…]` | 없음 (CLI) | 경로(기본 저장소 전체)의 산문 파일에 하드+소프트. 리포트(파일별, 룰별 건수, 상투어 밀도 = 건수/1000자) | 하드 위반 있으면 exit 1 |
| `doc_lint.py --lint <파일> --json` | 없음 | 단일 파일 findings JSON (docgen `lint_doc`가 import해서 쓰는 것과 동일 함수 `lint(text, path, cfg, soft=True)`) | JSON |
| `py_format.py --post` | `tool_name`, `tool_input.file_path`, `tool_response` | §7.6 | 미해결 오류: stdout `{"decision":"block","reason":…}`. 그 외 없음 |

공통: 최상위 try/except → exit 0 + stderr 한 줄(세션을 깨지 않는다). `CLAUDE_PROJECT_DIR` 있으면 루트, 없으면 cwd. 128KB 초과 편집은 건너뜀. `git` 없으면 `--stop`은 exit 0. 모듈은 `lint`, `parse_frontmatter`, `load_config`, `is_prose_file`, `run_pre`, `run_stop`, `run_all`을 export하고 `if __name__ == "__main__": main()`.

### 11.4 `STYLE.md` frontmatter 스키마와 본문

```yaml
---
ai_work_skill: 0.1
org: 데이타솔루션 기술연구소        # 표지·머리글의 조직 표기
lang: ko
theme: datasolution                 # themes/<name>.json 이름 또는 프로젝트 내 JSON 경로
template_pptx: null                 # 회사 덱 템플릿 경로 (있으면 deck-write가 사용)
template_docx: null
office_font: 맑은 고딕               # docx/pptx 폰트. Pretendard 설치 환경이면 Pretendard
tone_doc: 서술식                     # 서술식(~다) | 경어(~습니다)   보고서·설계서 본문
tone_deck: 개조식                    # 개조식 | 서술식
date_format: "YYYY-MM-DD"           # 또는 "YYYY. M. D."
currency: 원                        # 원 | ₩
numbering: "1.1"                    # "1.1" | "가나다"
placeholder_marker: "[확인 필요]"
filename_pattern: "{title}_v{version}_{date:%Y%m%d}"   # 렌더 결과물 파일명
render_output_dir: docs/_build      # 렌더 결과물 기본 위치 (.gitignore)
services: []                        # 우리 서비스 목록 (ai-trend-brief 관련도 판단, 설계서 AS-IS 참조)
dash_policy: deny                   # deny | allow        (H1)
emoji_policy: deny                  # deny | allow        (H6)
exclaim_policy: deny                # deny | allow        (H7)
buzzword_policy: block              # block | warn        (H2, H3)
allow_terms: []                     # 오탐 방지 허용어 (예: ["최적의 방안"])
glossary: docs/glossary.md          # 선택
---
```

본문 6섹션(사람용, 설치기가 `org`·`tone` 값을 채운다):
1. **조직과 독자**: 이 프로젝트가 만드는 서비스 한 줄, 문서를 읽는 사람(결재권자/개발자/고객)과 그들이 문서에서 3초 안에 찾는 것. `ai-trend-brief`의 관련도 판단 기준도 여기(서비스 목록).
2. **문서 유형과 톤**: 유형별 톤·분량·필수 절 표(`references/doc-types.md`의 요약 링크). 덱은 개조식·헤드 메시지 규칙.
3. **표기 규칙**: 번호 체계, 날짜·기간, 숫자·단위·통화, 용어 병기(첫 등장 1회 `한글(영문)`), 고유명사 표기(제품명은 공식 표기), 존댓말 통일.
4. **구조 규칙**: 결론 먼저, 사실/추론/권고 구분 표현, 비교표 "검토 의견" 열, `[확인 필요]` 모음 절, 요약 반복 금지.
5. **시각 규칙**: 테마 이름과 팔레트 역할(원색은 테마 JSON에만), 표·그림 캡션, 구성도 노드 종류 6종, 덱 레이아웃 10종, 로고 위치.
6. **금지와 허용 예외**: 프로젝트 추가 금지 + 예외 표 `| 규칙 | 파일 | 이유 | 승인자 | 날짜 |`.

### 11.5 `CLAUDE.md` 스니펫 (프로젝트 CLAUDE.md에 멱등 추가, 마커 `## 문서·코드 규약 (ai-work-skill)`)

```md
## 문서·코드 규약 (ai-work-skill)
- 문서(설계서·보고서·가이드·런북·ADR·브리프)나 덱을 만들기 전에 @STYLE.md 를 읽고 `doc-write` / `deck-write` 스킬 절차를 따른다. 코드 전 한 줄 "문서 리드/덱 리드"를 선언한다.
- 문서는 `.doc.md`/`.deck.md`로 쓰고 docx·pptx는 `docgen`(MCP 또는 `python -m docgen`)으로만 렌더링한다. python-docx/python-pptx를 직접 호출하지 않는다. 색·폰트는 테마 JSON에만 있다.
- em-dash·상투어·이모지·느낌표·가짜 채움(홍길동/TBD)·시크릿은 훅이 차단한다. 차단되면 우회하지 말고 고친다. 모르는 값은 `[확인 필요]`.
- FastAPI 서비스는 `fastapi-service` 골격, CI는 `gitlab-ci` 템플릿, 테스트는 `py-test` 규약, 리뷰는 `py-review` 체크리스트를 따른다. LLM 호출은 LiteLLM 게이트웨이 경유만.
- LiteLLM 설정은 `config_validate` 통과 후에만 배포한다. 키·시크릿은 yaml에 쓰지 않는다.
- 🚫 절대: STYLE.md 무시 · 훅 비활성화 · Bash 리다이렉트로 문서 작성 · 렌더러 우회 · 시크릿 인라인 · 출처 없는 수치
- ⚠️ 먼저 묻기: 예외 마커 추가 · 테마 변경 · MR 코멘트 게시 · 게이트웨이 키 발급/차단 · 파이프라인 재시도
- ✅ 항상: 결론 먼저 · 사실/추론/권고 구분 · 표 마지막 열은 검토 의견 · 렌더 후 미리보기 1회 · 종료 전 preflight
```

(이 스니펫의 🚫⚠️✅ 세 글자는 CLAUDE.md에만 있고 산문 파일이 아니므로 H6 대상이 아니다. `CLAUDE.md`는 §7.4 스킵 목록에 추가한다.)

### 11.6 `install.py` 계약

```
python templates/install.py --target <dir> [--org "데이타솔루션 기술연구소"] [--tone 서술식|경어]
                            [--theme datasolution] [--template-pptx <pptx>] [--template-docx <docx>]
                            [--logo <png>] [--with-ui] [--ui-skill-set <경로>]
                            [--no-python] [--update] [--force] [--uninstall]
                            [--gitlab-url https://gitlab.example.com]
```

동작(순서대로, 각 단계 `✓`/`·` 로그):
1. 실행기 탐지: `python --version`, `python3 --version`, `py -3 --version` 순으로 시도해 3.9 이상인 첫 것을 `PY`로. 없으면 훅 명령을 `python`으로 쓰고 경고.
2. `.claude/hooks/doc_lint.py`, `py_format.py`(Python 프로젝트일 때) 복사(항상 갱신).
3. `--update`면 여기서 종료(STYLE.md·settings·CLAUDE·docs 보존).
4. `STYLE.md`: 없거나 `--force`일 때 템플릿 복사 + frontmatter의 `org`·`tone_doc`·`theme` 치환(`fillFrontmatter` 포팅).
5. `.claude/settings.json` 병합(`mergeSettings` 포팅, `PY` 치환).
6. `CLAUDE.md` 스니펫 멱등 추가(`appendSnippet` 포팅). `AGENTS.md`가 있으면 같은 스니펫 추가.
7. `docs/{arch,adr,deck,trends,assets,_build}/.gitkeep`, `docs/glossary.md`(헤더만 있는 표 `| 표준 표기 | 금지 표기 | 비고 |`), `.gitignore`에 `docs/_build/` 멱등 추가.
8. `.mcp.json`: `gitlab` 항목 병합(`--gitlab-url` 있으면 값, 없으면 `${GITLAB_URL}`).
9. `--logo`: `docs/assets/logo.png`로 복사. `--template-pptx/--template-docx`: `STYLE.md`의 `template_pptx`·`template_docx`에 경로를 기록만 한다(테마 추출은 `ai-init` 스킬이 docgen으로 수행).
9-1. `--uninstall`: `.claude/hooks/{doc_lint,py_format}.py` 삭제, `settings.json`에서 우리 command 항목만 제거, CLAUDE.md·AGENTS.md의 스니펫 블록 제거. `STYLE.md`·`docs/`·`.mcp.json`은 남긴다(데이터).
10. `--with-ui`: ui-skill-set 루트 탐색(§5.5) → `python -m docgen theme-export --tokens-css`가 가능하면(플러그인의 docgen 환경) 램프를 생성해 `node <ui>/templates/install.mjs --target . --mode operate --stack <감지> --hue blue` 실행 후 `tokens.css`의 accent 블록 치환. docgen 환경이 없으면 install.mjs만 실행하고 램프 치환은 안내로 대체.
11. "다음 단계" 출력: STYLE.md §1 채우기, `doc_lint --all docs/` 실행, GitLab MCP 인증(`/mcp`), `LITELLM_BASE_URL` 설정.

순수 함수(`merge_settings`, `fill_frontmatter`, `append_snippet`, `merge_mcp_json`, `detect_python`)는 export되어 `tests/test_install.py`가 검사한다. 파일 I/O는 `main()`에만.

### 11.7 플러그인 매니페스트와 `.mcp.json`

`.claude-plugin/plugin.json`: `{"name":"ai-work-skill","version":"0.1.0","description":"생성형 AI 서비스 개발 조직용 스킬 세트 …","author":{"name":"sgustjd2"},"homepage":…,"repository":…,"license":"MIT","keywords":["fastapi","gitlab","litellm","docx","pptx","korean","anti-slop"],"skills":"./skills/","mcpServers":"./.mcp.json"}`.

`.mcp.json`(플러그인 루트):
```json
{
  "mcpServers": {
    "docgen": {
      "type": "stdio", "command": "uv",
      "args": ["run", "--project", "${CLAUDE_PLUGIN_ROOT}/mcp/docgen", "python", "-m", "docgen.server"]
    },
    "litellm-ops": {
      "type": "stdio", "command": "uv",
      "args": ["run", "--project", "${CLAUDE_PLUGIN_ROOT}/mcp/litellm_ops", "python", "-m", "litellm_ops.server"],
      "env": {
        "LITELLM_BASE_URL": "${LITELLM_BASE_URL:-http://localhost:4000}",
        "LITELLM_MASTER_KEY": "${LITELLM_MASTER_KEY}",
        "LITELLM_API_KEY": "${LITELLM_API_KEY:-}",
        "LITELLM_OPS_ALLOW_WRITE": "${LITELLM_OPS_ALLOW_WRITE:-false}"
      }
    }
  }
}
```
전제: `uv`가 PATH에 있다(README 첫 줄에 설치 명령). 첫 실행 시 uv가 의존성을 동기화하므로 최초 1회 네트워크가 필요하다. 플러그인 없이 클론해서 쓰는 팀원은 README의 절대 경로 예시로 프로젝트 `.mcp.json`에 직접 넣는다.

### 11.8 배포

| 경로 | 명령 | 대상 |
|---|---|---|
| Claude Code 플러그인 | `claude plugin marketplace add sgustjd2/ai-work-skill` → `/plugin install ai-work-skill@ai-work-skill` | 팀 표준 |
| 클론 | `git clone … && /ai-init`(스킬 경로를 저장소 상대 경로로) | 오프라인·사내 GitLab 미러 |
| 벤더 CLI | `npx skills add https://github.com/sgustjd2/ai-work-skill --skill doc-write` | Cursor·Codex |

어느 경로든 실제 강제는 `/ai-init`이 프로젝트에 커밋한 훅과 STYLE.md가 한다.

### 11.9 저장소 루트 `CLAUDE.md` (구현자 규약)

이 저장소를 Claude Code로 열면 자동 로드되는 파일이다. PRD와 함께 이미 작성돼 있다. 내용: 이 저장소가 무엇인지 한 줄, 시작 전 읽을 것(`docs/PRD.md` §16, §13), 의존성 정책(`templates/`·`skills/*/scripts/`는 표준 라이브러리만, `mcp/*`만 서드파티, 새 의존성 금지), 원색 금지(렌더러·훅 소스에 hex 리터럴 0), 함수 export와 `main()` 분리, Windows 규약(`pathlib`, UTF-8, 심링크·bash·jq 금지), 검증 명령(`uv run pytest`, `python templates/doc_lint.py --all docs skills README.md`, `uv run ruff check .`), 커밋 메시지 접두사 `feat(FR-n):`, 마일스톤 종료 시 갱신할 파일(`docs/PRD.md` 상태 표, `docs/traceability.md`, README 상태 줄), 하지 않는 것(§16-11). 이 파일 자체는 `doc_lint` 스킵 대상(§7.4).

---

## 12. 테스트와 평가

### 12.1 단위 테스트 (pytest, 루트 `uv run pytest`)

| 대상 | 파일 | 최소 케이스 |
|---|---|---|
| doc_lint 룰 | `tests/test_doc_lint.py` | H1~H10·S1~S18 각각 양성 2·음성 2(음성에는 코드 펜스·인라인 코드·URL·frontmatter 안의 같은 문자열, H6의 관용 기호 ★☞☑, H9의 `sk-xxxxxxxxxxxxxxxxxxxxxxxx` 자리표시자 포함). 마커·정책 예외, `doc_lint: off`, 정책 파일 스킵, 안티 데드락, CLI 3모드 subprocess, Windows 경로(`\\`), S18 용어집 픽스처 |
| install | `tests/test_install.py` | settings 병합(기존 훅 보존·중복 방지), frontmatter 치환, 스니펫 멱등(CLAUDE.md·AGENTS.md), mcp 병합, `.gitignore` 멱등, 실행기 탐지(모의), `--update` 보존, `--uninstall` 후 잔여물 0 |
| py_format | `tests/test_py_format.py` | ruff 없음 → 무출력 exit 0, 모의 ruff 미해결 → block JSON, 비-py 파일 무시 |
| 스킬 스크립트 | `tests/test_scripts.py` | scaffold(옵션 조합 6개: 기본 / db / rag(→db 함의·pgvector) / jobs / auth / 전부, 생성 트리·치환·옵션 모듈 제거·`--force`, 생성 골격에서 `uv run pytest` 통과 1회), route_table(생성 골격에 대해 라우트 6개, `--md` 표 열 6개), test_gaps(픽스처 패키지), import_graph(순환 1개·레이어 위반 1개 픽스처), vram_estimate(알려진 모델 값 ±5%), ci_lint(로컬 YAML 문법 모드), prompts 로더(누락 변수 기동 실패) |
| 테마 | `tests/test_theme.py` | 스키마 검증, 렌더러 소스에 hex 리터럴 0개, tokens-css 램프 9단계·대비 4.5:1 |
| docgen | `mcp/docgen/tests/` | 파서(frontmatter·표·diagram/timeline/chart 블록·slide 분리·layout 추론), docx(스타일 6종 존재·eastAsia 폰트·wordWrap·머리글/바닥글 필드·표 헤더 음영·캡션 번호·마커 형광·목차 필드·기본 출력 경로와 filename_pattern, 생성물 재로드, **템플릿 모드**: 픽스처 양식의 스타일·머리글 유지 + 자리표시자 치환 + 본문 교체), pptx(슬라이드 수·레이아웃별 도형 존재·헤드 메시지 텍스트·`a:ea` 폰트·`lang`·화살촉 XML·노트·바닥글 번호·네이티브 차트 존재와 시리즈 색, 템플릿 모드 픽스처 1개), diagram(레이아웃 좌표 결정성·미그룹 노드·mermaid 문자열·PNG 생성·폰트 미탐지 폴백 코드 블록, `diagram_from_compose` 픽스처), extract(docx/pptx 픽스처 → md), theme_from_pptx(픽스처 theme1.xml), 경로 해석(`DOCGEN_PROJECT_DIR` 기준 상대 경로), lint 단일 구현(assert `docgen.lint.lint is doc_lint.lint`) |
| litellm_ops | `mcp/litellm_ops/tests/` | §9.1 |

테스트는 프레임워크 없이도 읽히게 단순하게. agent-harness 규약대로 마커 `deterministic`(기본), `host_cli`, `manual`. 네트워크 없음.

### 12.2 골든 프롬프트 (`eval/prompts/`)

각 파일: 붙여 넣을 프롬프트 · 유도되는 슬롭 · 기대 · 고정 요소 · 자동 검사. 3회 실행해 구조 일치를 본다.

| # | 프롬프트 (요지) | 유도되는 슬롭 | 기대 | 자동 검사(`check_output.py`) |
|---|---|---|---|---|
| 01 | LLM 게이트웨이 도입 설계서 docx (AS-IS/TO-BE, 구성도, 단계별 계획) | em-dash, "혁신적", 굵은 라벨 목록, 3항목 리스트, 구성도를 말로 설명 | 문서 리드 1줄, 설계서 골격, diagram 블록, 표에 검토 의견 열, 마커 | `doc_lint --all` 0, docx 열림, 테마 밖 색 0, 목차·머리글·개정이력 존재 |
| 02 | 01을 경영진 10장 덱으로 | 글머리표 벽, 제목만 있는 슬라이드, 감사합니다 장 | 장마다 헤드 메시지, ≤ 6줄, 구성도 도형, 마지막 장 요청 사항 | 슬라이드 10±2, S9~S12 0, 테마 밖 색 0, 도형 이름에 노드 id |
| 03 | 문서 요약 API 서비스 골격 (LiteLLM 경유, 테스트·Docker·CI) | 벤더 SDK 직접 호출, 설정 하드코딩, 테스트 없음 | scaffold 결과, pytest 통과, Dockerfile, .gitlab-ci.yml | `uv run pytest` 0, `docker build` 0(도커 있을 때), `ci_lint` 통과, `import_graph` 위반 0 |
| 04 | 이 MR 리뷰 (픽스처 diff: 블로킹 호출·시크릿·테스트 누락) | 칭찬 서론, 근거 없는 승인 | 판정·block 3건(정확히 그 3개)·파일:줄 | 리뷰 형식 파싱, 3개 항목 검출 |
| 05 | Azure 2리전 + Bedrock 폴백 + 팀별 예산 config.yaml | 키 인라인, 폴백 오타, 헬스체크 누락 | config_validate 통과, `.env.example` 동기 | `config-validate` error 0 |
| 06 | 이번 주 AI 트렌드 브리프 | 링크 나열, "혁신적", 출처 없음 | 5~7항목, 항목마다 URL·날짜·영향·적용 | `doc_lint` 0, 항목마다 `http` 존재, 형식 파싱 |
| 07 | 신규 입사자 개발 가이드 (로컬 환경·브랜치·배포) | "알아보겠습니다", 이모지 제목, 요약 반복 | Diataxis how-to 순서, 명령 블록, 존댓말 통일 | `doc_lint` 0, S16 0 |
| 08 | services 패키지 순환 import 정리 계획 | 한 번에 다 옮기기, 동작 변경 섞기 | import_graph 전후, ADR, 단계별 검증 | ADR 파일 존재, 순환 0 |

`eval/check_output.py <run_dir>`: docx/pptx를 unzip해 `srgbClr val`·`w:color w:val`·`w:shd w:fill`을 수집하고 테마 팔레트(+흰·검·회색 계열 3개) 밖 값을 보고, `.deck.md`에 S9~S12를 적용, 산문 파일에 `doc_lint --all`. 종합 `PASS/FAIL`.

### 12.3 성공 지표

| 지표 | 목표 | 측정 |
|---|---|---|
| 하드 룰 위반 도달률 | 커밋된 문서에서 0 | CI `doc_lint --all docs/` |
| 테마 밖 색 | 생성 docx·pptx에서 0 | `check_output.py` |
| 구조 일관성 | 골든 01·02·03 3회 실행에서 절 순서·표 열·레이아웃·디렉터리 동일 | 수동 + check_output |
| 스킬 발견률 | 프롬프트 10개 중 ≥ 9 자동 로드 | 수동 |
| "회사 문서 같다" | 리뷰어 3명 5점 척도 ≥ 4 (01·02·07) | 수동 |
| 골격 건전성 | scaffold → pytest·docker build·ci lint 통과 ≤ 10분 | 골든 03 |
| config 검증 | V1~V8 픽스처 정확도 100%, 실제 config 오탐 ≤ 1건 | 테스트 + 도그푸딩 |
| 차단 정확도 | 하드 룰 오탐 ≤ 5% (도그푸딩 1주) | 로그 |

---

## 13. 마일스톤

| | 산출물 | 완료 조건 |
|---|---|---|
| **M0 골격 (완료)** | FR-1~8: STYLE.md, 테마, `doc_lint --pre`, 테스트, install.py, ai-init, doc-write(md까지), 스니펫 | 완료 2026-09-04. 실제 프로젝트 설치·차단 확인, 자기 검사 하드 0, `uv run pytest` 72 PASS. 소프트 룰(S1~S18)과 `--stop`/`--all`도 함께 구현(FR-18 선행), py_format(FR-25) 선행 |
| **M1 문서 생성 (완료)** | FR-9~19, 36: docgen 파서·docx·pptx·diagram·차트·MCP·CLI·preview·추출, deck-write, arch-doc-types | 완료 2026-09-04. docgen 53 테스트 PASS, 설계서 docx·게이트웨이 덱 pptx 실제 렌더(복구 없이 열림), 템플릿 모드 픽스처 검증. 골든 01·02 는 M4 eval 에서 실측 |
| **M2 개발 (완료)** | FR-20~26, 35: fastapi-service+scaffold(7옵션)+route_table, gitlab-ci+ci_lint, py-test+test_gaps, py-review, py-refactor+import_graph, python-conventions, genai-patterns | 완료 2026-09-04. 스크립트 10테스트 PASS, 생성 골격이 Windows 에서 pytest 통과(base 8, sse 9). 골든 03·04·08 은 M4 eval 에서 실측 |
| **M3 LLM 운영 (완료)** | FR-27~30: llm-gateway(assets+참조 7종), litellm-ops MCP(12툴, config_validate V1~V8, 쓰기 게이트), model-serving(vram_estimate·bench_llm), ai-trend-brief | 완료 2026-09-04. litellm_ops 21 + 스크립트 5 테스트 PASS(httpx MockTransport), config.example 검증 통과. 실제 LiteLLM 대상 `gateway_health`·`test_completion` 은 게이트웨이 확보 시(부록 F-4). 골든 05·06 은 M4 eval |
| **M4 배포** | FR-31~34: 매니페스트, README, eval 기준선, ui-skill-set 연동, 저장소 CI | 다른 PC에서 README만 보고 설치·골든 01 재현. `results.md`에 기준선 기록 |

권장 순서는 M0 → M1 → M2 → M3 → M4. M1과 M2는 독립이라 병렬 가능. 각 마일스톤 끝에 `docs/PRD.md` 상태 표와 이 표를 갱신한다.

---

## 14. 결정 필요 사항

각 항목에 추천값이 있다. 답이 없으면 추천값으로 진행한다.

| # | 결정 | 선택지 | 추천 | 이유·영향 |
|---|---|---|---|---|
| D1 | 훅·설치기 런타임 | Python 표준 라이브러리 / Node(ui-skill-set과 동일) | **Python** | 대상 조직이 Python 조직이라 Node보다 존재가 확실. `doc_lint`를 docgen이 그대로 import해 단일 구현. Windows는 실행기 탐지로 대응 |
| D2 | 기본 테마 값 | 웹사이트 CSS 변수 실측(부록 A) / CI 안내의 CMYK 환산 / 공식 템플릿 대기 | **실측값** | 합류 후 공식 pptx 템플릿을 `theme_from_pptx`로 추출해 덮는다. 그때까지 실측값이 가장 실제에 가깝다 |
| D3 | Office 문서 폰트 | 맑은 고딕 / Pretendard | **맑은 고딕** | 수신자 PC에 없는 폰트는 대체되어 레이아웃이 깨진다. 사용자의 기존 결재 문서도 맑은 고딕. 웹 UI만 Pretendard |
| D4 | pptx 엔진 | python-pptx(네이티브 도형) / html2pptx(Playwright) | **python-pptx** | 편집 가능한 도형, 회사 템플릿 마스터 재사용, 의존성 가벼움 |
| D5 | 문서 기본 톤 | 서술식(~다) / 경어(~습니다) | **서술식**(보고서·설계서), 고객 문서만 경어 | 사용자의 review-report-writer 예시가 서술식. STYLE.md에서 바꿀 수 있다 |
| D6 | GitLab 연동 | 공식 MCP(HTTP·OAuth) / 커뮤니티(PAT) | **공식**, 폴백 커뮤니티 | 유지보수 주체가 GitLab. 인스턴스 버전·beta 설정에 따라 폴백 |
| D7 | MCP 전송 | stdio / HTTP | **stdio** | 로컬 도구. 팀 공유가 필요해지면 FastMCP의 HTTP 전송으로 같은 코드 배포 |
| D8 | litellm-ops 쓰기 | 항상 허용 / 환경변수 게이트 / 금지 | **환경변수 게이트**(기본 읽기 전용) | 키 발급·차단은 되돌리기 어렵다 |
| D9 | 구성도 자동 배치 | 열 기반 단순 배치 / 그래프 레이아웃 라이브러리 | **단순 배치**, 20노드 초과 시 경고 | 아키텍처 구성도는 대부분 10노드 이하. 의존성 0 유지 |
| D10 | 라이선스 | MIT / Apache-2.0 | **MIT** + NOTICE(ui-skill-set 로직 포팅 출처) | 배포 |
| D11 | 렌더 결과물 위치 | 원본 옆에 커밋 / `docs/_build/`(gitignore) + 제출본만 `--out` | **`docs/_build/`** | 바이너리 diff 방지, 원본(.doc.md)이 단일 진실. 결재용 제출본은 `filename_pattern`으로 이름 붙여 공유 드라이브로 |
| D12 | 플러그인 레벨 훅(`hooks/hooks.json`) 동봉 | 동봉(설치 즉시 작동) / 미동봉(`/ai-init`이 프로젝트에 커밋) | **미동봉** | 프로젝트 훅과 이중 발화하면 같은 차단 메시지가 두 번 나온다. 플러그인 없는 팀원도 같은 검사를 받아야 하므로 프로젝트 커밋이 원칙(ui-skill-set과 동일) |
| D13 | 차트 렌더링 범위 | pptx 네이티브만 / docx에도 이미지 | **pptx 네이티브만**, docx·md는 표 | 이미지 차트는 matplotlib 의존성과 색 오탐을 부른다. 문서에서는 표가 더 정확하다 |
| D14 | Office 어절 줄바꿈 속성 | `w:wordWrap 0` + `eaLnBrk` / 미지정 | **지정 후 실측 확인** | 한글 문서에서 단어가 잘리면 "기계 티"가 난다. 확정값은 M1 픽스처 실측으로 |

---

## 15. 리스크와 완화

| 리스크 | 완화 |
|---|---|
| H2·H4 오탐(정당한 "극대화", 인용문 속 상투어) | `allow_terms`, 파일 마커, 인용 블록(`>`)은 소프트로 강등, 3회 연속 차단 통과. 도그푸딩 1주 후 목록 조정 |
| H6가 한국 문서 관용 기호(※·★·☞·☑)를 이모지로 차단 | 허용 집합 제외(§7.1). 테스트에 음성 케이스. 새 기호가 필요하면 `allow_terms`가 아니라 허용 집합에 추가(PR) |
| H9가 `.env.example`의 자리표시자를 차단 | 자리표시자 패턴 제외(§7.1). 진짜 키 모양(무작위 20자 이상)만 잡는다 |
| MCP 서버의 cwd가 프로젝트가 아님 | `DOCGEN_PROJECT_DIR=${CLAUDE_PROJECT_DIR}` 주입 + 절대 경로 반환(§9). 스킬은 절대 경로로 호출 |
| 회사 양식 docx의 본문 제거가 표지·목차까지 지움 | 템플릿 모드는 자리표시자 유무로 표지 보존을 판단하고, 제거 전 요소 수를 `warnings`에 기록. 픽스처 2종(표지 있음/없음) |
| 훅 잔소리 → 모델이 문서를 짧고 밋밋하게 씀 | 하드 9개만 즉시, 나머지 Stop 1회. 소프트 룰은 파일당 1건으로 합쳐 보고 |
| Windows에서 `python`이 Store 별칭이거나 없음 | 설치기 실행기 탐지, 실패 시 경고 + 훅은 no-op(세션은 안 깨짐) |
| python-pptx 한글 폰트가 대체됨 | `a:ea` 지정 테스트, 미리보기로 확인. 폰트 없는 PC는 D3의 맑은 고딕으로 대부분 해결 |
| LibreOffice 없음 | 미리보기는 선택. 없으면 안내만. 구조 검사는 XML로 |
| 회사 템플릿의 placeholder 구조가 예측과 다름 | `layouts` 툴로 확인 → `layout_map` 수동 보정. 매핑 실패 시 폴백 레이아웃 + 경고 |
| GitLab MCP가 beta라 툴 이름·인증이 바뀜 | 스킬은 툴 이름을 하드코딩하지 않고 탐색. 커뮤니티 서버 폴백 문서화 |
| LiteLLM 엔드포인트·응답 형태 변경 | 툴별 응답 파싱을 방어적으로(없는 필드는 null), 픽스처를 버전과 함께 기록. 폴백 엔드포인트(`/spend/logs`) |
| FastMCP 4 API 차이 | 서버 계층을 얇게(데코레이터 10줄). core는 프레임워크 무관 |
| 회사 정보 유출 | 저장소에 조직 실명·로고·URL 없음(`STYLE.md`·env·`--logo`로만). H9가 시크릿 차단. 실험 기록에 env 값 금지(agent-harness 규약) |
| 룰이 새로운 단일 문체가 됨 | 룰은 "기본값 거부"이지 문체 강제가 아니다. STYLE.md §1이 프로젝트별 독자·목적을 갖고, 톤은 설정값이다 |

---

## 16. Opus 구현 지침

이 절은 구현자에게 직접 말한다.

0. **시작 전**: 저장소 루트 `CLAUDE.md`(§11.9)와 `docs/research/sources-2026-09-04.md`(외부 사실의 출처·확인일)를 읽는다. 외부 API·라이브러리 동작이 이 PRD와 다르면 PRD가 아니라 현재 문서를 따르고, 차이를 `docs/research/`에 한 줄 기록한다.
1. **순서**: §13 마일스톤 순서. 각 FR은 "코드 + 테스트 + 이 PRD의 완료 조건 확인" 세 가지가 끝나야 완료다. FR 번호를 커밋 메시지 접두사로 쓴다(`feat(FR-3): doc_lint --pre`). 부록 E 추적표의 해당 행에 테스트 파일명과 결과를 채운다(`docs/traceability.md`).
2. **먼저 읽을 파일**(포팅 대상): `E:\workspace\ui-skill-set\templates\design-lint.mjs`(훅 구조 전체), `install.mjs`(병합 함수 3개), `skills\ui-design\SKILL.md`(스킬 문체와 길이), `docs\PRD.md`(§8.3 I/O 계약 표기법). `E:\workspace\품의서\.claude\skills\review-report-writer\references\writing-rules.md`(그대로 흡수). 파일을 복사하지 말고 구조를 옮긴다.
3. **의존성 정책**: `templates/`와 `skills/*/scripts/`는 표준 라이브러리만(테스트가 import 목록을 검사한다). `mcp/*`만 서드파티. 새 의존성은 이 PRD §9.2 목록 밖이면 추가하지 않는다.
4. **원색 금지**: 렌더러·훅 소스에 hex 리터럴 없음. 테마 JSON만. 테스트가 grep으로 강제한다.
5. **함수 export**: 훅·설치기·스크립트는 순수 함수와 `main()`을 분리한다. 테스트는 순수 함수를 부른다. subprocess 테스트는 모드당 1개.
6. **오류 처리**: 훅은 절대 세션을 깨지 않는다(최상위 catch → exit 0). MCP 툴은 `ToolError`에 코드와 사람이 읽는 이유. 렌더러의 DSL 오류는 파일:줄과 고치는 법.
7. **Windows**: 경로는 `pathlib`, 출력은 UTF-8(`sys.stdout.reconfigure(encoding="utf-8")`), 심링크·`bash`·`jq` 사용 금지, 테스트는 `tmp_path`.
8. **스킬 문체**: 한국어, 명령형, "왜"를 한 줄씩. 스킬에 사실을 복사하지 않는다(테마·STYLE.md·references를 가리킨다). description은 §8의 것을 그대로 쓴다. 각 SKILL.md에 플러그인 경로와 클론 경로 두 가지 실행 예시를 적는다.
9. **문서 예시 파일**: `mcp/docgen/fixtures/`에 `.doc.md` 2개(설계서·검토보고서)와 `.deck.md` 1개(10장)를 두고, 테스트와 README가 그것을 렌더링한다. 예시 내용은 이 PRD의 §10.1~10.2 것을 확장하되 회사 실명·실제 고객명은 쓰지 않는다.
10. **자기 검증**: 이 저장소의 `docs/`·`README.md`·`skills/**/SKILL.md`에 `doc_lint --all`을 돌려 하드 위반 0을 CI에서 확인한다(룰 정의를 담은 파일은 `doc_lint: off`). 만든 도구를 자기 문서에 쓴다.
11. **하지 않는 것**: 이 PRD에 없는 스킬·툴 추가, 프롬프트 평가 프레임워크, 컴포넌트 라이브러리, K8s 매니페스트 생성기, 자체 GitLab MCP, 회사 로고·실명 커밋.
12. **완료 보고**: 마일스톤마다 `docs/PRD.md` 상태 표와 §13 표를 갱신하고, 테스트 수·골든 결과·미해결 결정을 README 상태 줄에 쓴다(ui-skill-set README 형식).

---

## 부록 A. 데이타솔루션 팔레트 (실측 2026-09-04)

출처: `https://www.datasolution.kr` CSS 커스텀 속성(`common.css` `:root`), CI 안내 페이지(`/prcenter/ci`). 공식 브랜드 가이드 문서는 미확보이므로 합류 후 공식 템플릿으로 교체한다(D2).

| 역할 | 값 | 출처 변수 | 비고 |
|---|---|---|---|
| primary | `#133F91` | `--primary` | CI 딥블루(C100 M85 K10)에 대응. 제목·헤드 메시지·표 헤더 글자 |
| primary_dark | `#002B96` | 실측 `rgb(0,43,150)` | hover·강조 배경 |
| accent | `#00AEEF` | `--primary-02` | CI 메인 블루(C100). 구성도 LLM 노드·강조 경계·타임라인 교대색 |
| action | `#1366E3` | `--blue-main` | 링크·버튼(웹). UI 액센트 램프의 기준 |
| blue 보조 | `#1A73E8` `#007FFF` `#0071C5` `#0047AB` | `--blue-01…04` | 사이트 내부 변형. 문서에서는 쓰지 않음 |
| ink | `#222222` | `--black-01` | 본문 |
| ink_muted | `#666666` | 실측 | 보조 텍스트 |
| ink_subtle | `#999999` | 실측 | 캡션·바닥글 |
| line | `#CDCDCD` | `--light-gray` | 표 테두리 |
| surface | `#F7F7F7` | `--white-01` | 표 헤더 배경·코드 배경 |
| surface_alt | `#F6F7FB` | 실측 | UI 노드 채움 |
| 상태색 | positive `#0F8A5F` · warning `#B26A00` · critical `#C0392B` | 이 PRD 제안 | 사이트에 없음. 대비 4.5:1 이상으로 고른 값. 표의 상태 표기에만 |
| 웹 폰트 | Pretendard | `body font-family` | 사이트 본문 |
| Office 폰트 | 맑은 고딕 | 사용자 기존 문서 | D3 |

CI 안내 원문 요지: 전체 블루는 "고객·직원과의 신뢰"와 "데이터 기반 블루오션 시장 집중"을, 상단 블루는 "푸른 하늘", 하단 딥블루는 "깊은 심연"을 뜻한다. 심볼마크의 형태·색 임의 변경 금지. 로고 이미지는 저장소에 포함하지 않는다.

## 부록 B. 금지 표현 사전 (`references/writing-rules-ko.md`의 원본)

정규식은 §7.1·§7.2. 이 부록이 사람이 읽는 원본이고, `references/writing-rules-ko.md`는 이것을 옮긴 것이다. 테스트는 B.2~B.4의 어휘 집합이 H2~H5·S3~S7 정규식에 전부 매치되는지 확인한다(사전과 규칙의 드리프트 방지).

### B.1 검토보고서 상투 문장 11개 (review-report-writer 원본, 그대로 흡수)

효율성을 극대화할 수 있습니다 · 시너지를 창출할 수 있습니다 · 경쟁력을 강화할 수 있습니다 · 다양한 활용이 가능합니다 · 안정적인 운영이 가능합니다 · 향후 확장성이 우수합니다 · 최적의 솔루션입니다 · 업무 생산성을 향상할 수 있습니다 · 지속적인 고도화가 가능합니다 · 혁신적인 서비스를 제공할 수 있습니다 · 전반적으로 우수한 것으로 판단됩니다.

대체 원칙: "무엇이 좋아지는가"가 아니라 **"구체적으로 무엇을 할 수 있게 되는가"**를 쓴다. 대상 → 현재 한계 → 도입 후 가능한 작업 순서로 연결한다.

### B.2 한국어 마케팅 상투어 (H2 차단)

혁신적 · 차세대 · 획기적 · 최첨단 · 패러다임 · 게임 체인저 · 시너지 · 극대화 · 최적의 솔루션/방안/선택 · 경쟁력 강화/확보 · 효율성 극대화/제고/향상 · 생산성 향상 · 다양한 활용이 가능 · 안정적인 운영이 가능 · 확장성이 우수 · 지속적인 고도화가 가능 · 전반적으로 우수한 것으로.

감시 목록(차단하지 않지만 문단에 2개 이상이면 다시 쓴다, S4): 다양한 · 효과적으로 · 체계적으로 · 적극적으로 · 원활하게 · 안정적으로 · 지속적으로 · 효율적으로 · 유연한 · 강력한 · 스마트한 · 손쉽게.

### B.3 영어 AI 어휘 (H3 차단)

seamless(ly) · leverage · cutting-edge · state-of-the-art · game-changer/changing · delve · tapestry · unleash · supercharge · next-gen(eration) · best-in-class · revolutionize · synergy · paradigm.

감시 목록(소프트, 문장당 1개 이상이면 다시 쓴다): robust · holistic · empower · streamline · harness · navigate · landscape · realm · journey · elevate · foster · pivotal · crucial · comprehensive · ever-evolving · in the world of.

### B.4 블로그 문체 관용구 (H4·H5 차단, S3 지적)

한국어: ~에 대해 알아보겠습니다 · ~를 살펴보겠습니다 · ~하는 것이 중요합니다 · 주목할 만한 점은 · 다음과 같은 이점/장점/특징이 있습니다 · (문단 첫머리) 결론적으로 · 요약하자면 · 종합하자면 · 마무리하자면 · 정리하자면.
영어: in conclusion · it is important/worth noting · let's dive/explore/delve · in today's fast-paced/rapidly/ever · as an AI · I hope this helps · great question · certainly! · in summary · to summarize · overall,.

### B.5 서식 신호 5개와 대체

| 신호 | 왜 기계 티인가 | 대신 |
|---|---|---|
| em-dash(—) 구분 | 한국 문서에는 없는 문장부호. 모델의 영어 습관 | `,` `·` 괄호 줄바꿈. 범위는 `~` |
| 이모지(제목·글머리) | 기업 문서 관례에 없음 | 텍스트 제목. 상태는 단어(완료/진행/보류). 강조는 ※ ★ ☞ |
| `**굵은 라벨**: 설명` 목록 | ChatGPT 기본 서식 | 문장으로 풀거나, 표(항목·내용·검토 의견) |
| 항목 정확히 3개 | 모델이 "충분히 많고 적당히 짧다"고 학습한 수 | 실제 개수. 2개면 2개, 5개면 5개 |
| 마지막 요약 문단("결론적으로…") | 앞 내용 반복. 정보 0 | 삭제. 남길 것은 새 판단(권고)과 다음 행동만 |

### B.6 "대신 이렇게" 10쌍 (유형별)

| # | 유형 | 나쁜 예 | 좋은 예 |
|---|---|---|---|
| 1 | 설계서 개요 | 본 문서는 LLM 게이트웨이 도입 방안에 대해 알아보겠습니다. 게이트웨이는 다양한 이점을 제공하며 운영 효율성을 극대화할 수 있습니다. | LiteLLM 프록시를 사내 공용 LLM 게이트웨이로 도입한다. 팀별로 흩어진 API 키 12개를 엔드포인트 하나로 모으고, 모델 교체를 코드 수정 없이 설정 변경으로 끝내는 것이 목표다. 10월 파일럿, 12월 전환을 권고한다. |
| 2 | 비교표 검토 의견 열 | LiteLLM: 오픈소스, 기능 다양 / Kong: 상용, 안정적 | LiteLLM이 적합. 폴백·예산·가상 키가 설정 파일 하나로 끝나 운영 인력 1명으로 가능하다. Kong은 API 게이트웨이를 이미 운영하는 조직에만 유리하다(우리는 없음). |
| 3 | 위험 | 다양한 리스크가 존재할 수 있으나 체계적인 관리를 통해 최소화할 수 있습니다. | 제공자 장애 시 폴백 모델의 응답 형식이 달라 후처리 오류가 난다(파일럿에서 2건). 대응: 폴백 모델도 골든 테스트에 넣고, 장애 30분 초과 시 담당자 알림. |
| 4 | 가이드 단계 | 먼저 환경을 세팅해 보겠습니다! 아래 단계를 따라주세요 🚀 | 1. uv를 설치한다. 2. 저장소를 받고 `uv sync`를 실행한다. 3. `.env.example`을 `.env`로 복사하고 게이트웨이 주소를 넣는다. `uv run pytest`가 통과하면 준비가 끝난 것이다. |
| 5 | 브리프 항목 | OpenAI가 혁신적인 새 모델을 공개했습니다. 게임 체인저가 될 것으로 보입니다. | OpenAI가 9월 2일 새 모델을 공개했다(출처 URL). 사실: 컨텍스트 1M 토큰, 입력 $2/M. 영향(추론): 요약 API의 청킹 단계를 없앨 수 있다. 적용(권고): 10월 파일럿의 폴백 후보에 넣고 비용을 재측정한다. 확인 필요: Azure 제공 시점. |
| 6 | 덱 헤드 메시지 | 게이트웨이 도입 효과 | 비용 가시성 확보와 모델 교체 1일 단축, 게이트웨이의 두 효과 |
| 7 | 덱 본문 | **확장성**: 다양한 모델을 손쉽게 추가할 수 있습니다. | 모델 추가: 설정 5줄, 재배포 없음 |
| 8 | 리뷰 코멘트 | 전반적으로 잘 작성되었습니다! 몇 가지 개선 사항이 있습니다. | services/llm.py:42 `requests.get`이 이벤트 루프를 막는다. `httpx.AsyncClient`로 바꾸고 타임아웃 10초를 넣어야 한다. |
| 9 | 결론 | 결론적으로, 신규 서버 도입은 업무 효율성을 높이고 경쟁력을 강화할 것입니다. | RTX 5090 32GB 서버 2대 도입을 권고한다. 30B급 모델 검증이 현재 불가능하고, 대안인 클라우드 GPU는 전시 현장 시연에 쓸 수 없기 때문이다. 남은 위험은 부품 수급에 따른 견적 변동이며 발주 직전 재확인으로 관리한다. |
| 10 | 회의록 | 다양한 의견이 논의되었으며 향후 지속적으로 협의하기로 함 | 결정: 파일럿 대상은 요약 API 1개. 액션: 민현성, 10/15까지 config 초안. 보류: 팀별 예산 상한(재무 확인 후). |

### B.7 사람이 쓴 글의 실체 (규칙으로 못 잡는 것, preflight에서 눈으로)

- 첫 문단에 결론과 숫자가 있다. 독자가 다음 문단을 읽을지 스스로 정할 수 있다.
- 판단에 주어가 있다("개발연구본부는 ~로 판단한다", "필자는"). 무주어 수동태("~로 판단됩니다")가 연속되지 않는다.
- 문단 길이가 다르다. 한 문장 문단이 있어도 된다. 모든 문단이 3문장이면 기계다.
- 단점과 하지 않을 것을 쓴다. 장점만 나열한 문서는 결재권자가 믿지 않는다.
- 접속사 대신 마침표. "또한", "이를 통해"는 문단당 1회 이하.
- 숫자는 실측이고 출처가 있다. 반올림된 "완벽한" 숫자(100%, 99.9%, 10배)는 없다.
- 마지막 문단은 요약이 아니라 다음 행동(누가, 언제, 무엇을)이다.
- 모르는 것을 모른다고 쓴다(`[확인 필요]`). 아는 척하는 문장이 없다.

## 부록 C. 문서 유형별 골격 요약 (`references/doc-types.md`의 색인)

| 유형 | 필수 절 | 통합 가능 | 톤 | 분량 |
|---|---|---|---|---|
| 설계서 | 개요(결론) · 요구사항·제약 · AS-IS · TO-BE(구성도 3수준) · 인터페이스 · 비기능 · 단계별 구축 · 위험 · 추가 확인사항 | 요구사항+제약, 위험+확인사항 | 서술식 | 8~20쪽 |
| 검토보고서 | review-report-writer 16단계 축약(개요·목적·현황·대상·기준·세부·비교표·기대효과·위험·비용일정·종합의견·권고안·확인사항) | 원 규칙 | 서술식 | 3~8쪽 |
| 가이드 | 목적·대상 · 준비 · 단계(명령 블록) · 확인 방법 · 문제 해결 · 참고 | 준비+단계 | 경어 가능 | 2~6쪽 |
| 런북 | 대상 시스템 · 증상별(확인→조치→에스컬레이션) · 연락처 · 변경 이력 | 없음 | 개조식 허용 | 1~4쪽 |
| ADR | 제목·상태·맥락·결정·대안(왜 밀렸나)·결과 | 없음 | 서술식 | 1쪽 |
| 인터페이스 정의서 | 개요 · 공통(인증·오류·버전) · 엔드포인트 표 · 예시 · 변경 이력 | 없음 | 서술식 | 표 중심 |
| 회의록 | 일시·참석 · 결정 · 액션(담당·기한) · 논의 요약 | 없음 | 개조식 | 1쪽 |
| 브리프 | 항목별(제목·출처·사실·영향·적용·확인) | 없음 | 서술식 | 1~2쪽 |
| README | 한 줄 · 실행 4줄 · 구조 · 설정 · 테스트 · 배포 | 없음 | 서술식 | 1쪽 |
| 교육 자료 | 목표 · 개념 · 실습 단계 · 확인 문제 · 정리 | 없음 | 경어 | 덱 병행 |

## 부록 D. 용어

- **AI 티(slop)**: 모델의 통계적 기본 문체·서식이 그대로 나온 결과. 이 문서에서는 §1.2 목록.
- **하드 룰 / 소프트 룰**: 편집 전 차단 / 종료 전 1회 지적.
- **문서 리드 · 덱 리드 · 서비스 리드**: 코드 전 1줄 선언. 기본값 점프를 막는 장치.
- **테마**: 원색·폰트·치수를 가진 유일한 파일(JSON). ui-skill-set의 tokens.css에 해당.
- **DSL**: `.doc.md`·`.deck.md`·`diagram`·`timeline`·`chart`. Markdown 위의 얇은 약속.
- **템플릿 모드**: 회사 양식 docx·pptx의 스타일·마스터를 유지하고 본문만 우리 DSL로 채우는 렌더링.
- **쓰기 게이트**: 되돌리기 어려운 MCP 툴을 환경변수로 잠그는 것.
- **사실 / 추론 / 권고**: 근거 있는 단정문 / "~로 예상된다" / "~하는 것이 적절하다". review-report-writer 규약.
- **추적표**: 공고 항목 ↔ FR ↔ 테스트 ↔ 골든 프롬프트를 잇는 표(부록 E). 비어 있는 칸이 곧 누락이다.

## 부록 E. 추적표 (공고 항목 ↔ 산출물 ↔ 검증)

구현이 끝날 때 이 표의 "검증" 열이 전부 채워져야 한다. `docs/traceability.md`로 복사해 마일스톤마다 결과를 적는다(FR-38).

| 공고 항목 | 스킬·도구 | FR | 단위 테스트 | 골든 프롬프트 | 마일스톤 | 검증(결과 기록) |
|---|---|---|---|---|---|---|
| FastAPI 개발 환경 구축 | `fastapi-service`, `scaffold.py`, `route_table.py` | FR-20, 26, 35 | test_scripts(scaffold·route_table·prompts) | 03 | M2 | |
| GitLab CI/CD 빌드·배포 | `gitlab-ci`, `ci_lint.py`, GitLab 공식 MCP | FR-21 | test_scripts(ci_lint) | 03 | M2 | |
| 코드 모듈화·구조 개선·리팩토링 | `py-refactor`, `import_graph.py` | FR-24 | test_scripts(import_graph) | 08 | M2 | |
| 코드 리뷰 | `py-review`, GitLab MCP 리뷰 게시 | FR-23 | (체크리스트 픽스처 diff) | 04 | M2 | |
| Unit 테스트 | `py-test`, `test_gaps.py`, `py_format.py` | FR-22, 25 | test_scripts(test_gaps), test_py_format | 03 | M2 | |
| 개발 가이드·교육 | `doc-write`(가이드·교육), `deck-write`(교육 덱) | FR-7, 17 | docgen 테스트 | 07 | M0, M1 | |
| 생성형 AI 서비스 분석·설계 | `doc-write`(설계서), `genai-patterns.md`, `arch-doc-types.md`, `docgen` | FR-7, 9~12, 19, 35, 36 | docgen(docx·pptx·diagram·compose) | 01, 02 | M1 | |
| 생성형 AI 서비스 개발·유지보수 | `fastapi-service --with-rag/--with-jobs`, `llm-gateway` 클라이언트 패턴 | FR-20, 27, 35 | test_scripts(scaffold 옵션) | 03, 05 | M2, M3 | |
| API·오픈소스 활용 | `llm-gateway`(LiteLLM·Langfuse), `model-serving`(vLLM) | FR-27, 29 | litellm_ops 테스트, vram_estimate | 05 | M3 | |
| 최신 AI 트렌드 조사·적용 | `ai-trend-brief` | FR-30 | (형식 파싱은 check_output) | 06 | M3 | |
| LLM 이해·API 사용 | `llm-gateway/assets/client_example.py`, `python-conventions.md` | FR-26, 27 | 골격 test_llm_client | 03 | M2, M3 | |
| 모델 최적화·서빙 | `model-serving`, `vram_estimate.py`, `bench_llm.py` | FR-29 | test_scripts(vram) | (없음, 실기기 필요: manual) | M3 | |
| 클라우드(Azure/AWS/GCP) | `llm-gateway/references/{azure,bedrock,vertex}.md`, `gitlab-ci/references/deploy-targets.md` | FR-21, 27 | config_validate 픽스처(3 제공자) | 05 | M2, M3 | |
| LiteLLM·LLM Gateway 구축 | `llm-gateway`, `litellm-ops` MCP | FR-27, 28 | litellm_ops(12 툴·V1~V8) | 05 | M3 | |
| (사용자 추가 요구) 문서·덱이 회사 것처럼 | `STYLE.md`, 테마, `doc_lint`, 템플릿 모드, 부록 B | FR-1~4, 10, 11, 18 | test_doc_lint, test_theme, docgen | 01, 02, 07 | M0, M1 | |
| (사용자 추가 요구) ui-skill-set 연동 | `theme_export --tokens-css`, `install --with-ui` | FR-33 | test_theme(램프·대비) | (수동) | M4 | |

## 부록 F. 합류 첫 주 확인 목록 (결정값을 실제로 바꿀 정보)

이 PRD의 추천값 중 일부는 회사 환경을 보기 전의 가정이다. 첫 주에 아래를 확인하고 해당 결정·설정을 갱신한다. 각 항목의 답은 `STYLE.md`·`.mcp.json`·환경변수에만 기록하고 저장소에는 넣지 않는다.

| # | 확인할 것 | 바뀌는 결정·설정 | 확인 방법 |
|---|---|---|---|
| 1 | 공식 문서·PPT 템플릿 파일과 브랜드 가이드 존재 여부 | D2 테마 값 → `theme_from_pptx`로 `docs/theme.json`, `STYLE.md template_pptx/template_docx` | 디자인·경영지원 담당에게 요청 |
| 2 | 결재 문서의 실제 관례: 톤(~다/~습니다), 번호 체계, 날짜 표기, 보안 등급 문구, 표지 결재란 | `STYLE.md` tone·numbering·date_format·security, `doc-types.md` | 최근 결재 문서 2~3개를 `docx_to_md`로 읽기 |
| 3 | GitLab 버전, Duo·beta 기능 활성 여부, 셀프호스팅 URL, 러너 종류(docker/k8s/shell) | D6 공식 MCP vs 커뮤니티, `gitlab-ci.yml`의 빌드 방식(kaniko/DinD), `.mcp.json` | `GET /api/v4/version`, 관리자 문의 |
| 4 | LiteLLM 게이트웨이 존재 여부·버전·admin 접근 권한, 없으면 도입 승인 경로 | `LITELLM_*` env, `llm-gateway` 구축 vs 운영 모드 | `GET /health/readiness` |
| 5 | 사용 클라우드·리전(예: Azure Korea Central), 데이터 반출·로그 보존 정책 | `references/{azure,bedrock,vertex}.md` 선택, `security.md` 반영 | 인프라·보안 담당 |
| 6 | 개발 PC 정책: Python·uv·Docker·Node·LibreOffice 설치 가능 여부, PyPI 미러·프록시 | 설치 경로(`uv` 필요), `preview` 가능성, `.mcp.json`의 `uv run` | 보안 정책 문서, 직접 설치 시도 |
| 7 | 사내 용어 표기(제품명·팀명·약어) | `docs/glossary.md`(S18) | 기존 문서·위키 |
| 8 | 기존 서비스 저장소 1개의 구조·테스트·CI 상태 | `py-refactor` 기준선(`import_graph.py`), `fastapi-service` 진단 모드 | 클론 후 `import_graph.py` 실행 |
| 9 | 주간보고·회의록 양식 | `weekly-report` 재사용 여부(비목표 유지), 회의록 골격 | 팀장 문의 |
| 10 | 문서 공유 위치(공유 드라이브·위키·GitLab wiki) | D11 제출본 경로, md의 mermaid 렌더링 가능 여부 | 팀 관례 확인 |
