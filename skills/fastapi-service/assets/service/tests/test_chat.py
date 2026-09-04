import httpx
import respx

_COMPLETION = {
    "model": "gpt-4o",
    "choices": [{"message": {"role": "assistant", "content": "요약 결과"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
}


@respx.mock
def test_chat_ok(client):
    route = respx.post("http://gw.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=_COMPLETION, headers={"x-litellm-response-cost": "0.0012"})
    )
    r = client.post("/api/v1/chat", json={"message": "회의록 요약해줘"})
    assert r.status_code == 200
    body = r.json()
    assert body["text"] == "요약 결과"
    assert body["usage"]["total_tokens"] == 13
    assert body["cost_usd"] == 0.0012
    # 게이트웨이에 메타데이터가 전달됐는지
    sent = route.calls.last.request
    assert b"request_id" in sent.content


def test_chat_validation(client):
    r = client.post("/api/v1/chat", json={"message": ""})
    assert r.status_code == 422


@respx.mock
def test_chat_upstream_error(client):
    respx.post("http://gw.test/v1/chat/completions").mock(return_value=httpx.Response(400, json={"error": "bad"}))
    r = client.post("/api/v1/chat", json={"message": "안녕"})
    assert r.status_code == 502
    assert r.headers["content-type"].startswith("application/problem+json")
