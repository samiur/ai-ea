# ABOUTME: Person model — anyone the assistant coordinates with
# ABOUTME: Validation runs via model_validate (table models skip init validation)

import zoneinfo

from pydantic import EmailStr, field_validator
from sqlmodel import Field

from src.models.base import TimestampedModel


class Person(TimestampedModel, table=True):
    """A coordination counterpart: Samiur, directs, peers, customers, candidates."""

    __tablename__ = "persons"

    email: EmailStr = Field(unique=True, index=True)
    display_name: str = Field(min_length=1)
    timezone: str = Field(description="IANA timezone name, e.g. America/Los_Angeles")
    is_active: bool = Field(default=True)

    @field_validator("timezone")
    @classmethod
    def _valid_iana_timezone(cls, value: str) -> str:
        try:
            zoneinfo.ZoneInfo(value)
        except (zoneinfo.ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Unknown IANA timezone: {value!r}") from exc
        return value
