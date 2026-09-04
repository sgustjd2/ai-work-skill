---
name: py-test
description: >
  Python·FastAPI·LLM 서비스의 pytest 테스트를 만들고 정리한다. "테스트 작성", "단위 테스트", "커버리지 올려줘",
  "테스트 없는 함수 찾아줘", "LLM 호출 모킹", "스트리밍 테스트", "골든 파일 테스트", "픽스처 정리", "테스트 실패 분석"
  요청에 반드시 쓴다. HTTP 경계에서 모킹(respx)하고 실제 LLM 호출은 live_llm 마커로 격리한다.
  성능 벤치마크는 model-serving 이 담당한다.
version: 0.1.0
user-invocable: true
argument-hint: "[대상 모듈·함수 | 실패 로그]"
allowed-tools:
  - Bash(uv run pytest *)
  - Bash(python */skills/py-test/scripts/test_gaps.py *)
---

# py-test

pytest 테스트를 만든다. 규약은 `references/pytest-conventions.md` 가 원본이다.

## 절차

1. `scripts/test_gaps.py <pkg>` 로 테스트에서 참조되지 않는 공개 함수를 본다. 이름 기반 휴리스틱이므로 참고로만 쓴다.

2. 우선순위대로 쓴다. 서비스 로직, 그다음 API 계약, 그다음 인프라 어댑터.

3. `references/pytest-conventions.md` 를 읽는다. AAA, 이름 규칙, 파라미터화, 픽스처 범위, 마커를 따른다.

4. LLM 관련이면 `references/llm-mocking.md` 를 읽는다. respx 로 게이트웨이 응답을 고정하고, 스트리밍·429·타임아웃·폴백·비용 헤더 시나리오를 다룬다. 프롬프트 렌더는 골든 파일로 고정한다.

5. 실행한다. 실패는 원인별로 고친다. 테스트를 약하게 만들어 통과시키지 않는다.

6. 결과를 표로 낸다. 추가 테스트 수와 커버리지 전후.

## 하지 않는 것

- 검증을 약하게 만들어 통과시키기.
- 실제 게이트웨이에 붙는 테스트를 기본 스위트에 두기(`live_llm` 격리).
- 시간·난수·네트워크 의존 테스트.
