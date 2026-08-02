"""
Task API routes — thin HTTP handlers only.

Each handler:
  1. Receives validated input (Pydantic handles this automatically)
  2. Delegates to the service layer
  3. Returns the response

No business logic here. No direct DB access here.
"""

from fastapi import APIRouter, Query, status

from app.api.deps import DbSession
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
async def create_task(payload: TaskCreate, db: DbSession) -> TaskResponse:
    """
    Create a new task.

    - **title**: required, 1–200 characters
    - **description**: optional
    - **status**: todo | in_progress | done (default: todo)
    - **priority**: low | medium | high (default: medium)
    """
    return await TaskService(db).create_task(payload)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List all tasks",
)
async def list_tasks(
    db: DbSession,
    status_filter: TaskStatus | None = Query(
        default=None,
        alias="status",
        description="Filter tasks by status",
    ),
    priority_filter: TaskPriority | None = Query(
        default=None,
        alias="priority",
        description="Filter tasks by priority",
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Max records to return"),
) -> TaskListResponse:
    """
    List all tasks with optional filtering and pagination.

    Query params:
    - **status**: filter by status
    - **priority**: filter by priority
    - **skip**: offset for pagination
    - **limit**: max results (1–500)
    """
    return await TaskService(db).list_tasks(
        status=status_filter.value if status_filter else None,
        priority=priority_filter.value if priority_filter else None,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a specific task",
    responses={404: {"description": "Task not found"}},
)
async def get_task(task_id: str, db: DbSession) -> TaskResponse:
    """Retrieve a single task by its UUID."""
    return await TaskService(db).get_task(task_id)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task",
    responses={
        404: {"description": "Task not found"},
        400: {"description": "No fields provided"},
    },
)
async def update_task(task_id: str, payload: TaskUpdate, db: DbSession) -> TaskResponse:
    """
    Update one or more fields of an existing task.

    Only the fields you include in the request body will be updated.
    Omitted fields remain unchanged.
    """
    return await TaskService(db).update_task(task_id, payload)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses={404: {"description": "Task not found"}},
)
async def delete_task(task_id: str, db: DbSession) -> None:
    """Delete a task permanently. This action cannot be undone."""
    await TaskService(db).delete_task(task_id)
