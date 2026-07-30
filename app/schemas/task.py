"""
Pydantic schemas — define what the API accepts and returns.

Separate from ORM models intentionally:
  - ORM models = database shape
  - Schemas = API contract shape

These two can (and should) differ. For example, the API never
exposes internal database fields directly.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# ── Enums ─────────────────────────────────────────────────────────────────


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ── Request schemas (what the client sends) ───────────────────────────────


class TaskCreate(BaseModel):
    """Payload required to create a new task."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        examples=["Set up CI/CD pipeline"],
        description="Short descriptive title for the task",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        examples=["Configure GitHub Actions with lint, test, and Docker build jobs."],
        description="Optional longer description",
    )
    status: TaskStatus = Field(
        default=TaskStatus.todo,
        description="Current status of the task",
    )
    priority: TaskPriority = Field(
        default=TaskPriority.medium,
        description="Priority level",
    )


class TaskUpdate(BaseModel):
    """
    All fields optional — allows partial updates (PATCH semantics).
    Only provided fields will be updated.
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    status: TaskStatus | None = None
    priority: TaskPriority | None = None


# ── Response schemas (what the API returns) ───────────────────────────────


class TaskResponse(BaseModel):
    """Full task representation returned from the API."""

    model_config = ConfigDict(from_attributes=True)  # allows ORM → schema conversion

    id: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    items: list[TaskResponse]
    total: int


# ── Health schema ─────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Response shape for GET /health."""

    status: str
    app_name: str
    environment: str
    version: str = "1.0.0"
