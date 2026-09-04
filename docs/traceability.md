# 추적표

공고 항목과 산출물, 검증을 잇는다(PRD 부록 E). 마일스톤마다 "검증" 열에 테스트 파일명과 결과를 적는다. 빈 칸은 곧 누락이다.

| 공고 항목 | 스킬·도구 | FR | 단위 테스트 | 골든 | 마일스톤 | 검증(결과) |
|---|---|---|---|---|---|---|
| FastAPI 개발 환경 구축 | fastapi-service, scaffold.py, route_table.py | FR-20, 26, 35 | test_scripts | 03 | M2 | |
| GitLab CI/CD 빌드·배포 | gitlab-ci, ci_lint.py, GitLab MCP | FR-21 | test_scripts | 03 | M2 | |
| 코드 모듈화·구조 개선 | py-refactor, import_graph.py | FR-24 | test_scripts | 08 | M2 | |
| 코드 리뷰 | py-review, GitLab MCP | FR-23 | 픽스처 diff | 04 | M2 | |
| Unit 테스트 | py-test, test_gaps.py, py_format.py | FR-22, 25 | test_py_format | 03 | M2 | py_format: 순수 함수 테스트 PASS(M0 선행), 통합 M2 |
| 개발 가이드·교육 | doc-write(가이드·교육), deck-write | FR-7, 17 | docgen | 07 | M0, M1 | doc-write SKILL·references M0 완료, 렌더링 M1 |
| 생성형 AI 서비스 분석·설계 | doc-write(설계서), genai-patterns, docgen | FR-7, 9~12, 19, 35, 36 | docgen | 01, 02 | M1 | doc-write M0 완료, docgen M1 |
| 생성형 AI 서비스 개발·유지보수 | fastapi-service, llm-gateway | FR-20, 27, 35 | test_scripts | 03, 05 | M2, M3 | |
| API·오픈소스 활용 | llm-gateway, model-serving | FR-27, 29 | litellm_ops | 05 | M3 | |
| 최신 AI 트렌드 조사·적용 | ai-trend-brief | FR-30 | check_output | 06 | M3 | |
| LLM 이해·API 사용 | client_example.py, python-conventions | FR-26, 27 | 골격 test | 03 | M2, M3 | |
| 모델 최적화·서빙 | model-serving, vram_estimate.py | FR-29 | test_scripts | manual | M3 | |
| 클라우드(Azure/AWS/GCP) | 참조 문서, deploy-targets | FR-21, 27 | config_validate | 05 | M2, M3 | |
| LiteLLM·LLM Gateway 구축 | llm-gateway, litellm-ops MCP | FR-27, 28 | litellm_ops | 05 | M3 | |
| 문서·덱이 회사 것처럼 | STYLE.md, 테마, doc_lint, 부록 B | FR-1~5, 10, 11, 18 | test_doc_lint, test_theme, test_install | 01, 02, 07 | M0, M1 | M0 완료: doc_lint(H1~H10·S1~S18)·테마·install·STYLE.md, 72 테스트 PASS |
| ui-skill-set 연동 | theme_export, install --with-ui | FR-33 | test_theme | manual | M4 | |

## M0 완료 근거 (2026-09-04)

- FR-1 STYLE.md: `templates/STYLE.md`. frontmatter 스키마 + 6절 본문.
- FR-2 테마: `themes/datasolution.json` + `themes/theme.schema.json`. `tests/test_theme.py` PASS(스키마·hex·소스 리터럴 0).
- FR-3 doc_lint --pre: `templates/doc_lint.py`. 하드 H1~H10, 소프트 S1~S18, 3 CLI 모드, 마커·정책 예외, 안티 데드락.
- FR-4 테스트: `tests/test_doc_lint.py` 49 케이스 PASS(룰별 양성/음성, CLI 3모드 subprocess, Windows 경로).
- FR-5 install.py: `templates/install.py`. `tests/test_install.py` PASS(병합·치환·멱등·실행기 탐지·update·uninstall).
- FR-6 ai-init: `skills/ai-init/SKILL.md`.
- FR-7 doc-write: `skills/doc-write/SKILL.md` + references 4종(writing-rules-ko, doc-types, korean-format, preflight-doc).
- FR-8 스니펫: `templates/CLAUDE.snippet.md`, `templates/settings.json`, `templates/mcp.gitlab.snippet.json`.
- FR-25 py_format(M0 선행): `templates/py_format.py` + `tests/test_py_format.py`. 통합 테스트는 M2.
- FR-37 저장소 CLAUDE.md·research: 유지.
- 검증 명령: `uv run pytest`(72 PASS), `uv run ruff check`·`format --check`(clean), `doc_lint.py --all docs skills README.md`(하드 0).
