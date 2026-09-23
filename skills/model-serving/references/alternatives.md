# alternatives · 서빙 대안

vLLM 이 기본이다. 상황에 따라 다른 도구를 본다. 버전은 2026-09-23 기준이다.

- vLLM(0.30): 처리량이 높고 OpenAI 호환이다. 모델 지원이 가장 빠르다. 대부분의 사내 서빙에 기본으로 쓴다.
- SGLang(0.5.20): 첫 번째 대안. 구조화 출력·긴 프롬프트 공유·에이전트 흐름에서 빠를 수 있다. vLLM 과 같은 모델로 `bench_llm.py` 비교해 고른다.
- Ollama(0.34)·llama.cpp: 로컬·개발용, GGUF·CPU 배포. 운영 처리량은 vLLM 이 낫다.
- NVIDIA Dynamo(1.5): vLLM·SGLang·TensorRT-LLM 을 백엔드로 쓰는 다중 노드 분산 서빙(프리필·디코드 분리). GPU 노드가 여럿일 때 본다.
- llm-d(0.9): Kubernetes 위 vLLM 분산 추론. 사내 K8s 가 있고 노드가 여럿일 때 본다.
- TensorRT-LLM(1.2.1): NVIDIA 전용 최적화. 모델 변환 부담이 있어 처리량이 꼭 필요할 때만.
- TGI: 저장소가 보관(archived) 처리됐다. 신규 도입하지 않고, 쓰고 있으면 vLLM·SGLang 으로 옮긴다.

고르는 기준은 처리량, 모델 호환, 운영 편의다. 확신이 없으면 vLLM 으로 시작하고 `bench_llm.py` 로 비교한다.
