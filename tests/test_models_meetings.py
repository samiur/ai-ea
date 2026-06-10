# ABOUTME: Tests for MeetingSeries, attendees, ScheduleIntent, and RRULE utilities (Step 13)
# ABOUTME: Exercises model validation, FK relationships, and recurrence math on SQLite

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel

from src.database import configure_database, get_engine, get_session
from src.models.meeting import AttendeeResponse, MeetingAttendee, MeetingSeries
from src.models.person import Person
from src.models.policy import Policy, PolicyTier
from src.models.schedule import IntentKind, IntentSource, IntentStatus, ScheduleIntent
from src.repositories.meeting import MeetingRepository
from src.utils.rrule import expand_series, next_occurrence, validate_rrule

SQLITE_URL = "sqlite+aiosqlite:///:memory:"

WEEKLY_TUESDAY = "FREQ=WEEKLY;BYDAY=TU"


@pytest.fixture
async def db() -> AsyncIterator[None]:
    """Fresh in-memory database with all tables created."""
    await configure_database(SQLITE_URL)
    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await configure_database(None)


def _series(owner_id: object, policy_id: object, **overrides: object) -> MeetingSeries:
    data: dict[str, object] = {
        "title": "Weekly 1-1 with Alex",
        "owner_id": owner_id,
        "default_duration_min": 30,
        "cadence_rule": WEEKLY_TUESDAY,
        "policy_id": policy_id,
    }
    data.update(overrides)
    return MeetingSeries.model_validate(data)


# --- Validation ---


def test_series_validates() -> None:
    series = _series(owner_id="0" * 32, policy_id="1" * 32)
    assert series.is_active is True


@pytest.mark.parametrize("duration", [5, 481])
def test_series_rejects_bad_duration(duration: int) -> None:
    with pytest.raises(ValidationError):
        _series(owner_id="0" * 32, policy_id="1" * 32, default_duration_min=duration)


def test_series_rejects_invalid_rrule() -> None:
    with pytest.raises(ValidationError):
        _series(owner_id="0" * 32, policy_id="1" * 32, cadence_rule="FREQ=SOMETIMES")


def test_intent_enums_and_validation() -> None:
    intent = ScheduleIntent.model_validate(
        {
            "kind": IntentKind.RESCHEDULE,
            "requested_by": "0" * 32,
            "target_date": date(2026, 6, 16),
            "duration_min": 30,
            "source": IntentSource.CONFLICT_DETECTOR,
        }
    )
    assert intent.status == IntentStatus.PENDING
    assert intent.series_id is None

    with pytest.raises(ValidationError):
        ScheduleIntent.model_validate(
            {
                "kind": "vaporize",
                "requested_by": "0" * 32,
                "target_date": date(2026, 6, 16),
                "duration_min": 30,
                "source": IntentSource.MANUAL,
            }
        )


# --- Relationships & repository ---


async def test_series_attendees_round_trip(db: None) -> None:
    async for session in get_session():
        owner = Person.model_validate(
            {"email": "sam@example.com", "display_name": "Sam", "timezone": "America/Los_Angeles"}
        )
        direct = Person.model_validate(
            {"email": "alex@example.com", "display_name": "Alex", "timezone": "America/New_York"}
        )
        policy = Policy.model_validate(
            {
                "name": "one-on-one",
                "tier": PolicyTier.ONE_ON_ONE,
                "reschedule_window_days": 14,
                "buffer_before_min": 5,
                "buffer_after_min": 5,
                "working_hours": {"default": ["09:00", "17:00"]},
            }
        )
        session.add(owner)
        session.add(direct)
        session.add(policy)
        await session.commit()

        repo = MeetingRepository(session)
        series = await repo.create(_series(owner_id=owner.id, policy_id=policy.id))

        await repo.add_attendee(series.id, direct.id, is_required=True)
        attendees = await repo.list_attendees(series.id)
        assert len(attendees) == 1
        assert attendees[0].person_id == direct.id
        assert attendees[0].response_status == AttendeeResponse.PENDING

        by_owner = await repo.list_by_owner(owner.id)
        assert [s.id for s in by_owner] == [series.id]

        for_attendee = await repo.list_for_attendee(direct.id)
        assert [s.id for s in for_attendee] == [series.id]

        assert await repo.remove_attendee(series.id, direct.id) is True
        assert await repo.list_attendees(series.id) == []


def test_attendee_join_uses_composite_primary_key() -> None:
    """Composite primary key prevents duplicate (series, person) pairs."""
    assert set(MeetingAttendee.__table__.primary_key.columns.keys()) == {  # type: ignore[attr-defined]
        "series_id",
        "person_id",
    }


# --- RRULE utilities ---


def test_validate_rrule_accepts_and_rejects() -> None:
    assert validate_rrule(WEEKLY_TUESDAY) == WEEKLY_TUESDAY
    with pytest.raises(ValueError, match="RRULE"):
        validate_rrule("FREQ=SOMETIMES")


def test_next_occurrence_lands_on_tuesday() -> None:
    # 2026-06-10 is a Wednesday; next Tuesday is 2026-06-16
    after = datetime(2026, 6, 10, 9, 0, tzinfo=UTC)
    nxt = next_occurrence(WEEKLY_TUESDAY, after=after)
    assert nxt is not None
    assert nxt.date() == date(2026, 6, 16)


def test_expand_series_returns_all_occurrences_in_window() -> None:
    start = datetime(2026, 6, 1, 0, 0, tzinfo=UTC)
    end = datetime(2026, 6, 30, 23, 59, tzinfo=UTC)
    occurrences = expand_series(WEEKLY_TUESDAY, start=start, end=end)
    assert [d.date() for d in occurrences] == [
        date(2026, 6, 2),
        date(2026, 6, 9),
        date(2026, 6, 16),
        date(2026, 6, 23),
        date(2026, 6, 30),
    ]
