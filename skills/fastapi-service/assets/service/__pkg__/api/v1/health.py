"""헬스체크. /healthz 는 항상 200, /readyz 는 게이트웨이 연결을 확인한다."""
from __future__ import annotations

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    llm = request.app.state.llm
    ok = True
    detail = {}
    try:
        resp = await llm._client.get("/health/readiness")
        detail["gateway"] = resp.status_code
        ok = resp.status_code < 500
    except httpx.HTTPError as e:
        ok = False
        detail["gateway"] = str(e)
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ready" if ok else "degraded", **detail})
