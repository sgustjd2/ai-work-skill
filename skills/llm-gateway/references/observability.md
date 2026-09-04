# observability · 관측

게이트웨이 한곳에서 비용·지연·오류를 본다. 서비스마다 따로 계측하지 않아도 된다.

## Langfuse

프롬프트·응답·비용을 추적한다. `litellm_settings.success_callback: ["langfuse"]` 를 켜고 `LANGFUSE_PUBLIC_KEY`·`LANGFUSE_SECRET_KEY` 를 환경변수로 둔다. compose 의 `obs` 프로파일로 Langfuse 를 띄운다.

## 비용

응답 헤더 `x-litellm-response-cost` 에 요청당 비용이 실린다. 앱은 이 값을 로그에 남겨 요청 단위 비용을 추적한다. 팀·키별 누적은 `litellm-ops spend` 나 MCP `spend_summary` 로 본다.

## 메트릭

- 프록시의 `/metrics`(Prometheus 형식)로 요청 수·지연·오류율을 수집한다.
- OTel 이 있으면 `litellm_settings.callbacks` 에 otel 을 더해 트레이스를 보낸다.

## 로그 보존

프롬프트·응답 본문은 민감할 수 있다. 보존 기간과 마스킹 정책을 정한다. 개인정보가 들어가는 서비스는 본문 로깅을 끄거나 마스킹한다.
