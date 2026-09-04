# vllm · 사내 vLLM 등록

사내 GPU 에서 vLLM 으로 서빙하는 모델을 게이트웨이에 붙인다. 서빙 자체는 model-serving 스킬이 다룬다.

## model_list 항목

vLLM 은 OpenAI 호환 서버다. `model` 접두사는 `hosted_vllm/` 를 쓰고 `api_base` 로 서버 주소를 준다.

```yaml
- model_name: internal-llm
  litellm_params:
    model: hosted_vllm/Qwen2.5-32B-Instruct
    api_base: os.environ/VLLM_BASE_URL   # 예: http://vllm:8000/v1
```

## 확인할 것

- vLLM 의 `--served-model-name` 이 `model` 의 슬래시 뒤 이름과 맞는가.
- 게이트웨이에서 vLLM 서버까지 네트워크가 닿는가. compose 라면 같은 네트워크에 둔다.
- 사내 모델을 폴백 대상에 넣을 때는 응답 형식이 상용 모델과 달라질 수 있으니 골든 테스트로 확인한다.
