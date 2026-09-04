---
title: LLM 게이트웨이 도입 아키텍처
subtitle: LiteLLM 기반 사내 공용 LLM API
org: 데이타솔루션 기술연구소
author: 민현성
date: 2026-09-04
theme: datasolution
agenda: true
security: 대외비
footer: 데이타솔루션 기술연구소
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
type: architecture
direction: LR
groups:
  - { id: platform, label: AI 플랫폼, style: highlight }
  - { id: prov, label: 제공자 }
nodes:
  - { id: svc, label: 서비스들, kind: service, group: platform }
  - { id: gw, label: LiteLLM, kind: gateway, group: platform }
  - { id: az, label: Azure OpenAI, kind: external, group: prov }
  - { id: vllm, label: vLLM, kind: llm, group: prov }
edges:
  - { from: svc, to: gw, label: OpenAI 호환 }
  - { from: gw, to: az }
  - { from: gw, to: vllm, label: 폴백, style: dashed }
```

---
# 비용 비교
<!-- layout: chart -->
## LiteLLM 이 3년 총소유비용이 가장 낮다
```chart
type: bar
title: 3년 총소유비용
unit: 백만원
categories: [LiteLLM, Kong, 자체개발]
series:
  - { name: 구축, values: [20, 60, 140] }
  - { name: 운영, values: [100, 120, 100] }
source: 사내 추정 2026-09
```

---
# 대안 비교
<!-- layout: table -->
## 기능 폭 대비 운영 부담은 LiteLLM 이 가장 낫다
| 항목 | LiteLLM | Kong | 자체 개발 | 검토 의견 |
|---|---|---|---|---|
| 폴백 | 있음 | 일부 | 구현 | LiteLLM 우위 |
| 예산 | 있음 | 없음 | 구현 | LiteLLM 우위 |
| 인력 | 1명 | 2명 | 3명+ | 소규모에 적합 |
<!-- source: 각 제품 공식 문서 2026-09 -->

---
# 추진 일정
<!-- layout: timeline -->
## 10월 말 파일럿, 12월 전사 전환
```timeline
tasks:
  - { label: 설계·검토, start: 2026-09, end: 2026-09 }
  - { label: 파일럿, start: 2026-10, end: 2026-11 }
  - { label: 전사 전환, start: 2026-12, end: 2026-12 }
```

---
# 요청 사항
<!-- layout: closing -->
## 파일럿 예산 승인과 팀별 키 발급 정책 확정이 필요하다
- 결정 1: 파일럿 대상은 요약 API 1개
- 결정 2: 팀별 예산 상한과 키 등급 정책
- 기한: 9월 30일
