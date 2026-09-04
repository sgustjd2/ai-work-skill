# scaffold: with-sse
import httpx
import respx


@respx.mock
def test_chat_stream(client):
    sse = (
        'data: {"choices":[{"delta":{"content":"안"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"녕"}}]}\n\n'
        "data: [DONE]\n\n"
    )
    respx.post("http://gw.test/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=sse, headers={"content-type": "text/event-stream"})
    )
    with client.stream("POST", "/api/v1/chat/stream", json={"message": "인사해줘"}) as r:
        body = "".join(r.iter_text())
    assert "event: delta" in body
    assert "event: done" in body
