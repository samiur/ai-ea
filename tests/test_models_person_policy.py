# ABOUTME: Tests for Person and Policy models with CRUD operations (Step 12)
# ABOUTME: Validation runs via model_validate (SQLModel table models skip init validation)

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel

from src.database import configure_database, get_engine, get_session
from src.models.person import Person
from src.models.policy import Policy, PolicyTier
from src.repositories.person import PersonRepository
from src.repositories.policy import PolicyRepository

SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db() -> AsyncIterator[None]:
    """Fresh in-memory database with all tables created."""
    await configure_database(SQLITE_URL)
    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await configure_database(None)


def _valid_person(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "email": "alex@example.com",
        "display_name": "Alex Example",
        "timezone": "America/Los_Angeles",
    }
    data.update(overrides)
    return data


def _valid_policy(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "name": "one-on-one-default",
        "tier": PolicyTier.ONE_ON_ONE,
        "reschedule_window_days": 14,
        "buffer_before_min": 5,
        "buffer_after_min": 5,
        "working_hours": {"default": ["09:00", "17:00"]},
    }
    data.update(overrides)
    return data


# --- Validation ---


def test_person_validates() -> None:
    person = Person.model_validate(_valid_person())
    assert person.email == "alex@example.com"
    assert person.is_active is True


def test_person_rejects_bad_email() -> None:
    with pytest.raises(ValidationError):
        Person.model_validate(_valid_person(email="not-an-email"))


def test_person_rejects_unknown_timezone() -> None:
    with pytest.raises(ValidationError):
        Person.model_validate(_valid_person(timezone="Mars/Olympus_Mons"))


def test_policy_validates() -> None:
    policy = Policy.model_validate(_valid_policy())
    assert policy.tier == PolicyTier.ONE_ON_ONE
    assert policy.strict_mode is False


def test_policy_tier_is_enum() -> None:
    assert {t.value for t in PolicyTier} == {"VIP", "Customer", "Hiring", "Internal", "OneOnOne"}
    with pytest.raises(ValidationError):
        Policy.model_validate(_valid_policy(tier="Imaginary"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("reschedule_window_days", -1),
        ("reschedule_window_days", 31),
        ("buffer_before_min", 61),
        ("buffer_after_min", -5),
    ],
)
def test_policy_rejects_out_of_range(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        Policy.model_validate(_valid_policy(**{field: value}))


def test_policy_rejects_malformed_working_hours() -> None:
    with pytest.raises(ValidationError):
        Policy.model_validate(_valid_policy(working_hours={"default": ["9am"]}))
    with pytest.raises(ValidationError):
        Policy.model_validate(_valid_policy(working_hours={"default": ["25:00", "17:00"]}))


# --- CRUD ---


async def test_person_crud_round_trip(db: None) -> None:
    async for session in get_session():
        repo = PersonRepository(session)

        created = await repo.create(Person.model_validate(_valid_person()))
        assert created.id is not None

        fetched = await repo.get(created.id)
        assert fetched is not None and fetched.email == "alex@example.com"

        by_email = await repo.get_by_email("alex@example.com")
        assert by_email is not None and by_email.id == created.id

        updated = await repo.update(created.id, {"display_name": "Alexandra Example"})
        assert updated is not None and updated.display_name == "Alexandra Example"

        people = await repo.list(limit=10, offset=0)
        assert len(people) == 1

        assert await repo.delete(created.id) is True
        assert await repo.get(created.id) is None


async def test_person_email_unique(db: None) -> None:
    async for session in get_session():
        repo = PersonRepository(session)
        await repo.create(Person.model_validate(_valid_person()))
        with pytest.raises(IntegrityError):
            await repo.create(Person.model_validate(_valid_person(display_name="Dup")))
        await session.rollback()


async def test_policy_crud_round_trip(db: None) -> None:
    async for session in get_session():
        repo = PolicyRepository(session)

        created = await repo.create(Policy.model_validate(_valid_policy()))
        fetched = await repo.get(created.id)
        assert fetched is not None and fetched.name == "one-on-one-default"

        by_name = await repo.get_by_name("one-on-one-default")
        assert by_name is not None

        updated = await repo.update(created.id, {"reschedule_window_days": 7})
        assert updated is not None and updated.reschedule_window_days == 7

        assert await repo.delete(created.id) is True


async def test_repo_get_missing_returns_none(db: None) -> None:
    async for session in get_session():
        assert await PersonRepository(session).get(uuid4()) is None
        assert await PolicyRepository(session).delete(uuid4()) is False
