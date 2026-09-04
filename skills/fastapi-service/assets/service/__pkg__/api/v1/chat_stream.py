# scaffold: with-sse
"""SSE 스트리밍 챗. event: delta | done | error."""
from __future__ import annotations

import json

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ...schemas.chat import ChatRequest
from ...services.llm import LLMClient
from ..deps import get_llm

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def chat_stream(req: ChatRequest, llm: LLMClient = Depends(get_llm)) -> StreamingResponse:
    async def gen():
        try:
            async for delta in llm.stream(req.message, req.model):
                yield f"event: delta\ndata: {json.dumps({'text': delta}, ensure_ascii=False)}\n\n"
            yield "event: done\ndata: {}\n\n"
        except httpx.HTTPError as e:
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
