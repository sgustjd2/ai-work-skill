import pytest

from litellm_ops import validate

pytestmark = pytest.mark.deterministic

GOOD = """
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: azure/gpt-4o
      api_key: os.environ/AZURE_API_KEY
      api_base: os.environ/AZURE_API_BASE
  - model_name: claude
    litellm_params:
      model: bedrock/anthropic.claude-3-sonnet-20240229-v1:0
litellm_settings:
  fallbacks:
    - gpt-4o: [claude]
router_settings:
  routing_strategy: simple-shuffle
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  background_health_checks: true
"""


def _write(tmp_path, text, name="config.yaml", env_example=None):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    if env_example:
        (tmp_path / ".env.example").write_text(env_example, encoding="utf-8")
    return str(p)


def test_valid_config(tmp_path):
    path = _write(
        tmp_path, GOOD, env_example="AZURE_API_KEY=x\nAZURE_API_BASE=x\nLITELLM_MASTER_KEY=x\n"
    )
    r = validate.config_validate(path)
    errors = [f for f in r["findings"] if f["level"] == "error"]
    assert r["ok"] and not errors, r["findings"]


def test_v1_bad_yaml(tmp_path):
    r = validate.config_validate(_write(tmp_path, "model_list: [\n  - broken"))
    assert not r["ok"] and r["findings"][0]["code"] == "V1"


def test_v2_empty_model_list(tmp_path):
    r = validate.config_validate(_write(tmp_path, "model_list: []\n"))
    assert any(f["code"] == "V2" for f in r["findings"])


def test_v3_unknown_provider(tmp_path):
    text = "model_list:\n  - model_name: x\n    litellm_params:\n      model: weirdvendor/x\n"
    r = validate.config_validate(_write(tmp_path, text))
    assert any(f["code"] == "V3" for f in r["findings"])


def test_v4_inline_secret(tmp_path):
    text = (
        "model_list:\n  - model_name: x\n    litellm_params:\n"
        "      model: openai/gpt-4o\n      api_key: sk-abcdefghijklmnopqrstuvwxyz123\n"
    )
    r = validate.config_validate(_write(tmp_path, text))
    assert any(f["code"] == "V4" and f["level"] == "error" for f in r["findings"])
    assert not r["ok"]


def test_v5_missing_env(tmp_path):
    text = (
        "model_list:\n  - model_name: x\n    litellm_params:\n"
        "      model: openai/gpt-4o\n      api_key: os.environ/NOPE_MISSING_VAR\n"
    )
    r = validate.config_validate(_write(tmp_path, text))
    assert any(f["code"] == "V5" for f in r["findings"])


def test_v6_bad_fallback(tmp_path):
    text = GOOD.replace("- gpt-4o: [claude]", "- gpt-4o: [ghost-model]")
    r = validate.config_validate(
        _write(
            tmp_path, text, env_example="AZURE_API_KEY=x\nAZURE_API_BASE=x\nLITELLM_MASTER_KEY=x\n"
        )
    )
    assert any(f["code"] == "V6" and "ghost-model" in f["message"] for f in r["findings"])
    assert not r["ok"]


def test_v7_bad_routing(tmp_path):
    text = GOOD.replace("simple-shuffle", "made-up-strategy")
    r = validate.config_validate(
        _write(
            tmp_path, text, env_example="AZURE_API_KEY=x\nAZURE_API_BASE=x\nLITELLM_MASTER_KEY=x\n"
        )
    )
    assert any(f["code"] == "V7" for f in r["findings"])


def test_v8_no_master_key(tmp_path):
    text = (
        "model_list:\n  - model_name: x\n    litellm_params:\n      model: openai/gpt-4o\n"
        "general_settings:\n  background_health_checks: true\n"
    )
    r = validate.config_validate(_write(tmp_path, text))
    assert any(f["code"] == "V8" for f in r["findings"])


def test_config_diff(tmp_path):
    a = _write(tmp_path, GOOD, name="a.yaml")
    b_text = GOOD.replace("routing_strategy: simple-shuffle", "routing_strategy: least-busy")
    b = _write(tmp_path, b_text, name="b.yaml")
    d = validate.config_diff(a, b)
    assert any(c["path"] == "router_settings" for c in d["changed"])
