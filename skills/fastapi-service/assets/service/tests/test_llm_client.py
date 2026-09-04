import httpx
import pytest
import respx

from {{pkg}}.core.config import Settings
from {{pkg}}.services.llm import LLMClient
from {{pkg}}.services.prompts import load_prompts

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _settings():
    return Settings(llm_base_url="http://gw.test", llm_api_key="test-key", request_timeout_s=5)


@respx.mock
async def test_retry_then_success():
    route = respx.post("http://gw.test/v1/chat/completions").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(200, json={"model": "m", "choices": [{"message": {"content": "ok"}}], "usage": {}}),
        ]
    )
    llm = LLMClient(_settings())
    try:
        res = await llm.chat("안녕")
        assert res.text == "ok"
        assert route.call_count == 2  # 503 후 재시도
    finally:
        await llm.aclose()


def test_prompt_loader_missing_var(tmp_path):
    (tmp_path / "p.md").write_text(
        "---\nname: p\nversion: 1\nvariables: [x]\n---\n값은 $x 다\n", encoding="utf-8"
    )
    prompts = load_prompts(tmp_path)
    assert prompts["p"].render(x="A") == "값은 A 다"
    with pytest.raises(KeyError):
        prompts["p"].render()
