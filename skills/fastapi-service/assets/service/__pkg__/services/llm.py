"""LLM 게이트웨이(LiteLLM) 클라이언트. 벤더 SDK 를 직접 부르지 않고 게이트웨이만 부른다.

OpenAI 호환 /chat/completions 를 httpx 로 호출한다. 타임아웃과 재시도(429/5xx)를 둔다.
요청마다 user·metadata(서비스명·환경·request_id)를 게이트웨이에 넘겨 비용 귀속·추적을 돕는다.
"""
from __future__ import annotations

import asyncio

import httpx

from ..core.config import Settings
from ..core.logging import request_id_var
from ..schemas.chat import ChatResponse, Usage

_RETRY_STATUS = {429, 500, 502, 503, 504}


class LLMClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self.settings = settings
        self._client = client or httpx.AsyncClient(
            base_url=settings.llm_base_url.rstrip("/"),
            timeout=settings.request_timeout_s,
            headers={"Authorization": f"Bearer {settings.llm_api_key.get_secret_value()}"},
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _payload(self, message: str, model: str, stream: bool) -> dict:
        return {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": stream,
            "user": "service",
            "metadata": {
                "service": self.settings.app_name,
                "env": self.settings.env,
                "request_id": request_id_var.get(),
            },
        }

    async def _post(self, payload: dict) -> httpx.Response:
        last: httpx.Response | None = None
        for attempt in range(3):
            resp = await self._client.post("/v1/chat/completions", json=payload)
            if resp.status_code not in _RETRY_STATUS:
                return resp
            last = resp
            await asyncio.sleep(0.2 * (2**attempt))
        return last  # type: ignore[return-value]

    async def chat(self, message: str, model: str | None = None) -> ChatResponse:
        model = model or self.settings.llm_default_model
        resp = await self._post(self._payload(message, model, stream=False))
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {}) or {}
        cost = resp.headers.get("x-litellm-response-cost")
        return ChatResponse(
            text=text,
            model=data.get("model", model),
            usage=Usage(**{k: usage.get(k, 0) for k in ("prompt_tokens", "completion_tokens", "total_tokens")}),
            cost_usd=float(cost) if cost else None,
        )

    async def stream(self, message: str, model: str | None = None):
        """SSE 청크(text/event-stream)를 델타 문자열로 흘려보낸다."""
        model = model or self.settings.llm_default_model
        payload = self._payload(message, model, stream=True)
        async with self._client.stream("POST", "/v1/chat/completions", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data:"):
                    continue
                chunk = line[len("data:"):].strip()
                if chunk == "[DONE]":
                    return
                import json

                try:
                    delta = json.loads(chunk)["choices"][0]["delta"].get("content")
                except (KeyError, IndexError, ValueError):
                    continue
                if delta:
                    yield delta
