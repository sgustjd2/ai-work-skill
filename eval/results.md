# 검증 기준선 (2026-09-04)

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
