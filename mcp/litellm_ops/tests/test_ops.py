import httpx
import pytest

from litellm_ops import core

pytestmark = pytest.mark.deterministic


def test_mask_key():
    assert core.mask_key("sk-abcdefghijklmnop").startswith("sk-")
    assert core.mask_key("sk-abcdefghijklmnop").endswith("mnop")
    assert "…" in core.mask_key("sk-abcdefghijklmnop")
    assert core.mask_key("") == ""


def test_gateway_health(ops):
    r = ops.gateway_health()
    assert r["liveness"] == "alive"
    assert r["readiness"]["status"] == "healthy"
    assert len(r["healthy"]) == 1 and len(r["unhealthy"]) == 1
    assert r["healthy"][0]["api_base"] == "x.openai.azure.com"  # host 만


def test_list_models(ops):
    r = ops.list_models()
    assert r["count"] == 1
    m = r["models"][0]
    assert m["model_name"] == "gpt-4o" and m["provider"] == "azure"
    assert m["api_base"] == "x.openai.azure.com"


def test_test_completion(ops):
    r = ops.test_completion("gpt-4o")
    assert r["sample"].startswith("pong")
    assert r["cost_usd"] == 0.0001
    assert r["usage"]["total_tokens"] == 5


def test_spend_summary(ops):
    r = ops.spend_summary("2026-09-01", "2026-09-30", "api_key")
    assert r["total_usd"] == 1.5
    assert r["rows"][0]["group"] == "sk-a"


def test_key_info_masks(ops):
    r = ops.key_info("sk-secret-abcdefghijklmnop")
    assert "…" in r["key_masked"]
    assert "secret" not in r["key_masked"]
    assert r["alias"] == "team-a" and r["team_id"] == "t1"


def test_team_info(ops):
    r = ops.team_info("t1")
    assert r["alias"] == "A" and r["keys_count"] == 2


def test_write_gate_blocks(ops):
    with pytest.raises(core.WriteDisabled):
        ops.key_create("a", ["gpt-4o"], 100)
    with pytest.raises(core.WriteDisabled):
        ops.key_block("sk-x")
    with pytest.raises(core.WriteDisabled):
        ops.team_create("t", 500)


def test_write_allowed(ops_write):
    r = ops_write.key_create("team-a", ["gpt-4o"], 100)
    assert r["key_full_once"].startswith("sk-newkey")
    assert "…" in r["key_masked"]
    assert "저장" in r["note"]
    assert ops_write.key_block("sk-x")["blocked"] is True
    assert ops_write.key_unblock("sk-x")["blocked"] is False
    assert ops_write.team_create("t", 500)["team_id"] == "t-new"


def test_api_error_raises():
    def handler(request):
        return httpx.Response(503, json={"error": "down"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://gw.test")
    o = core.LiteLLMOps("http://gw.test", "sk-m", client=client)
    with pytest.raises(core.OpsError):
        o.list_models()


def test_from_env(monkeypatch):
    monkeypatch.setenv("LITELLM_BASE_URL", "http://x:4000")
    monkeypatch.setenv("LITELLM_OPS_ALLOW_WRITE", "true")
    o = core.from_env()
    assert o.base_url == "http://x:4000" and o.allow_write is True
    o.close()
