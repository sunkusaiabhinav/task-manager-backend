"""
Task Service — business logic layer.

Responsibilities:
  - Orchestrate repository calls
  - Enforce business rules
  - Raise meaningful HTTP exceptions (not the repository's job)
  - Keep route handlers thin

Why separate from routes?
  - Routes only deal with HTTP (request in, response out)
  - This layer contains the actual application logic
  - Business rules tested here independently of HTTP
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (TaskCreate, TaskListResponse, TaskResponse,
                              TaskUpdate)


class TaskService:
    """Encapsulates all business operations for tasks."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = TaskRepository(db)

    async def create_task(self, payload: TaskCreate) -> TaskResponse:
        """Create and persist a new task."""
        task = await self.repo.create(payload)
        return TaskResponse.model_validate(task)

    async def get_task(self, task_id: str) -> TaskResponse:
        """
        Fetch a task by ID.
        Raises 404 if not found.
        """
        task = await self._get_or_404(task_id)
        return TaskResponse.model_validate(task)

    async def list_tasks(
        self,
        status: str | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> TaskListResponse:
        """Return a paginated, optionally filtered list of tasks."""
        tasks, total = await self.repo.list_all(
            status=status,
            priority=priority,
            skip=skip,
            limit=limit,
        )
        return TaskListResponse(
            items=[TaskResponse.model_validate(t) for t in tasks],
            total=total,
        )

    async def update_task(self, task_id: str, payload: TaskUpdate) -> TaskResponse:
        """
        Partially update a task.
        Raises 404 if not found.
        Raises 400 if payload contains no fields to update.
        """
        # Guard: reject empty payloads
        if not payload.model_dump(exclude_none=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update.",
            )

        task = await self._get_or_404(task_id)
        updated = await self.repo.update(task, payload)
        return TaskResponse.model_validate(updated)

    async def delete_task(self, task_id: str) -> None:
        """
        Delete a task by ID.
        Raises 404 if not found.
        """
        task = await self._get_or_404(task_id)
        await self.repo.delete(task)

    # ── Private helpers ───────────────────────────────────────────────────

    async def _get_or_404(self, task_id: str) -> Task:
        """Fetch task or raise HTTP 404 with a descriptive message."""
        task = await self.repo.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id '{task_id}' was not found.",
            )
        return task
