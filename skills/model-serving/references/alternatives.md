# alternatives · 서빙 대안

vLLM 이 기본이다. 상황에 따라 다른 도구를 본다.

- vLLM: 처리량이 높고 OpenAI 호환이다. PagedAttention 으로 KV 캐시를 효율적으로 쓴다. 대부분의 사내 서빙에 기본으로 쓴다.
- TGI(Text Generation Inference): Hugging Face 생태계와 붙기 쉽다. 특정 모델·기능에서 유리할 때 본다.
- SGLang: 구조화 출력·복잡한 프롬프트 흐름에서 빠를 수 있다.
- Ollama: 로컬·소형 배포와 개발용에 편하다. 운영 처리량은 vLLM 이 낫다.

고르는 기준은 처리량, 모델 호환, 운영 편의다. 확신이 없으면 vLLM 으로 시작하고 `bench_llm.py` 로 비교한다.
