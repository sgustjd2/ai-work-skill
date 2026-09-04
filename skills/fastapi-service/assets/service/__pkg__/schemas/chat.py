"""요청·응답 스키마(pydantic v2). OpenAPI 예시를 포함한다."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000, description="사용자 입력")
    model: str | None = Field(default=None, description="모델 이름(생략 시 기본값)")

    model_config = {"json_schema_extra": {"examples": [{"message": "회의록을 3줄로 요약해줘"}]}}


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    text: str
    model: str
    usage: Usage
    cost_usd: float | None = None
