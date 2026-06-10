# ABOUTME: Async CRUD repository for Person
# ABOUTME: Callers pass validated models; updates re-validate changed fields

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.person import Person


class PersonRepository:
    """Data access for Person rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, person: Person) -> Person:
        self._session.add(person)
        await self._session.commit()
        await self._session.refresh(person)
        return person

    async def get(self, person_id: UUID) -> Person | None:
        return await self._session.get(Person, person_id)

    async def get_by_email(self, email: str) -> Person | None:
        result = await self._session.exec(select(Person).where(Person.email == email))
        return result.first()

    async def update(self, person_id: UUID, updates: dict[str, object]) -> Person | None:
        person = await self._session.get(Person, person_id)
        if person is None:
            return None
        merged = person.model_dump() | dict(updates)
        Person.model_validate(merged)
        for key, value in updates.items():
            setattr(person, key, value)
        await self._session.commit()
        await self._session.refresh(person)
        return person

    async def delete(self, person_id: UUID) -> bool:
        person = await self._session.get(Person, person_id)
        if person is None:
            return False
        await self._session.delete(person)
        await self._session.commit()
        return True

    async def list(self, limit: int = 50, offset: int = 0) -> list[Person]:
        result = await self._session.exec(select(Person).offset(offset).limit(limit))
        return list(result.all())
