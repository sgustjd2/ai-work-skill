# scaffold: with-redis
"""redis.asyncio 클라이언트. URL 은 환경변수(APP_REDIS_URL)."""
from __future__ import annotations

import os

import redis.asyncio as redis

_URL = os.environ.get("APP_REDIS_URL", "redis://localhost:6379/0")


def get_redis() -> "redis.Redis":
    return redis.from_url(_URL, encoding="utf-8", decode_responses=True)
