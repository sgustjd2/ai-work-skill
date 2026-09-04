# llm-mocking · LLM 호출 테스트

실제 모델을 부르지 않고 게이트웨이 경계에서 모킹한다. 테스트는 빠르고 결정적이어야 한다.

## HTTP 경계에서 모킹

`respx` 로 게이트웨이의 `/v1/chat/completions` 응답을 고정한다. 앱 코드는 그대로 두고 바깥 호출만 가로챈다.

```python
import httpx, respx


@respx.mock
def test_chat(client):
    respx.post("http://gw.test/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "model": "gpt-4o",
                "choices": [{"message": {"content": "요약 결과"}}],
                "usage": {"total_tokens": 13},
            },
            headers={"x-litellm-response-cost": "0.0012"},
        )
    )
    r = client.post("/api/v1/chat", json={"message": "요약해줘"})
    assert r.status_code == 200
```

## 스트리밍

SSE 청크를 문자열로 만들어 응답 본문에 넣는다. `data: {...}` 줄과 `data: [DONE]` 로 끝을 알린다. 파서가 델타를 이어 붙이는지 확인한다.

## 시나리오

- 정상 응답과 사용량·비용 헤더 파싱.
- 429·503 뒤 재시도해 성공하는지(호출 횟수 확인).
- 타임아웃과 연결 실패에서 앱이 502·503 을 내는지.
- 폴백 모델의 응답 형식이 달라도 처리되는지.

## 프롬프트 골든 파일

프롬프트 렌더 결과를 `tests/golden/*.txt` 로 고정한다. 프롬프트를 바꾸면 골든 파일도 함께 바뀌므로, 리뷰에서 변경이 눈에 보인다.

## 비용·토큰

응답의 `x-litellm-response-cost` 헤더와 usage 를 파싱해 검증한다. 비용 상한을 넘는 입력이 막히는지 확인한다.
