# ABOUTME: MeetingSeries and attendee join models
# ABOUTME: A series is a recurring meeting (e.g. a 1-1) governed by a Policy

import uuid
from enum import StrEnum

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from src.models.base import TimestampedModel
from src.utils.rrule import validate_rrule


class AttendeeResponse(StrEnum):
    """Invitation response state for a series attendee."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class MeetingSeries(TimestampedModel, table=True):
    """A recurring meeting series owned by a person and governed by a policy."""

    __tablename__ = "meeting_series"

    title: str = Field(min_length=1)
    owner_id: uuid.UUID = Field(foreign_key="persons.id", index=True)
    default_duration_min: int = Field(ge=15, le=480)
    cadence_rule: str = Field(description="iCal RRULE, e.g. FREQ=WEEKLY;BYDAY=TU")
    policy_id: uuid.UUID = Field(foreign_key="policies.id", index=True)
    is_active: bool = Field(default=True)

    @field_validator("cadence_rule")
    @classmethod
    def _valid_rrule(cls, value: str) -> str:
        return validate_rrule(value)


class MeetingAttendee(SQLModel, table=True):
    """Join table linking people to a meeting series (composite primary key)."""

    __tablename__ = "meeting_attendees"

    series_id: uuid.UUID = Field(foreign_key="meeting_series.id", primary_key=True)
    person_id: uuid.UUID = Field(foreign_key="persons.id", primary_key=True)
    is_required: bool = Field(default=True)
    response_status: AttendeeResponse = Field(default=AttendeeResponse.PENDING)
