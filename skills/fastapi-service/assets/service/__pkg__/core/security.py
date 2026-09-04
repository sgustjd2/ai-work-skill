# scaffold: with-auth
"""API 키 인증. 키 목록은 환경변수(APP_API_KEYS, 쉼표 구분). 상수 시간 비교.

SSO/JWT 는 references/python-conventions.md 와 llm-gateway 보안 문서를 따른다.
"""
from __future__ import annotations

import hmac
import os

from fastapi import Header

from .errors import AppError


def _valid_keys() -> set[str]:
    return {k.strip() for k in os.environ.get("APP_API_KEYS", "").split(",") if k.strip()}


async def require_api_key(x_api_key: str = Header(default="")) -> None:
    keys = _valid_keys()
    if not keys:
        return  # 키가 설정되지 않으면 개방(로컬 개발)
    if not any(hmac.compare_digest(x_api_key, k) for k in keys):
        raise AppError("unauthorized", 401, "유효한 API 키가 필요합니다.")
