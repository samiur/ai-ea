# ABOUTME: Async CRUD repository for Policy
# ABOUTME: Callers pass validated models; updates re-validate changed fields

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.policy import Policy, PolicyTier


class PolicyRepository:
    """Data access for Policy rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, policy: Policy) -> Policy:
        self._session.add(policy)
        await self._session.commit()
        await self._session.refresh(policy)
        return policy

    async def get(self, policy_id: UUID) -> Policy | None:
        return await self._session.get(Policy, policy_id)

    async def get_by_name(self, name: str) -> Policy | None:
        result = await self._session.exec(select(Policy).where(Policy.name == name))
        return result.first()

    async def list_by_tier(self, tier: PolicyTier) -> list[Policy]:
        result = await self._session.exec(select(Policy).where(Policy.tier == tier))
        return list(result.all())

    async def update(self, policy_id: UUID, updates: dict[str, object]) -> Policy | None:
        policy = await self._session.get(Policy, policy_id)
        if policy is None:
            return None
        merged = policy.model_dump() | dict(updates)
        Policy.model_validate(merged)
        for key, value in updates.items():
            setattr(policy, key, value)
        await self._session.commit()
        await self._session.refresh(policy)
        return policy

    async def delete(self, policy_id: UUID) -> bool:
        policy = await self._session.get(Policy, policy_id)
        if policy is None:
            return False
        await self._session.delete(policy)
        await self._session.commit()
        return True

    async def list(self, limit: int = 50, offset: int = 0) -> list[Policy]:
        result = await self._session.exec(select(Policy).offset(offset).limit(limit))
        return list(result.all())
