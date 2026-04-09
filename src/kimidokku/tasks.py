"""Background task tracking module."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Coroutine, Optional
from uuid import uuid4

from kimidokku.database import db


class TaskStatus(Enum):
    """Background task status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BackgroundTask:
    """Represents a tracked background task."""

    id: str
    task_type: str
    app_name: Optional[str]
    deploy_id: Optional[int]
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    asyncio_task: Optional[asyncio.Task] = field(default=None, repr=False)


class TaskManager:
    """Manages and tracks background tasks."""

    def __init__(self):
        self._tasks: dict[str, BackgroundTask] = {}
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        task_type: str,
        coro: Coroutine,
        app_name: Optional[str] = None,
        deploy_id: Optional[int] = None,
    ) -> BackgroundTask:
        """Create and track a new background task."""
        task_id = str(uuid4())
        task = BackgroundTask(
            id=task_id,
            task_type=task_type,
            app_name=app_name,
            deploy_id=deploy_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
        )

        async with self._lock:
            self._tasks[task_id] = task

        # Store in database
        await db.execute(
            """
            INSERT INTO background_tasks (id, task_type, app_name, deploy_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                task_type,
                app_name,
                deploy_id,
                task.status.value,
                task.created_at.isoformat(),
            ),
        )

        # Create asyncio task with wrapper for tracking
        asyncio_task = asyncio.create_task(self._run_task_wrapper(task_id, coro))
        task.asyncio_task = asyncio_task

        return task

    async def _run_task_wrapper(self, task_id: str, coro: Coroutine) -> None:
        """Wrapper that tracks task execution."""
        task = self._tasks.get(task_id)
        if not task:
            return

        # Update to running
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        await db.execute(
            "UPDATE background_tasks SET status = ?, started_at = ? WHERE id = ?",
            (TaskStatus.RUNNING.value, task.started_at.isoformat(), task_id),
        )

        try:
            await coro
            # Success
            task.status = TaskStatus.SUCCESS
            task.finished_at = datetime.now()
            await db.execute(
                "UPDATE background_tasks SET status = ?, finished_at = ? WHERE id = ?",
                (TaskStatus.SUCCESS.value, task.finished_at.isoformat(), task_id),
            )
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.finished_at = datetime.now()
            await db.execute(
                "UPDATE background_tasks SET status = ?, finished_at = ? WHERE id = ?",
                (TaskStatus.CANCELLED.value, task.finished_at.isoformat(), task_id),
            )
            raise
        except Exception as e:
            # Failed
            task.status = TaskStatus.FAILED
            task.finished_at = datetime.now()
            error_msg = str(e)
            task.error_message = error_msg
            await db.execute(
                """
                UPDATE background_tasks 
                SET status = ?, finished_at = ?, error_message = ? 
                WHERE id = ?
                """,
                (TaskStatus.FAILED.value, task.finished_at.isoformat(), error_msg, task_id),
            )

    async def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID."""
        async with self._lock:
            return self._tasks.get(task_id)

    async def get_tasks(
        self,
        app_name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
    ) -> list[BackgroundTask]:
        """Get tasks with optional filtering."""
        async with self._lock:
            tasks = list(self._tasks.values())

        if app_name:
            tasks = [t for t in tasks if t.app_name == app_name]
        if status:
            tasks = [t for t in tasks if t.status == status]

        return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task or not task.asyncio_task:
                return False

            task.asyncio_task.cancel()
            return True

    async def cleanup_completed(self, max_age_hours: int = 24) -> int:
        """Remove completed tasks older than max_age_hours from memory."""
        cutoff = datetime.now() - __import__("datetime").timedelta(hours=max_age_hours)
        removed = 0

        async with self._lock:
            to_remove = [
                tid
                for tid, t in self._tasks.items()
                if t.status in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED)
                and t.finished_at
                and t.finished_at < cutoff
            ]
            for tid in to_remove:
                del self._tasks[tid]
                removed += 1

        return removed


# Global task manager instance
task_manager = TaskManager()
