# scaffold: with-db
"""SQLAlchemy 2 async 엔진과 세션 의존성. DSN 은 환경변수(APP_DATABASE_URL)."""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_DSN = os.environ.get("APP_DATABASE_URL", "postgresql+asyncpg://app:app@localhost:5432/app")
engine = create_async_engine(_DSN, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with Session() as session:
        yield session
