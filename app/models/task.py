"""
Task ORM model — defines the 'tasks' database table.

This is what SQLAlchemy uses to:
  - CREATE the table (schema)
  - Map Python objects ↔ database rows
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(UTC)


class Task(Base):
    """
    Represents a single task in the database.

    Table name: tasks
    """

    __tablename__ = "tasks"

    # ── Primary key ───────────────────────────────────────────────────────
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── Core fields ───────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )

    status: Mapped[str] = mapped_column(
        Enum("todo", "in_progress", "done", name="task_status"),
        nullable=False,
        default="todo",
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        Enum("low", "medium", "high", name="task_priority"),
        nullable=False,
        default="medium",
        index=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id!r} title={self.title!r} status={self.status!r}>"
