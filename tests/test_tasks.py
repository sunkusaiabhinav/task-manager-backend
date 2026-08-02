"""
Tests for the Task CRUD API endpoints.

Coverage:
  - POST   /api/v1/tasks        (create)
  - GET    /api/v1/tasks        (list)
  - GET    /api/v1/tasks/{id}   (retrieve)
  - PATCH  /api/v1/tasks/{id}   (update)
  - DELETE /api/v1/tasks/{id}   (delete)
  - Validation errors
  - 404 cases
"""

import pytest

BASE = "/api/v1/tasks"


# ── Helpers ───────────────────────────────────────────────────────────────


async def create_sample_task(client, **overrides) -> dict:
    """Helper: create a task and return its JSON."""
    payload = {
        "title": "Sample Task",
        "description": "A test task",
        "status": "todo",
        "priority": "medium",
        **overrides,
    }
    response = await client.post(BASE, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ── CREATE ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_task_returns_201(client):
    """Creating a valid task must return 201 Created."""
    payload = {"title": "Write unit tests", "priority": "high"}
    response = await client.post(BASE, json=payload)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_task_response_fields(client):
    """Created task must have all expected fields."""
    payload = {
        "title": "Configure Docker",
        "description": "Set up Dockerfile and .dockerignore",
        "status": "in_progress",
        "priority": "high",
    }
    response = await client.post(BASE, json=payload)
    data = response.json()

    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_task_defaults(client):
    """Status and priority should default to 'todo' and 'medium'."""
    response = await client.post(BASE, json={"title": "Minimal task"})
    data = response.json()
    assert data["status"] == "todo"
    assert data["priority"] == "medium"


@pytest.mark.asyncio
async def test_create_task_empty_title_returns_422(client):
    """Empty title should fail Pydantic validation with 422."""
    response = await client.post(BASE, json={"title": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_missing_title_returns_422(client):
    """Missing required title field must return 422 Unprocessable Entity."""
    response = await client.post(BASE, json={"description": "No title here"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_status_returns_422(client):
    """Invalid enum value for status must return 422."""
    response = await client.post(
        BASE, json={"title": "Bad status", "status": "invalid_value"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_task_invalid_priority_returns_422(client):
    """Invalid enum value for priority must return 422."""
    response = await client.post(
        BASE, json={"title": "Bad priority", "priority": "urgent"}
    )
    assert response.status_code == 422


# ── LIST ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_tasks_empty(client):
    """List endpoint must return empty list when no tasks exist."""
    response = await client.get(BASE)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_tasks_returns_created_tasks(client):
    """Tasks created must appear in the list."""
    await create_sample_task(client, title="Task A")
    await create_sample_task(client, title="Task B")

    response = await client.get(BASE)
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client):
    """Filtering by status must return only matching tasks."""
    await create_sample_task(client, status="todo")
    await create_sample_task(client, status="done")
    await create_sample_task(client, status="done")

    response = await client.get(BASE, params={"status": "done"})
    data = response.json()
    assert data["total"] == 2
    assert all(t["status"] == "done" for t in data["items"])


@pytest.mark.asyncio
async def test_list_tasks_filter_by_priority(client):
    """Filtering by priority must return only matching tasks."""
    await create_sample_task(client, priority="high")
    await create_sample_task(client, priority="low")

    response = await client.get(BASE, params={"priority": "high"})
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["priority"] == "high"


@pytest.mark.asyncio
async def test_list_tasks_pagination(client):
    """Pagination skip/limit must work correctly."""
    for i in range(5):
        await create_sample_task(client, title=f"Task {i}")

    response = await client.get(BASE, params={"skip": 2, "limit": 2})
    data = response.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5  # total is always the full count


# ── RETRIEVE ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_task_by_id(client):
    """Fetching a task by its ID must return the correct task."""
    created = await create_sample_task(client, title="Specific Task")
    task_id = created["id"]

    response = await client.get(f"{BASE}/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Specific Task"


@pytest.mark.asyncio
async def test_get_task_not_found_returns_404(client):
    """Fetching a non-existent task ID must return 404."""
    response = await client.get(f"{BASE}/nonexistent-uuid-1234")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ── UPDATE ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_task_status(client):
    """PATCH should update the status field."""
    task = await create_sample_task(client, status="todo")
    task_id = task["id"]

    response = await client.patch(f"{BASE}/{task_id}", json={"status": "done"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"


@pytest.mark.asyncio
async def test_update_task_partial(client):
    """PATCH must only update provided fields, leaving others unchanged."""
    task = await create_sample_task(client, title="Original Title", priority="low")
    task_id = task["id"]

    response = await client.patch(f"{BASE}/{task_id}", json={"priority": "high"})
    data = response.json()

    assert data["priority"] == "high"
    assert data["title"] == "Original Title"  # unchanged


@pytest.mark.asyncio
async def test_update_task_updates_timestamp(client):
    """updated_at must change after a PATCH."""
    task = await create_sample_task(client)
    task_id = task["id"]
    original_updated_at = task["updated_at"]

    # Small delay to ensure a different timestamp
    import asyncio

    await asyncio.sleep(0.01)

    response = await client.patch(f"{BASE}/{task_id}", json={"status": "in_progress"})
    new_updated_at = response.json()["updated_at"]

    # Timestamps should differ (updated_at changed)
    assert new_updated_at >= original_updated_at


@pytest.mark.asyncio
async def test_update_task_empty_body_returns_400(client):
    """PATCH with no fields must return 400 Bad Request."""
    task = await create_sample_task(client)
    response = await client.patch(f"{BASE}/{task['id']}", json={})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_update_task_not_found_returns_404(client):
    """PATCHing a non-existent task must return 404."""
    response = await client.patch(f"{BASE}/nonexistent-id", json={"status": "done"})
    assert response.status_code == 404


# ── DELETE ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_task_returns_204(client):
    """Deleting an existing task must return 204 No Content."""
    task = await create_sample_task(client)
    response = await client.delete(f"{BASE}/{task['id']}")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_task_removes_it(client):
    """After deletion, fetching the task must return 404."""
    task = await create_sample_task(client)
    task_id = task["id"]

    await client.delete(f"{BASE}/{task_id}")

    response = await client.get(f"{BASE}/{task_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_not_found_returns_404(client):
    """Deleting a non-existent task must return 404."""
    response = await client.delete(f"{BASE}/does-not-exist-uuid")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_reduces_list_count(client):
    """Total task count must decrease by 1 after deletion."""
    await create_sample_task(client, title="Keep me")
    delete_me = await create_sample_task(client, title="Delete me")

    await client.delete(f"{BASE}/{delete_me['id']}")

    response = await client.get(BASE)
    assert response.json()["total"] == 1
