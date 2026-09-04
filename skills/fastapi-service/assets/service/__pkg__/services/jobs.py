# scaffold: with-jobs
"""인프로세스 비동기 작업 큐. 상태: queued -> running -> done|failed.

# ponytail: 단일 프로세스 큐. 다중 워커면 Redis 큐(Arq/Dramatiq)로 교체.
"""
from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class Job:
    id: str
    status: str = "queued"
    result: Any = None
    error: str | None = None


@dataclass
class JobStore:
    jobs: dict[str, Job] = field(default_factory=dict)

    def create(self) -> Job:
        job = Job(id=uuid.uuid4().hex[:16])
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self.jobs.get(job_id)

    async def run(self, job: Job, coro: Callable[[], Awaitable[Any]]) -> None:
        job.status = "running"
        try:
            job.result = await coro()
            job.status = "done"
        except Exception as e:  # noqa: BLE001 - 작업 실패를 상태로 남긴다
            job.status = "failed"
            job.error = str(e)


def submit(store: JobStore, coro: Callable[[], Awaitable[Any]]) -> Job:
    job = store.create()
    asyncio.create_task(store.run(job, coro))
    return job
