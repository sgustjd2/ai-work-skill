# scaffold: with-jobs
"""장기 작업 엔드포인트. POST 는 202 + job_id, GET 은 상태·결과."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...core.errors import AppError
from ...services.jobs import JobStore, submit

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _store(request: Request) -> JobStore:
    if not hasattr(request.app.state, "jobs"):
        request.app.state.jobs = JobStore()
    return request.app.state.jobs


@router.post("", status_code=202)
async def create_job(request: Request) -> JSONResponse:
    async def work():
        await asyncio.sleep(0)
        return {"done": True}

    job = submit(_store(request), work)
    return JSONResponse(status_code=202, content={"job_id": job.id, "status": job.status})


@router.get("/{job_id}")
async def get_job(job_id: str, request: Request) -> dict:
    job = _store(request).get(job_id)
    if not job:
        raise AppError("not_found", 404, "작업을 찾을 수 없습니다.")
    return {"job_id": job.id, "status": job.status, "result": job.result, "error": job.error}
