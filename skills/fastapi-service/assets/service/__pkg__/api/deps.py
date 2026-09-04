"""의존성. 앱 상태에 보관한 LLM 클라이언트를 핸들러에 주입한다."""
from __future__ import annotations

from fastapi import Request

from ..services.llm import LLMClient


def get_llm(request: Request) -> LLMClient:
    return request.app.state.llm
