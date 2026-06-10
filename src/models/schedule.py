# ABOUTME: ScheduleIntent — a declared need to create, move, cancel, or hold a meeting
# ABOUTME: The single intake shape promoted by parsers and the conflict detector (TRD §9)

import uuid
from datetime import date
from enum import StrEnum

from sqlmodel import Field

from src.models.base import TimestampedModel


class IntentKind(StrEnum):
    """What the intent wants to do."""

    NEW = "new"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    HOLD = "hold"


class IntentStatus(StrEnum):
    """Lifecycle state of an intent."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class IntentSource(StrEnum):
    """Where the intent came from."""

    SLACK = "slack"
    EMAIL = "email"
    CONFLICT_DETECTOR = "conflict_detector"
    MANUAL = "manual"


class ScheduleIntent(TimestampedModel, table=True):
    """A scheduling need awaiting decision and execution."""

    __tablename__ = "schedule_intents"

    kind: IntentKind
    series_id: uuid.UUID | None = Field(default=None, foreign_key="meeting_series.id")
    requested_by: uuid.UUID = Field(foreign_key="persons.id", index=True)
    target_date: date
    duration_min: int = Field(ge=15, le=480)
    status: IntentStatus = Field(default=IntentStatus.PENDING, index=True)
    source: IntentSource
