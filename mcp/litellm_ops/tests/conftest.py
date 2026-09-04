import httpx
import pytest


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/health/liveliness":
        return httpx.Response(200, text="I'm alive!")
    if path == "/health/readiness":
        return httpx.Response(200, json={"status": "healthy", "db": "connected"})
    if path == "/health":
        return httpx.Response(
            200,
            json={
                "healthy_endpoints": [
                    {"model": "gpt-4o", "api_base": "https://x.openai.azure.com/"}
                ],
                "unhealthy_endpoints": [
                    {"model": "gpt-4o", "api_base": "https://y.openai.azure.com/"}
                ],
            },
        )
    if path == "/model/info":
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "model_name": "gpt-4o",
                        "litellm_params": {
                            "model": "azure/gpt-4o",
                            "api_base": "https://x.openai.azure.com/",
                            "rpm": 300,
                        },
                        "model_info": {"id": "abc"},
                    }
                ]
            },
        )
    if path == "/v1/chat/completions":
        return httpx.Response(
            200,
            json={
                "model": "gpt-4o",
                "choices": [{"message": {"content": "pong 응답"}}],
                "usage": {"total_tokens": 5},
            },
            headers={"x-litellm-response-cost": "0.0001"},
        )
    if path == "/global/spend/report":
        return httpx.Response(200, json=[{"api_key": "sk-a", "spend": 1.5, "total_tokens": 1000}])
    if path == "/spend/logs":
        return httpx.Response(200, json=[{"api_key": "sk-a", "spend": 0.5, "total_tokens": 300}])
    if path == "/key/info":
        return httpx.Response(
            200,
            json={
                "info": {
                    "key_alias": "team-a",
                    "spend": 1.2,
                    "max_budget": 100,
                    "models": ["gpt-4o"],
                    "team_id": "t1",
                    "blocked": False,
                }
            },
        )
    if path == "/team/info":
        return httpx.Response(
            200,
            json={
                "team_info": {
                    "team_alias": "A",
                    "spend": 5,
                    "max_budget": 500,
                    "models": [],
                    "keys": [1, 2],
                }
            },
        )
    if path == "/key/generate":
        return httpx.Response(200, json={"key": "sk-newkeyabcdefghijklmnop1234"})
    if path == "/key/block":
        return httpx.Response(200, json={"blocked": True})
    if path == "/key/unblock":
        return httpx.Response(200, json={"blocked": False})
    if path == "/team/new":
        return httpx.Response(200, json={"team_id": "t-new"})
    return httpx.Response(404, json={"error": "not found"})


@pytest.fixture
def client():
    return httpx.Client(transport=httpx.MockTransport(_handler), base_url="http://gw.test")


@pytest.fixture
def ops(client):
    from litellm_ops.core import LiteLLMOps

    return LiteLLMOps(base_url="http://gw.test", master_key="sk-master", client=client)


@pytest.fixture
def ops_write(client):
    from litellm_ops.core import LiteLLMOps

    return LiteLLMOps(
        base_url="http://gw.test", master_key="sk-master", allow_write=True, client=client
    )
