# 검증 기준선 (2026-09-04)

## 골든 프롬프트 재현 (2026-09-04)

`prompts/01`~`08` 을 저장소 도구만으로 재현하고 각 프롬프트의 자동 검사를 돌린 결과다. 실기기(사내 GitLab·게이트웨이·공식 템플릿) 없이, 모르는 값은 `[확인 필요]` 로 남겼다.

| # | 프롬프트 | 검사 | 결과 |
|---|---|---|---|
| 01 | 게이트웨이 설계서 docx | 렌더 + check_output | PASS (하드 0, 테마 밖 색 0, 목차·구성도 2·비교표) |
| 02 | 경영진 10장 덱 pptx | 렌더 + check_output | PASS (9장, 덱 소프트 0, 네이티브 차트·타임라인) |
| 03 | 요약 API 서비스 골격 | scaffold → uv sync → pytest → import_graph | 9 passed, 순환 0, 레이어 위반 0 |
| 04 | MR 리뷰 | 리뷰 형식 + H9 | 3건 검출(S1·A1·T1), 시크릿 H9 확인 |
| 05 | 게이트웨이 config | config-validate | ok True, error 0 (V1~V8) |
| 06 | 트렌드 브리프 | doc_lint + 출처 | 5항목 모두 URL·날짜, 하드 0 소프트 0 |
| 07 | 개발 가이드(경어) | 렌더 + check_output + S16 | PASS, 존댓말 혼용 0 |
| 08 | 순환 import 정리 | import_graph + ADR 렌더 | 순환 검출 후 ADR 로 제거 계획, docx 렌더 |

재현 중 `doc_lint` S16(존댓말 혼용)이 경어 `~합니다` 를 평서문으로 오탐하던 버그를 고쳤다(경어 문서 전부에 영향). 정규식을 `~니다.` 전체로 넓히고 이중 차감을 없앴다.

## MCP 이식성 검증 (2026-09-04)

Claude 가 아닌 범용 MCP stdio 클라이언트로 두 서버에 붙여 확인했다. Codex·Gemini·Grok 이 MCP 서버에 붙는 방식이 이 방식이다.

| 서버 | initialize | 프로토콜 | tools/list | tools/call |
|---|---|---|---|---|
| docgen | OK | 2025-06-18 | 11툴 | theme_export 정상 |
| litellm-ops | OK | 2025-06-18 | 12툴 | config_validate ok:true |

Codex CLI 는 이 PC 에 없어 `codex plugin marketplace add` 는 실행하지 못했다. 매니페스트(`.codex-plugin/plugin.json`)는 JSON 유효를 확인했다.

## check_output 기준선

`mcp/docgen/fixtures/` 의 설계서(`design.doc.md`)와 덱(`gateway.deck.md`)을 렌더링해 `check_output.py` 로 검사한 결과다. 이 두 파일은 스킬이 만드는 문서·덱의 대표 형태다.

| 실행 | 산문 | office | 하드 룰 | 덱 소프트 | 테마 밖 색 | 판정 |
|---|---|---|---|---|---|---|
| design + gateway | 2 | 2(docx·pptx) | 0 | 0 | 0 | PASS |

- 하드 룰 0: em-dash·상투어·이모지·가짜 채움이 없다.
- 테마 밖 색 0: 생성 docx·pptx 가 데이타솔루션 팔레트와 그 파생 틴트만 쓴다. 문서에 내장된 기본 Office 팔레트(theme1.xml)는 검사 대상이 아니다. 콘텐츠 부분(document.xml, slideN.xml)만 본다.
- 이 검사는 `tests/test_m4_eval.py` 가 매번 렌더링해 재현한다.

## 스크립트 검증

| 항목 | 도구 | 결과 |
|---|---|---|
| 서비스 골격 | scaffold → uv sync → pytest | base 8, --with-sse 9 PASS |
| 게이트웨이 config | litellm-ops config-validate | config.example.yaml error 0 |
| 파이프라인 | ci_lint.py | assets/gitlab-ci.yml 통과, 오탐 stage 검출 |
| VRAM 산정 | vram_estimate.py | 알려진 값(32B fp16 = 64GB 가중치) 정확 |

## 재현

```
python eval/check_output.py runs/<프롬프트>
```

전체 자동 검증은 `uv run pytest` 와 `python -X utf8 templates/doc_lint.py --all docs skills references README.md`.
