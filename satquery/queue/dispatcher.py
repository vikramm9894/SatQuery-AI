"""
satquery.queue.dispatcher
=========================
Async Task Queue & Job Dispatcher (Section 28).
Prevents long-running satellite analysis jobs from blocking HTTP requests.
Accepts jobs returning HTTP 202 Accepted, dispatches to async workers,
and provides live progress and execution trace polling/streaming.
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional

logger = logging.getLogger(__name__)


class JobRecord:
    def __init__(self, job_id: str, query: str, session_id: str):
        self.job_id = job_id
        self.query = query
        self.session_id = session_id
        self.status = "queued"  # queued, running, completed, failed
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.trace_events: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "session_id": self.session_id,
            "query": self.query,
            "status": self.status,
            "has_result": self.result is not None,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "event_count": len(self.trace_events)
        }


class JobDispatcher:
    """
    Asynchronous in-memory job queue with Redis-ready interface.
    """

    def __init__(self):
        self._jobs: Dict[str, JobRecord] = {}

    def submit_job(
        self,
        query: str,
        session_id: str,
        coroutine_fn: Callable[[str], Coroutine[Any, Any, Dict[str, Any]]]
    ) -> JobRecord:
        """
        Enqueues an asynchronous analysis task and triggers background execution.
        Returns JobRecord with status='queued' immediately (HTTP 202 Accepted).
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = JobRecord(job_id=job_id, query=query, session_id=session_id)
        self._jobs[job_id] = job

        # Fire background task if event loop is running
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._worker(job, coroutine_fn))
        except RuntimeError:
            # No running loop; can be executed via process_job_now
            pass
        return job

    async def process_job_now(
        self,
        job_id: str,
        coroutine_fn: Callable[[str], Coroutine[Any, Any, Dict[str, Any]]]
    ) -> JobRecord:
        job = self._jobs.get(job_id)
        if job:
            await self._worker(job, coroutine_fn)
        return job

    async def _worker(
        self,
        job: JobRecord,
        coroutine_fn: Callable[[str], Coroutine[Any, Any, Dict[str, Any]]]
    ) -> None:
        job.status = "running"
        try:
            res = await coroutine_fn(job.job_id)
            job.status = "completed"
            job.result = res
            job.completed_at = time.time()
        except Exception as e:
            logger.exception("Job %s execution failed: %s", job.job_id, e)
            job.status = "failed"
            job.error = str(e)
            job.completed_at = time.time()

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def append_trace_event(self, job_id: str, event: Dict[str, Any]) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.trace_events.append(event)


dispatcher = JobDispatcher()
