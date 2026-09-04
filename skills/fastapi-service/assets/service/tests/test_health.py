import httpx
import respx


def test_healthz(client):
    r = client.get("/api/v1/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "X-Request-ID" in r.headers


@respx.mock
def test_readyz_ok(client):
    respx.get("http://gw.test/health/readiness").mock(return_value=httpx.Response(200, json={"status": "healthy"}))
    r = client.get("/api/v1/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


@respx.mock
def test_readyz_degraded(client):
    respx.get("http://gw.test/health/readiness").mock(side_effect=httpx.ConnectError("down"))
    r = client.get("/api/v1/readyz")
    assert r.status_code == 503
