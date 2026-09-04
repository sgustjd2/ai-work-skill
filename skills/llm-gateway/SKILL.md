---
name: llm-gateway
description: >
  LiteLLM 프록시 기반 LLM 게이트웨이를 설계·구축·운영한다. "LiteLLM", "LLM 게이트웨이", "API 게이트웨이",
  "config.yaml", "모델 라우팅·폴백", "가상 키·팀별 예산", "Azure OpenAI/Bedrock/Vertex 연결", "vLLM 등록",
  "비용 추적", "Langfuse 연동", "게이트웨이 장애", "모델 교체", "레이트 리밋" 요청에 반드시 쓴다. 설정은
  검증(config_validate) 후에만 배포하고, 상태·비용·키는 litellm-ops MCP 로 본다. 시크릿은 절대 yaml 에 쓰지 않는다.
  모델 서빙(vLLM 자체 운영)은 model-serving 이 담당한다.
version: 0.1.0
user-invocable: true
argument-hint: "[구축 | 모델 추가 | 키 발급 | 장애 진단 | 비용]"
allowed-tools:
  - Bash(uv run --project * python -m litellm_ops *)
  - Bash(docker compose *)
  - mcp__litellm-ops
---

# llm-gateway

LiteLLM 게이트웨이를 만들고 운영한다. 설정 조각은 `assets/` 와 `references/` 가 원본이다. 시크릿은 yaml 에 쓰지 않는다.

## 절차

1. 요청을 분류한다. 구축, 모델 추가, 키·예산, 장애, 비용, 관측 중 무엇인가.

2. 구축이면 게이트웨이 리드를 한 줄로 선언한다.
   `게이트웨이: <환경> · 제공자 <azure,bedrock,vertex,openai,vllm 중> · 라우팅 <simple-shuffle|least-busy|latency> · 폴백 <있음> · 예산 <팀별> · 관측 <langfuse|otel|없음>`

3. `assets/config.example.yaml` 을 복사해 채운다. 제공자별 상세는 `references/<provider>.md`. 모든 키·엔드포인트는 `os.environ/` 참조이고 `assets/.env.example` 과 1:1 이다.

4. 배포 전에 검증한다.
   ```
   python -m litellm_ops config-validate config.yaml
   ```
   또는 litellm-ops MCP 의 `config_validate`. 오류(V1~V8)가 0 이어야 배포한다.

5. `assets/compose.yaml` 으로 기동한다. postgres 가 있어야 가상 키·비용이 저장된다. `gateway_health` 로 준비를 확인하고 `test_completion` 으로 실제 응답을 본다.

6. 팀 키가 필요하면 `team_create` 로 팀·예산을 만든 뒤 `key_create` 로 발급한다(둘 다 쓰기 게이트가 열려야 한다). 전체 키는 응답에 한 번만 나오므로 즉시 비밀 저장소에 넣고 대화에 다시 적지 않는다.

7. 앱 연결은 `assets/client_example.py` 를 따른다. OpenAI SDK 의 `base_url` 을 게이트웨이로, `user`·`metadata.tags` 로 비용을 귀속한다.

8. 장애면 `references/ops-runbook.md` 순서를 따른다. 헬스, 죽은 엔드포인트, 폴백 동작, 제공자 상태, 키 예산 소진, 레이트 리밋 순서로 좁힌다.

## references

`azure.md`·`bedrock.md`·`vertex.md`·`vllm.md`(제공자 연결), `observability.md`(Langfuse·OTel·비용 헤더), `security.md`(키 등급·팀 예산·PII 마스킹), `ops-runbook.md`(기동·모델 추가·키 회전·장애·업그레이드).

## 하지 않는 것

- 시크릿을 config.yaml 에 인라인.
- 검증(config_validate) 없이 배포.
- 승인 없이 키 발급·차단.
- 게이트웨이 대화에 전체 키를 남기기.
