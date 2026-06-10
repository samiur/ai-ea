# ABOUTME: Shared base class for persisted models
# ABOUTME: Provides UUID primary key and created/updated timestamps

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    """Timezone-aware now; SQLModel default_factory needs a named callable."""
    return datetime.now(UTC)


class TimestampedModel(SQLModel):
    """Base for all persisted tables: UUID primary key + audit timestamps.

    (The plan calls this BaseModel; renamed to avoid shadowing
    pydantic.BaseModel, which every schema module imports.)
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=_utcnow,
        nullable=False,
        sa_column_kwargs={"onupdate": _utcnow},
    )
