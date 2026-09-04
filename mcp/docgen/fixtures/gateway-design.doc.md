---
title: 사내 LLM 게이트웨이 아키텍처 설계서
subtitle: LiteLLM 기반 공용 LLM API
doc_type: 설계서
org: 데이타솔루션 기술연구소
author: 민현성
date: 2026-09-04
version: 0.1
security: 대외비
theme: datasolution
toc: true
history:
  - { version: 0.1, date: 2026-09-04, author: 민현성, note: 초안 }
approvers: [팀장, 본부장]
---

# 1. 개요

LiteLLM 프록시를 사내 공용 LLM 게이트웨이로 도입한다. 팀별로 흩어진 API 키를 엔드포인트 하나로 모으고, 모델 교체를 코드 수정 없이 설정 변경으로 끝내는 것이 목표다. 10월 파일럿, 12월 전환을 권고한다. 예산 승인 시점은 `[확인 필요]`.

## 1.1 목적

- 팀별 키 관리와 비용 집계를 한곳으로 모은다
- 모델 교체를 설정 변경으로 끝낸다

# 2. 대안 비교

<!-- caption: 게이트웨이 대안 비교 -->

| 항목 | LiteLLM | 자체 개발 | 검토 의견 |
|---|---|---|---|
| 도입 기간 | 2주 | 3개월 | LiteLLM 이 운영 부담 대비 기능이 넓다 |
| 폴백 | 설정 | 직접 구현 | 설정 파일 하나로 끝난다 |

# 3. 목표 구성 (TO-BE)

```diagram
type: architecture
direction: LR
groups:
  - { id: platform, label: AI 플랫폼 }
nodes:
  - { id: api, label: 요약 API\n(FastAPI), kind: service, group: platform }
  - { id: gw, label: LiteLLM Proxy, kind: gateway, group: platform, note: 라우팅·예산 }
  - { id: azure, label: Azure OpenAI, kind: external }
edges:
  - { from: api, to: gw, label: OpenAI 호환 }
  - { from: gw, to: azure, style: dashed }
```

# 4. 예상 비용

```chart
type: bar
title: 월 예상 비용
unit: 만원
categories: [10월, 11월, 12월]
series:
  - { name: 파일럿, values: [50, 80, 120] }
```

> 참고: 폴백 모델의 응답 형식이 달라 후처리 오류가 날 수 있다. 골든 테스트에 폴백 모델도 넣는다.

# 5. 추가 확인사항

- 예산 승인 시점 `[확인 필요]`
