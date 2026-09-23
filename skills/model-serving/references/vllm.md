# vllm · vLLM 서빙 인자

`vllm serve <모델>` 로 OpenAI 호환 서버를 띄운다. 기준은 v0.30.0(2026-09-22)이다. V1 엔진만 남았고 V0 는 없어졌다. 버전이 다르면 `vllm serve --help` 를 먼저 본다.

## 먼저 정하는 인자

- `--max-model-len`: 최대 컨텍스트. KV 캐시가 이 값에 비례한다. 필요보다 크게 잡지 않는다. `32k` 같은 표기와 `auto` 를 받는다.
- `--tensor-parallel-size`: GPU 여러 장에 모델을 나눈다. 한 노드 안의 GPU 수와 맞춘다.
- `--gpu-memory-utilization`: 기본 0.92(예전 0.9). 같은 GPU 에 다른 프로세스가 있으면 낮춘다.
- `--served-model-name`: 게이트웨이의 `hosted_vllm/<이름>` 과 맞춘다.
- `--dtype`: 보통 `auto`. 체크포인트 설정을 따른다.
- `--quantization`: 양자화 체크포인트는 설정에서 자동으로 잡히니 보통 생략한다. 원본 가중치를 올리면서 즉석 FP8 을 쓰려면 `fp8`.
- `--kv-cache-dtype fp8`: KV 캐시를 절반으로 줄인다. 정확도가 중요하면 llm-compressor 로 보정한 체크포인트를 쓴다.

## 모델에 따라 붙이는 인자

- `--reasoning-parser <이름>`: 추론 모델(Qwen3 계열 등)에 필수다. 빠지면 `<think>` 블록이 본문에 섞인다.
- `--enable-auto-tool-choice --tool-call-parser <이름>`: 툴 호출을 쓸 때. 파서 이름은 모델 카드·vLLM 레시피를 따르고 실제 호출로 확인한다.
- `--speculative-config '{"method":"mtp","num_speculative_tokens":3}'`: MTP 헤드가 있는 모델에서 지연을 줄인다.
- `--data-parallel-size`, `--enable-expert-parallel`: 큰 MoE 모델을 여러 GPU 에 펼칠 때.
- `--limit-mm-per-prompt`: 이미지 입력을 받는 VLM 에서 요청당 이미지 수를 제한한다.
- 임베딩·리랭커: `--task` 는 없어졌다. `--runner pooling` 을 쓴다(필요하면 `--convert embed`).

## 기본으로 켜져 있어 줄 필요 없는 것

- 프리픽스 캐싱: 기본 켜짐. 끌 때만 `--no-enable-prefix-caching`.
- 청크 프리필, 비동기 스케줄링: 기본 켜짐.

## 보안

`--api-key` 는 `/v1` 등 일부 경로만 막는다. 서버는 내부망에만 두고 외부 접근은 게이트웨이로만 받는다.

## 확인

기동 뒤 `curl http://localhost:8000/v1/models` 로 모델이 뜨는지 본다. VRAM 이 부족하면 `--max-model-len` 을 줄이거나, `--kv-cache-dtype fp8` 을 켜거나, 양자화 체크포인트로 바꾼다. 처리량은 `bench_llm.py` 로 잰다.

예시(Qwen3.8-27B, 1장):

```
vllm serve Qwen/Qwen3.8-27B --served-model-name qwen3.8-27b --max-model-len 32k \
  --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_xml
```
