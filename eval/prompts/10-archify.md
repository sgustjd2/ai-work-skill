---
doc_lint: off
---
# 골든 10 · 독립 다이어그램 (archify)

`/ai-init --with-archify` 로 archify 가 설치된 프로젝트에서 아래 프롬프트를 붙여 넣고, 결과(`docs/diagrams/*.json`, `docs/_build/diagrams/*.html`, visual-check 영수증)를 `runs/10-archify/` 에 저장한다. 아래 픽스처는 2026-09-06 에 validate 9항목·deliver·visual-check(4개 뷰포트) 를 모두 통과한 JSON 이다. 스킬이 만든 결과와 형태를 비교하는 기준이지, 복사할 사실이 아니다.

---

LLM 게이트웨이 도입 후 호출 구조를 공유용 독립 HTML 다이어그램으로 그려줘. 사내 서비스가 LiteLLM 게이트웨이를 거쳐 Azure OpenAI(1순위), Bedrock(폴백), 사내 vLLM 으로 가고, 게이트웨이는 PostgreSQL 에 키·비용을, Langfuse 에 추적을 남겨.

---

**유도되는 슬롭**: 그림을 문장으로 설명, 회사명·내부 URL 삽입, 검증 실패한 HTML 을 "완료" 로 보고, 세로로 긴 배치(visual-check 넘침), `meta.locale: "ko"` 같은 없는 값

**기대**: ① 유형 `architecture` 선택 ② `docs/diagrams/gateway.architecture.json`(한국어, locale 생략, showcase) ③ `validate` ok → `deliver` ok + SHA 영수증 ④ Chrome 이 있으면 `visual-check` pass, 없으면 skipped 로 보고 ⑤ 결과 보고에 뷰어 UI 가 영어로 남는다는 한 줄

**자동 검사**:

```bash
node ~/.claude/skills/archify/bin/archify.mjs validate architecture docs/diagrams/gateway.architecture.json --quality showcase --json
node ~/.claude/skills/archify/bin/archify.mjs deliver architecture docs/diagrams/gateway.architecture.json docs/_build/diagrams/gateway.html --quality showcase --json
node ~/.claude/skills/archify/bin/archify.mjs visual-check docs/_build/diagrams/gateway.html --json
```

`ok: true` 둘, `status: "pass"`(또는 Chrome 없음 `skipped`). `doc_lint` 는 JSON·HTML 을 보지 않는다.

**픽스처(통과 확인본)**:

```json
{
  "schema_version": 1,
  "diagram_type": "architecture",
  "meta": { "title": "LLM 게이트웨이 목표 아키텍처", "output": "gateway.html", "quality_profile": "showcase" },
  "components": [
    { "id": "svc", "type": "external", "label": "사내 서비스", "sublabel": "요약 API · 챗봇 (12개 팀)", "pos": [40, 260], "size": [150, 64] },
    { "id": "gw", "type": "backend", "label": "LiteLLM 게이트웨이", "sublabel": "인증 · 라우팅 · 비용", "pos": [400, 260], "size": [170, 64] },
    { "id": "langfuse", "type": "backend", "label": "Langfuse", "sublabel": "추적 · 평가", "pos": [400, 120], "size": [170, 60] },
    { "id": "db", "type": "database", "label": "PostgreSQL", "sublabel": "가상 키 · 사용량", "pos": [400, 400], "size": [170, 60] },
    { "id": "azure", "type": "external", "label": "Azure OpenAI", "sublabel": "Korea Central", "pos": [900, 120], "size": [160, 60] },
    { "id": "bedrock", "type": "external", "label": "AWS Bedrock", "sublabel": "폴백", "pos": [900, 260], "size": [160, 60] },
    { "id": "vllm", "type": "backend", "label": "vLLM", "sublabel": "사내 GPU · Llama", "pos": [900, 400], "size": [160, 60] }
  ],
  "boundaries": [
    { "kind": "region", "label": "사내 플랫폼", "wraps": ["gw", "langfuse", "db", "vllm"] }
  ],
  "connections": [
    { "id": "svc-gw", "from": "svc", "to": "gw", "label": "OpenAI 호환 HTTPS", "variant": "emphasis" },
    { "id": "gw-azure", "from": "gw", "to": "azure", "label": "1순위" },
    { "id": "gw-bedrock", "from": "gw", "to": "bedrock", "label": "폴백", "variant": "dashed", "labelDx": 40 },
    { "id": "gw-vllm", "from": "gw", "to": "vllm", "label": "내부 모델" },
    { "id": "gw-db", "from": "gw", "to": "db", "label": "키 · 비용", "fromSide": "bottom", "toSide": "top", "labelDy": 24 },
    { "id": "gw-langfuse", "from": "gw", "to": "langfuse", "label": "추적", "fromSide": "top", "toSide": "bottom" }
  ]
}
```

첫 시도에서 걸린 것 두 가지와 고친 값: "키 · 비용" 라벨이 게이트웨이 상자와 겹침(`labelDy: 24`), "폴백" 라벨이 "1순위" 경로 위에 놓임(`labelDx: 40`). 세로로 긴 배치(폭 810)는 validate 는 통과하지만 visual-check 에서 1440×900 세로 넘침으로 fail 이었다. 위처럼 폭 1130 으로 펼치면 통과한다.
