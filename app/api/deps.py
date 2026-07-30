"""
Shared FastAPI dependencies — injected into route handlers via Depends().

Centralizing dependencies here means:
  - One place to change how a dependency works
  - Routes stay thin (no boilerplate)
  - Easy to override in tests
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# Type alias — used in route signatures for clean annotations
DbSession = Annotated[AsyncSession, Depends(get_db)]
