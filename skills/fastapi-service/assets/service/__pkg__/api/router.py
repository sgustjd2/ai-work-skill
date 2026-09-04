"""API 라우터 조립. 옵션 모듈(chat_stream, jobs, rag)은 있으면 자동으로 포함한다."""
from __future__ import annotations

import importlib

from fastapi import APIRouter

from .v1 import chat, health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(chat.router)

# 스캐폴드 옵션으로 생성된 경우에만 포함(없으면 조용히 건너뜀).
for _name in ("chat_stream", "jobs", "rag"):
    try:
        _mod = importlib.import_module(f"{__package__}.v1.{_name}")
    except ImportError:
        continue
    api_router.include_router(_mod.router)
