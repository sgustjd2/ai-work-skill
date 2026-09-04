# vllm · vLLM 서빙 인자

`vllm serve <모델>` 로 OpenAI 호환 서버를 띄운다. 주요 인자다.

- `--dtype`: `auto`·`bfloat16`·`float16`. 가중치 정밀도.
- `--max-model-len`: 최대 컨텍스트. KV 캐시가 이 값에 비례한다. 필요보다 크게 잡지 않는다.
- `--tensor-parallel-size`: GPU 여러 장에 모델을 나눈다. GPU 수와 맞춘다.
- `--quantization`: `awq`·`gptq`·`fp8`. 가중치를 줄여 더 큰 모델을 올린다.
- `--gpu-memory-utilization`: 0.9 기본. KV 캐시 여유를 남긴다.
- `--enable-prefix-caching`: 공통 프롬프트 접두사를 캐시해 처리량을 올린다.
- `--served-model-name`: 게이트웨이의 `hosted_vllm/<이름>` 과 맞춘다.

## 확인

기동 뒤 `curl http://localhost:8000/v1/models` 로 모델이 뜨는지 본다. VRAM 이 부족하면 `--max-model-len` 을 줄이거나 양자화를 켠다. 처리량은 `bench_llm.py` 로 잰다.
