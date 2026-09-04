# ai-work-skill

생성형 AI 서비스 개발 조직(데이타솔루션)에서 매일 하는 일을 Claude Code가 회사 표준대로 해내게 하는 스킬 세트.
FastAPI 서비스 골격, GitLab CI/CD, 코드 리뷰·테스트·리팩토링, LiteLLM 게이트웨이 운영, 아키텍처 문서(docx)·덱(pptx) 생성, AI 트렌드 브리프를 다룬다.
문서는 데이타솔루션 팔레트와 한국 기업 문서체로 나오고, AI 문체는 훅이 파일에 닿기 전에 차단한다.

- 설계 문서: [docs/PRD.md](docs/PRD.md) · 구현 규약: [CLAUDE.md](CLAUDE.md) · 외부 사실 출처: [docs/research/sources-2026-09-04.md](docs/research/sources-2026-09-04.md)
- 상태: **완성** (2026-09-04). M0~M4 전체 구현. 스킬 11개 + MCP 서버 2개(docgen·litellm-ops) + 훅 2개. 검증: `uv run pytest` 171 PASS(+manual 1), `ruff check`·`format --check` clean, `doc_lint --all` 하드 위반 0(97파일). 생성 FastAPI 골격이 그대로 `uv run pytest` 통과, `config.example.yaml` 이 `config_validate` 통과, 설계서 docx·덱 pptx 가 실제 렌더되고 `check_output` PASS. 선행 자산: `../ui-skill-set`(구조·훅 원형), `../품의서/.claude/skills/review-report-writer`(문체 규칙 원형).

## 구성

| 계층 | 내용 |
|---|---|
| 에셋 | `templates/STYLE.md`(문서 계약), `themes/datasolution.json`(팔레트·폰트·치수), `skills/fastapi-service/assets/`(예제 서비스), `skills/llm-gateway/assets/config.example.yaml` |
| 룰 | 스킬 11개: `ai-init` `doc-write` `deck-write` `fastapi-service` `gitlab-ci` `py-review` `py-test` `py-refactor` `llm-gateway` `model-serving` `ai-trend-brief` |
| 하네스 | `templates/doc_lint.py`(편집 전 AI 문체 차단·종료 전 점검), `templates/py_format.py`(편집 후 ruff) |
| 도구 | MCP `docgen`(md → docx/pptx, 구성도·차트, 미리보기, 양식 추출), `litellm-ops`(게이트웨이 상태·비용·키·config 검증 12툴), GitLab 공식 MCP(설정만) |

## 설치

플러그인으로:

```bash
claude plugin marketplace add sgustjd2/ai-work-skill
```

그다음 `/plugin install ai-work-skill@ai-work-skill`. MCP 서버(`docgen`·`litellm-ops`)는 `uv` 가 필요하다. 프로젝트에 훅·`STYLE.md`·규약을 넣으려면 `/ai-init` 을 실행한다(문서 스킬은 `STYLE.md` 가 있어야 동작한다).

## 개발

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run python -X utf8 templates/doc_lint.py --all docs skills references README.md
```

구조·규약은 [CLAUDE.md](CLAUDE.md), 검증 기준선은 [eval/results.md](eval/results.md), 요구사항 추적은 [docs/traceability.md](docs/traceability.md) 를 본다.
