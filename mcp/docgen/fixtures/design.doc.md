---
title: 사내 LLM 게이트웨이 도입 설계서
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

여러 팀이 각자 발급한 LLM API 키가 흩어져 비용과 접근을 통제하지 못한다. LiteLLM 프록시를
사내 공용 게이트웨이로 도입해 인증·라우팅·비용을 한곳에서 처리하는 것을 권고한다. 확정되지 않은
값은 `[확인 필요]` 로 표시한다.

## 1.1 목적

- 팀별로 흩어진 API 키를 엔드포인트 하나로 모은다
- 모델 교체를 서비스 코드 수정 없이 설정 변경으로 끝낸다
- 프롬프트·응답 로그와 비용을 한곳에서 본다

## 1.2 제약

- 시크릿은 환경변수로만 주입한다
- 기존 서비스의 코드 변경을 최소화한다

# 2. 목표 아키텍처

게이트웨이가 인증과 라우팅, 예산을 담당하고 각 서비스는 OpenAI 호환 API 로 게이트웨이만 부른다.

<!-- caption: 목표 구성 -->

```diagram
type: architecture
direction: LR
groups:
  - { id: client, label: 사용자 채널 }
  - { id: platform, label: AI 플랫폼 (신규), style: highlight }
  - { id: providers, label: 모델 제공자 }
nodes:
  - { id: web, label: 웹 포털, kind: ui, group: client }
  - { id: api, label: 요약 API\n(FastAPI), kind: service, group: platform }
  - { id: gw, label: LiteLLM Proxy, kind: gateway, group: platform, note: 라우팅·예산·키 }
  - { id: pg, label: PostgreSQL, kind: data, group: platform }
  - { id: azure, label: Azure OpenAI, kind: external, group: providers }
  - { id: vllm, label: vLLM (사내 GPU), kind: llm, group: providers }
edges:
  - { from: web, to: api, label: HTTPS }
  - { from: api, to: gw, label: OpenAI 호환 }
  - { from: gw, to: pg, label: 키·비용, style: dashed }
  - { from: gw, to: azure }
  - { from: gw, to: vllm, label: 폴백, style: dashed }
```

# 3. 대안 비교

<!-- caption: 게이트웨이 대안 -->

| 항목 | LiteLLM | Kong AI Gateway | 자체 개발 | 검토 의견 |
|---|---:|---:|---:|---|
| 초기 구축 | 낮음 | 중간 | 높음 | LiteLLM 이 설정 파일 하나로 시작 |
| 폴백·예산 | 있음 | 일부 | 직접 구현 | LiteLLM 우위 |
| 운영 인력 | 1명 | 2명 | 3명 이상 | 소규모 조직에 LiteLLM 적합 |

LiteLLM 을 권고한다. 운영 부담 대비 기능이 가장 넓고, 팀별 예산과 가상 키가 설정 하나로 끝난다.

# 4. 비기능 요구

| 항목 | 목표 | 비고 |
|---|---|---|
| 가용성 | 99% | 폴백으로 단일 제공자 장애 흡수 |
| 지연 | 스트리밍 우선 | 첫 토큰까지 [확인 필요] |
| 비용 | 팀별 예산 상한 | 초과 시 알림 |

# 5. 위험과 대응

- 제공자 장애 시 폴백 모델의 응답 형식이 달라 후처리 오류가 날 수 있다. 폴백 모델도 골든 테스트에 넣는다.
- 게이트웨이가 단일 장애점이 된다. 다중 인스턴스와 헬스체크로 완화한다.

# 6. 추가 확인사항

- 첫 토큰 지연 목표치 `[확인 필요]`
- 팀별 예산 상한 정책 `[확인 필요]`
