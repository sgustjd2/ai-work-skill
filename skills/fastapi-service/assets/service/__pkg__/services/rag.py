# scaffold: with-rag
"""RAG 오케스트레이션. 수집: 청킹 -> 임베딩 -> 저장. 질의: 임베딩 -> 검색 -> 프롬프트 -> 답."""
from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import Settings
from ..infra import vector


def chunk(textval: str, size: int = 800, overlap: int = 100) -> list[str]:
    out, i = [], 0
    while i < len(textval):
        out.append(textval[i : i + size])
        i += size - overlap
    return [c for c in out if c.strip()]


async def _embed(settings: Settings, inputs: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(base_url=settings.llm_base_url.rstrip("/"),
                                 timeout=settings.request_timeout_s) as c:
        resp = await c.post("/v1/embeddings", json={"model": "text-embedding-3-small", "input": inputs})
        resp.raise_for_status()
        return [d["embedding"] for d in resp.json()["data"]]


async def ingest(session: AsyncSession, settings: Settings, doc: str, textval: str) -> int:
    await vector.ensure_schema(session)
    chunks = chunk(textval)
    embeddings = await _embed(settings, chunks)
    for content, emb in zip(chunks, embeddings, strict=False):
        await vector.add_chunk(session, doc, content, emb)
    return len(chunks)


async def ask(session: AsyncSession, settings: Settings, question: str, k: int = 5) -> dict:
    emb = (await _embed(settings, [question]))[0]
    hits = await vector.search(session, emb, k)
    context = "\n\n".join(f"[{h['doc']}] {h['content']}" for h in hits)
    prompt = f"다음 자료만 근거로 답하고 출처를 []로 표기한다.\n\n{context}\n\n질문: {question}"
    async with httpx.AsyncClient(base_url=settings.llm_base_url.rstrip("/"),
                                 timeout=settings.request_timeout_s) as c:
        resp = await c.post("/v1/chat/completions",
                            json={"model": settings.llm_default_model,
                                  "messages": [{"role": "user", "content": prompt}]})
        resp.raise_for_status()
        answer = resp.json()["choices"][0]["message"]["content"]
    return {"answer": answer, "sources": [h["doc"] for h in hits]}
