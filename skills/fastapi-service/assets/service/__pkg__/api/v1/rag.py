# scaffold: with-rag
"""RAG 엔드포인트. /ingest 로 문서를 넣고 /ask 로 인용 포함 답을 받는다."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...infra.db import get_session
from ...services import rag

router = APIRouter(prefix="/rag", tags=["rag"])


class IngestRequest(BaseModel):
    doc: str
    text: str


class AskRequest(BaseModel):
    question: str
    k: int = 5


@router.post("/ingest")
async def ingest(req: IngestRequest, request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    n = await rag.ingest(session, request.app.state.settings, req.doc, req.text)
    return {"chunks": n}


@router.post("/ask")
async def ask(req: AskRequest, request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    return await rag.ask(session, request.app.state.settings, req.question, req.k)
