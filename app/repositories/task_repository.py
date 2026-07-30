"""
Task Repository — the ONLY place in the codebase that touches the database for tasks.

Responsibilities:
  - Raw CRUD operations against the 'tasks' table
  - No business logic here — just data access

Why separate from the service layer?
  - Swap SQLite → PostgreSQL → any database without touching business logic
  - Easy to mock in tests (replace repository, not the database)
"""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository:
    """Data access layer for Task entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: TaskCreate) -> Task:
        """Insert a new task row and return it."""
        task = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status.value,
            priority=payload.priority.value,
        )
        self.db.add(task)
        await self.db.flush()  # get the generated id without committing
        await self.db.refresh(task)
        return task

    async def get_by_id(self, task_id: str) -> Task | None:
        """Fetch a single task by its UUID. Returns None if not found."""
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def list_all(
        self,
        status: str | None = None,
        priority: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        """
        Return a paginated list of tasks and the total count.

        Args:
            status:   filter by status (optional)
            priority: filter by priority (optional)
            skip:     number of rows to skip (offset)
            limit:    max rows to return
        """
        query = select(Task)
        count_query = select(func.count(Task.id))

        if status:
            query = query.where(Task.status == status)
            count_query = count_query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)
            count_query = count_query.where(Task.priority == priority)

        # Most recently created first
        query = query.order_by(Task.created_at.desc()).offset(skip).limit(limit)

        tasks_result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        tasks = list(tasks_result.scalars().all())
        total = count_result.scalar_one()
        return tasks, total

    async def update(self, task: Task, payload: TaskUpdate) -> Task:
        """Apply only the provided (non-None) fields to the task."""
        update_data = payload.model_dump(exclude_none=True)

        for field, value in update_data.items():
            # Convert enum values to their string representation for storage
            if hasattr(value, "value"):
                value = value.value
            setattr(task, field, value)

        # Manually set updated_at since SQLAlchemy onupdate doesn't
        # trigger on attribute assignment alone with async sessions
        task.updated_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        """Remove the task from the database."""
        await self.db.delete(task)
        await self.db.flush()
