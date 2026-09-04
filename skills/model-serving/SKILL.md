---
name: model-serving
description: >
  오픈소스 LLM·VLM 을 vLLM 등으로 서빙하고 최적화한다. "vLLM", "모델 서빙", "자체 호스팅",
  "양자화(AWQ/GPTQ/FP8)", "GPU 메모리·VRAM 산정", "몇 장 필요해", "처리량·지연 벤치마크", "텐서 병렬",
  "컨텍스트 길이", "서빙 모델을 게이트웨이에 등록" 요청에 반드시 쓴다. 모델 학습·파인튜닝은 대상이 아니다.
version: 0.1.0
user-invocable: true
argument-hint: "[모델 이름 | GPU 사양 | 벤치 대상 URL]"
allowed-tools:
  - Bash(python */skills/model-serving/scripts/*.py *)
---

# model-serving

오픈소스 모델을 서빙하고 최적화한다. 상세는 `references/` 가 원본이다.

## 절차

1. VRAM 을 추정한다.
   ```
   python skills/model-serving/scripts/vram_estimate.py --params 32 --dtype fp16 --ctx 32768 --batch 8
   ```
   가중치 + KV 캐시 + 여유를 더해 GPU 수를 낸다. 배치와 컨텍스트가 KV 캐시를 좌우한다.

2. `references/sizing.md` 의 표로 GPU 수와 정밀도를 정한다. 양자화 선택은 `references/quantization.md`(AWQ·GPTQ·FP8·GGUF, 품질 손실 확인법).

3. `references/vllm.md` 로 `vllm serve` 인자를 정한다(`--dtype`, `--max-model-len`, `--tensor-parallel-size`, `--quantization`, `--gpu-memory-utilization`, `--enable-prefix-caching`).

4. 벤치한다.
   ```
   python skills/model-serving/scripts/bench_llm.py --base-url <url> --model <m> --concurrency 1,4,16 --prompt-tokens 512 --max-tokens 256
   ```
   동시성별 TTFT p50/p95, tokens/s, 실패율을 본다.

5. `llm-gateway` 로 서빙 모델을 등록한다(`hosted_vllm/` 접두사).

6. 결과를 기술 검토서로 남길지 한 번 묻는다. 남긴다면 `doc-write` 의 기술 검토서 골격을 쓴다.

## references

`vllm.md`(서빙 인자), `quantization.md`(양자화 선택), `sizing.md`(산식과 표), `alternatives.md`(TGI·Ollama·SGLang 비교).

## 하지 않는 것

- 모델 학습·파인튜닝.
- VRAM 추정 없이 GPU 수를 단정하기.
