# scaffold: with-rag
"""pgvector 저장·검색. 청크와 임베딩을 저장하고 코사인 유사도로 상위 k 개를 찾는다.

# ponytail: 최소 구현. 실제로는 인덱스(ivfflat/hnsw)와 배치 삽입을 더한다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DDL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    doc TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536)
);
"""


async def ensure_schema(session: AsyncSession) -> None:
    for stmt in DDL.strip().split(";"):
        if stmt.strip():
            await session.execute(text(stmt))
    await session.commit()


async def add_chunk(session: AsyncSession, doc: str, content: str, embedding: list[float]) -> None:
    await session.execute(
        text("INSERT INTO chunks (doc, content, embedding) VALUES (:d, :c, :e)"),
        {"d": doc, "c": content, "e": str(embedding)},
    )
    await session.commit()


async def search(session: AsyncSession, embedding: list[float], k: int = 5) -> list[dict]:
    rows = await session.execute(
        text("SELECT doc, content FROM chunks ORDER BY embedding <=> :e LIMIT :k"),
        {"e": str(embedding), "k": k},
    )
    return [{"doc": r[0], "content": r[1]} for r in rows.fetchall()]
