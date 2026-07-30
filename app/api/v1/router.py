"""
V1 API router — aggregates all v1 route modules.

Adding a new feature module: import its router here and include it.
"""

from fastapi import APIRouter

from app.api.v1 import tasks

router = APIRouter()
router.include_router(tasks.router)
