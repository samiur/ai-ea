# ABOUTME: Policy model — scheduling rules per priority tier (PRD R2)
# ABOUTME: Canonical tier enum shared across PRD/TRD; validation via model_validate

import re
from enum import StrEnum

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field

from src.models.base import TimestampedModel

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class PolicyTier(StrEnum):
    """Canonical priority tiers (PRD R2): VIP > Customer > Hiring > Internal > 1-1."""

    VIP = "VIP"
    CUSTOMER = "Customer"
    HIRING = "Hiring"
    INTERNAL = "Internal"
    ONE_ON_ONE = "OneOnOne"


class Policy(TimestampedModel, table=True):
    """Scheduling rules applied to meetings of a given tier."""

    __tablename__ = "policies"

    name: str = Field(unique=True, index=True, min_length=1)
    tier: PolicyTier
    reschedule_window_days: int = Field(ge=0, le=30)
    buffer_before_min: int = Field(ge=0, le=60)
    buffer_after_min: int = Field(ge=0, le=60)
    working_hours: dict[str, list[str]] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Mapping of audience/zone key to [start, end] in HH:MM",
    )
    strict_mode: bool = Field(default=False)

    @field_validator("working_hours")
    @classmethod
    def _valid_working_hours(cls, value: dict[str, list[str]]) -> dict[str, list[str]]:
        for key, window in value.items():
            if len(window) != 2:
                raise ValueError(f"working_hours[{key!r}] must be [start, end]")
            for time_str in window:
                if not _TIME_RE.match(time_str):
                    raise ValueError(f"working_hours[{key!r}] has invalid time {time_str!r}")
            if window[0] >= window[1]:
                raise ValueError(f"working_hours[{key!r}] start must be before end")
        return value
