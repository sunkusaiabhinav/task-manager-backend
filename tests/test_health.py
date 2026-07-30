"""
Tests for GET /health
"""

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """Health endpoint must return HTTP 200."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_body(client):
    """Health endpoint must return expected JSON shape."""
    response = await client.get("/health")
    data = response.json()

    assert data["status"] == "ok"
    assert "app_name" in data
    assert "environment" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_status_field(client):
    """Status field must always be 'ok' when service is running."""
    response = await client.get("/health")
    assert response.json()["status"] == "ok"
