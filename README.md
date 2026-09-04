# ai-work-skill

생성형 AI 서비스 개발 조직(데이타솔루션)에서 매일 하는 일을 Claude Code가 회사 표준대로 해내게 하는 스킬 세트.
FastAPI 서비스 골격, GitLab CI/CD, 코드 리뷰·테스트·리팩토링, LiteLLM 게이트웨이 운영, 아키텍처 문서(docx)·덱(pptx) 생성, AI 트렌드 브리프를 다룬다.
문서는 데이타솔루션 팔레트와 한국 기업 문서체로 나오고, AI 문체는 훅이 파일에 닿기 전에 차단한다.

- 설계 문서: [docs/PRD.md](docs/PRD.md)
- 상태: **M0~M3 완료** (2026-09-04). M0 골격, M1 문서 생성 엔진 `docgen`(.doc.md→docx, .deck.md→pptx, 구성도·차트, MCP+CLI), M2 개발 스킬(`fastapi-service`+`scaffold`, `gitlab-ci`, `py-test`, `py-review`, `py-refactor`)에 더해, M3 LLM 운영이 동작한다. `llm-gateway` 는 검증을 통과하는 `config.example.yaml`(Azure 2리전·Bedrock·Vertex·vLLM·임베딩)과 제공자별 참조를 갖췄다. `litellm-ops` MCP 서버는 상태·비용·키·팀 조회와 `config_validate`(V1~V8)를 12개 툴로 제공하고, 키 발급·차단은 환경변수 쓰기 게이트로 잠근다. `model-serving`(`vram_estimate`·`bench_llm`), `ai-trend-brief` 도 갖췄다. 검증: `uv run pytest` 167 PASS(+manual 1), `ruff check`·`format --check` clean, `doc_lint --all` 하드 0(98파일). 생성 FastAPI 골격이 그대로 pytest 통과, litellm-ops 는 httpx MockTransport 로 테스트. 미해결 결정 없음(§14 추천값 적용). 다음은 M4(배포·플러그인 매니페스트·`.mcp.json`·eval·ui-skill-set 연동). 구현은 Claude Opus 4.8이 PRD와 [CLAUDE.md](CLAUDE.md)만 보고 진행한다.
- 외부 사실 출처: [docs/research/sources-2026-09-04.md](docs/research/sources-2026-09-04.md)
- 선행 자산: `../ui-skill-set`(구조·훅·설치기 원형), `../품의서/.claude/skills/review-report-writer`(문체 규칙 원형)

## 구성 (계획)

| 계층 | 내용 |
|---|---|
| 에셋 | `templates/STYLE.md`(문서 계약), `themes/datasolution.json`(팔레트·폰트·치수), FastAPI 골격, LiteLLM `config.example.yaml` |
| 룰 | 스킬 11개: `ai-init` `doc-write` `deck-write` `fastapi-service` `gitlab-ci` `py-review` `py-test` `py-refactor` `llm-gateway` `model-serving` `ai-trend-brief` |
| 하네스 | `doc_lint.py`(편집 전 차단·종료 전 점검), `py_format.py`(편집 후 ruff) |
| 도구 | MCP 서버 `docgen`(md → docx/pptx, 구성도, 미리보기, 양식 추출), `litellm-ops`(게이트웨이 상태·비용·키·설정 검증), GitLab 공식 MCP(설정만) |

## 구현 시작하기 (Opus)

1. `docs/PRD.md` 전체를 읽는다. §16이 구현 지침이다.
2. §14의 결정은 추천값으로 진행한다.
3. M0부터 순서대로. 각 FR은 코드 + 테스트 + 완료 조건 확인이 끝나야 완료다.
