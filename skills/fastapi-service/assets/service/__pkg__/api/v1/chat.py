"""동기 챗 엔드포인트."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends

from ...core.errors import AppError
from ...schemas.chat import ChatRequest, ChatResponse
from ...services.llm import LLMClient
from ..deps import get_llm

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, llm: LLMClient = Depends(get_llm)) -> ChatResponse:
    try:
        return await llm.chat(req.message, req.model)
    except httpx.HTTPStatusError as e:
        raise AppError("upstream_error", 502, f"게이트웨이 오류: {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise AppError("upstream_unreachable", 503, "게이트웨이에 연결할 수 없습니다.") from e
