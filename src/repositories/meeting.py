# ABOUTME: Async repository for meeting series and their attendees
# ABOUTME: Series CRUD plus attendee management and owner/attendee queries

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.meeting import MeetingAttendee, MeetingSeries


class MeetingRepository:
    """Data access for MeetingSeries and MeetingAttendee rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, series: MeetingSeries) -> MeetingSeries:
        self._session.add(series)
        await self._session.commit()
        await self._session.refresh(series)
        return series

    async def get(self, series_id: UUID) -> MeetingSeries | None:
        return await self._session.get(MeetingSeries, series_id)

    async def update(self, series_id: UUID, updates: dict[str, object]) -> MeetingSeries | None:
        series = await self._session.get(MeetingSeries, series_id)
        if series is None:
            return None
        merged = series.model_dump() | dict(updates)
        MeetingSeries.model_validate(merged)
        for key, value in updates.items():
            setattr(series, key, value)
        await self._session.commit()
        await self._session.refresh(series)
        return series

    async def delete(self, series_id: UUID) -> bool:
        series = await self._session.get(MeetingSeries, series_id)
        if series is None:
            return False
        await self._session.delete(series)
        await self._session.commit()
        return True

    async def list_by_owner(self, owner_id: UUID) -> list[MeetingSeries]:
        result = await self._session.exec(
            select(MeetingSeries).where(MeetingSeries.owner_id == owner_id)
        )
        return list(result.all())

    async def list_for_attendee(self, person_id: UUID) -> list[MeetingSeries]:
        result = await self._session.exec(
            select(MeetingSeries)
            .join(MeetingAttendee, MeetingAttendee.series_id == MeetingSeries.id)  # type: ignore[arg-type]
            .where(MeetingAttendee.person_id == person_id)
        )
        return list(result.all())

    async def add_attendee(
        self, series_id: UUID, person_id: UUID, *, is_required: bool = True
    ) -> MeetingAttendee:
        attendee = MeetingAttendee(
            series_id=series_id, person_id=person_id, is_required=is_required
        )
        self._session.add(attendee)
        await self._session.commit()
        await self._session.refresh(attendee)
        return attendee

    async def remove_attendee(self, series_id: UUID, person_id: UUID) -> bool:
        attendee = await self._session.get(MeetingAttendee, (series_id, person_id))
        if attendee is None:
            return False
        await self._session.delete(attendee)
        await self._session.commit()
        return True

    async def list_attendees(self, series_id: UUID) -> list[MeetingAttendee]:
        result = await self._session.exec(
            select(MeetingAttendee).where(MeetingAttendee.series_id == series_id)
        )
        return list(result.all())
