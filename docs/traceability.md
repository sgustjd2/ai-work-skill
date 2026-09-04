# 추적표

공고 항목과 산출물, 검증을 잇는다(PRD 부록 E). 마일스톤마다 "검증" 열에 테스트 파일명과 결과를 적는다. 빈 칸은 곧 누락이다.

| 공고 항목 | 스킬·도구 | FR | 단위 테스트 | 골든 | 마일스톤 | 검증(결과) |
|---|---|---|---|---|---|---|
| FastAPI 개발 환경 구축 | fastapi-service, scaffold.py, route_table.py | FR-20, 26, 35 | test_scripts | 03 | M2 | |
| GitLab CI/CD 빌드·배포 | gitlab-ci, ci_lint.py, GitLab MCP | FR-21 | test_m2_scripts(ci_lint) | 03 | M2 | **완료**: .gitlab-ci.yml·MR/이슈 템플릿·CODEOWNERS·references 4종, ci_lint 3테스트 |
| 코드 모듈화·구조 개선 | py-refactor, import_graph.py | FR-24 | test_m2_scripts(import_graph) | 08 | M2 | **완료**: 순환(Tarjan)·레이어 위반·긴 파일, 2테스트 |
| 코드 리뷰 | py-review, GitLab MCP | FR-23 | checklist.md | 04 | M2 | **완료**: SKILL + 체크리스트(항목 ID), MR 리뷰 흐름 |
| Unit 테스트 | py-test, test_gaps.py, py_format.py | FR-22, 25 | test_m2_scripts(test_gaps), test_py_format | 03 | M2 | **완료**: SKILL + pytest-conventions·llm-mocking, test_gaps 1테스트 |
| 개발 가이드·교육 | doc-write(가이드·교육), deck-write | FR-7, 17 | docgen | 07 | M0, M1 | doc-write SKILL·references M0 완료, 렌더링 M1 |
| 생성형 AI 서비스 분석·설계 | doc-write(설계서), genai-patterns, docgen | FR-7, 9~12, 19, 35, 36 | docgen | 01, 02 | M1 | doc-write M0 완료, docgen M1 |
| 생성형 AI 서비스 개발·유지보수 | fastapi-service, llm-gateway | FR-20, 27, 35 | test_m2_scripts(scaffold·route_table), 생성 서비스 pytest | 03, 05 | M2, M3 | **M2 완료**: 예제 서비스+scaffold(7옵션)+route_table, 생성 골격 pytest 통과(base 8, sse 9) |
| API·오픈소스 활용 | llm-gateway, model-serving | FR-27, 29 | litellm_ops(21), vram/bench(5) | 05 | M3 | **완료**: 게이트웨이 설정·클라이언트, vLLM·양자화 참조 |
| 최신 AI 트렌드 조사·적용 | ai-trend-brief | FR-30 | (형식은 M4 eval) | 06 | M3 | **완료**: SKILL + sources.yaml + brief-template |
| LLM 이해·API 사용 | LLMClient(게이트웨이), python-conventions | FR-26, 27 | 생성 서비스 test_llm_client | 03 | M2, M3 | **M2 완료**: 게이트웨이 클라이언트·재시도·비용헤더·프롬프트 로더, python-conventions |
| 모델 최적화·서빙 | model-serving, vram_estimate·bench_llm | FR-29 | test_m3_scripts(5) | manual | M3 | **완료**: VRAM 산정·벤치, sizing·quantization·vllm·alternatives |
| 클라우드(Azure/AWS/GCP) | azure·bedrock·vertex 참조, deploy-targets | FR-21, 27 | config_validate 픽스처 | 05 | M2, M3 | **M3 완료**: 제공자 3종 연결 참조, config.example 검증 통과 |
| LiteLLM·LLM Gateway 구축 | llm-gateway, litellm-ops MCP | FR-27, 28 | litellm_ops(21: ops+validate) | 05 | M3 | **완료**: MCP 12툴+CLI, config_validate V1~V8, 쓰기 게이트 |
| 문서·덱이 회사 것처럼 | STYLE.md, 테마, doc_lint, 부록 B | FR-1~5, 10, 11, 18 | test_doc_lint, test_theme, test_install | 01, 02, 07 | M0, M1 | M0 완료: doc_lint(H1~H10·S1~S18)·테마·install·STYLE.md, 72 테스트 PASS |
| ui-skill-set 연동 | theme_export, install --with-ui | FR-33 | test_theme | manual | M4 | |

## M1 완료 (docgen, 2026-09-04)

FR-9~19, 36 전부 구현. docgen 테스트 53개 + M0 72개 = 125 PASS. ruff·doc_lint 자기 검사 통과.

- FR-9 파서: `parse.py`. `.doc.md`/`.deck.md` -> frontmatter + 블록(제목·문단·목록·표·코드·구성도·타임라인·차트·이미지·인용·각주). 표 정렬·캡션·2단·레이아웃 추론. `test_parse.py` PASS.
- FR-10 docx: `docx_render.py`. 표지·개정이력·목차 필드·머리글/바닥글·쪽번호·스타일 6종·eastAsia 폰트·wordWrap·표 헤더 음영·캡션 번호(표/그림)·마커 형광·구성도 PNG 삽입·회사 docx 템플릿 모드. `test_docx.py` PASS(unzip 검증).
- FR-11 pptx: `pptx_render.py`. 레이아웃 10종·헤드 메시지·accent bar·바닥글 쪽번호·발표자 노트·a:ea 한글 폰트·네이티브 차트·구성도 도형·회사 pptx 템플릿 모드(기존 슬라이드 제거). `test_pptx.py` PASS.
- FR-12 구성도: `diagram/{layout,mermaid,svg,png,pptx_shapes}.py`. 결정적 열 기반 배치 + mermaid(md)·svg·PNG(Pillow, 한글 폰트 자동 탐색, 없으면 mermaid 대체)·pptx 네이티브 도형(화살촉 XML). timeline·chart 블록 포함. `test_diagram.py` PASS.
- FR-13 MCP+CLI: `server.py`(FastMCP 11툴, ToolError 가드, 절대경로·warnings) + `__main__.py`(argparse, --json, 종료코드 0/1/2/3) + `core.py`(경로 해석 DOCGEN_PROJECT_DIR, STYLE.md 테마/출력경로, filename_pattern).
- FR-14 lint 단일 구현: `lint.py` 가 `templates/doc_lint.py` 를 sys.modules 등록 후 import → `doc_lint.lint is docgen.lint.lint`. `test_lint_bridge.py`·`test_lint_extract_theme.py` 로 확인.
- FR-15 preview: `preview.py`. LibreOffice(soffice) 탐색 → PDF → PNG(pdftoppm), 없으면 available=false + 안내(CI 안 깸).
- FR-16 추출: `extract.py`. docx_to_md·pptx_to_md·theme_from_pptx(clrScheme/fontScheme 매핑 초안)·layouts.
- FR-17 deck-write: `skills/deck-write/SKILL.md` + `references/{slide-rules,layouts}.md`.
- FR-19 arch-doc-types: `skills/doc-write/references/arch-doc-types.md`(설계서·AS-IS/TO-BE·인터페이스·런북·ADR·구성도 규약).
- FR-36 diagram_from_compose: compose.yaml → 노드 kind 추론(litellm→gateway, pgvector→data 등)·depends_on→엣지.
- 테마: `theme.py`(로드 4단계 해석·색 역할·tint·mix·대비). 소스에 hex 리터럴 0(테스트 강제).
- 픽스처: `fixtures/{design.doc.md, gateway.deck.md}`. 렌더·추출 테스트와 예시에 사용.
- 미해결 결정 없음(§14 추천값 적용). 남은 것은 D14(한글 어절 줄바꿈 속성 실측)로, PowerPoint/Word 실측 시 확정.

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

## M2 완료 (개발 스킬, 2026-09-04)

FR-20~26, 35 전부 구현. 스크립트 단위 테스트 10개 추가(누적 139 PASS, manual 1 제외). ruff·doc_lint 통과.

- FR-20 fastapi-service: SKILL + `assets/service/`(완전한 예제 서비스, 프롬프트 파일 로더) + `scripts/scaffold.py`(7옵션: db·redis·sse·auth·rag·jobs·otel, 마커 기반 가지치기, pyproject·compose·.env·README 생성) + `scripts/route_table.py`(openapi 기반, --md·--openapi). **생성 골격이 실제로 uv sync + pytest 통과**(base 8, --with-sse 9).
- FR-21 gitlab-ci: SKILL + `assets/`(.gitlab-ci.yml: workflow·5스테이지·uv 캐시·kaniko·SAST·환경별 배포, MR/이슈 템플릿, CODEOWNERS) + `scripts/ci_lint.py`(로컬 구조검사 + GitLab CI Lint API) + `references/`(deploy-targets·pipeline-recipes·gitlab-mcp-playbook·branching).
- FR-22 py-test: SKILL + `references/`(pytest-conventions·llm-mocking) + `scripts/test_gaps.py`(ast, 미참조 공개함수).
- FR-23 py-review: SKILL + `references/checklist.md`(항목 ID, 호출자 추적) + MR 리뷰 흐름(GitLab MCP, 승인 후 게시).
- FR-24 py-refactor: SKILL + `scripts/import_graph.py`(ast, Tarjan SCC 순환, 레이어 위반, 팬인/팬아웃, 긴 파일).
- FR-25 py_format: M0 선행 완료.
- FR-26 python-conventions.md, FR-35 genai-patterns.md: 플러그인 루트 `references/`(공용). RAG·프롬프트·구조화 출력·비동기·가드레일·평가.
- 스크립트는 전부 표준 라이브러리만. 서비스 자산은 `{{pkg}}` 토큰 템플릿이라 ruff 에서 제외(extend-exclude).
- 다음: M3(LLM 운영: llm-gateway·litellm-ops MCP·model-serving·ai-trend-brief).

## M3 완료 (LLM 운영, 2026-09-04)

FR-27~30 전부 구현. litellm_ops 21 + M3 스크립트 5 테스트 추가(누적 167 PASS, manual 1 제외). ruff·doc_lint 통과.

- FR-27 llm-gateway: SKILL + assets(config.example.yaml[검증 통과]·compose.yaml·.env.example·client_example.py) + references 7종(azure·bedrock·vertex·vllm·observability·security·ops-runbook).
- FR-28 litellm-ops MCP: mcp/litellm_ops(uv 프로젝트). core(LiteLLMOps 12메서드, 키 마스킹, 쓰기 게이트) + validate(config_validate V1~V8, config_diff) + server(FastMCP 12툴) + CLI. 테스트는 httpx.MockTransport 로 각 엔드포인트 픽스처, config_validate V1~V8 각 1개.
- FR-29 model-serving: SKILL + scripts(vram_estimate.py 가중치+KV+여유, bench_llm.py TTFT p50/p95·tokens/s) + references 4종(vllm·quantization·sizing·alternatives).
- FR-30 ai-trend-brief: SKILL + assets(sources.yaml·brief-template.md). WebSearch·WebFetch.
- 쓰기 게이트: LITELLM_OPS_ALLOW_WRITE=true 일 때만 키 발급·차단·팀 생성. 시크릿은 마스킹.
- config.example.yaml 은 config_validate 를 통과한다(azure 2리전·bedrock·vertex·vllm·임베딩, 폴백 무결, os.environ 참조).
- 다음: M4(배포·플러그인 매니페스트·.mcp.json·eval·ui 연동).
