from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.assistant_profiles import AssistantProfiles
from app.domain.interfaces.repositories.assistant_profiles_repository import IAssistantProfilesRepository


class AssistantProfilesRepository(IAssistantProfilesRepository):
    """Implementation of assistant profiles repository."""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def create(
        self,
        creator_user_id: UUID,
        instruction: str,
        assistant_id: str,
        name: str,
        capabilities: List[str]
    ) -> AssistantProfiles:
        """Create a new assistant profile."""
        profile = AssistantProfiles(
            id=assistant_id,
            creator_user_id=creator_user_id,
            name=name,
            instruction=instruction,
            capabilities=capabilities
        )
        self.db_session.add(profile)
        await self.db_session.flush()
        await self.db_session.commit()
        return profile
    
    async def get_by_id(self, profile_id: str) -> Optional[AssistantProfiles]:
        """Get assistant profile by ID."""
        query = select(AssistantProfiles).where(AssistantProfiles.id == profile_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: UUID) -> List[AssistantProfiles]:
        """Get all assistant profiles for a user."""
        query = select(AssistantProfiles).where(
            AssistantProfiles.creator_user_id == user_id
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())
    
    async def update(
        self,
        profile_id: str,
        instruction: Optional[str] = None
    ) -> Optional[AssistantProfiles]:
        """Update assistant profile."""
        profile = await self.get_by_id(profile_id)
        if profile and instruction is not None:
            profile.instruction = instruction
            await self.db_session.flush()
            await self.db_session.commit()
        return profile
    
    async def delete(self, profile_id: str) -> bool:
        """Delete assistant profile."""
        profile = await self.get_by_id(profile_id)
        if profile:
            await self.db_session.delete(profile)
            await self.db_session.flush()
            await self.db_session.commit()
            return True
        return False
