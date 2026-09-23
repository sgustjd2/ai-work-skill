# vllm · 사내 vLLM 등록

사내 GPU 에서 vLLM 으로 서빙하는 모델을 게이트웨이에 붙인다. 서빙 자체는 model-serving 스킬이 다룬다.

## model_list 항목

vLLM 은 OpenAI 호환 서버다. `model` 접두사는 `hosted_vllm/` 를 쓰고 `api_base` 로 서버 주소를 준다. 옛 `vllm/` 접두사는 폐기됐다. 임베딩·리랭크 모델도 같은 접두사로 붙는다.

```yaml
- model_name: internal-llm
  litellm_params:
    model: hosted_vllm/qwen3.8-27b
    api_base: os.environ/VLLM_BASE_URL   # 예: http://vllm:8000/v1
```

## 확인할 것

- vLLM 의 `--served-model-name` 이 `model` 의 슬래시 뒤 이름과 맞는가.
- 추론(thinking) 모델이면 vLLM 에 `--reasoning-parser` 를 줬는가. 없으면 `<think>` 블록이 응답 본문에 섞여 나와 폴백·파서가 깨진다.
- 툴 호출을 쓰면 `--enable-auto-tool-choice --tool-call-parser <모델별>` 을 줬는가.
- 게이트웨이에서 vLLM 서버까지 네트워크가 닿는가. compose 라면 같은 네트워크에 둔다. vLLM 의 `--api-key` 는 `/v1` 등 일부 경로만 막으므로 서버를 외부에 열지 않는다.
- 사내 모델은 상용 모델보다 컨텍스트가 짧다. `context_window_fallbacks` 로 긴 요청을 상용 모델에 넘긴다. 응답 형식이 달라질 수 있으니 골든 테스트로 확인한다.
