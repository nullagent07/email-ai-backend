from typing import List, Dict, Any, Optional
from uuid import UUID

from app.domain.interfaces.services.assistant_profile_service import IAssistantProfileService
from app.domain.interfaces.repositories.assistant_profiles_repository import IAssistantProfilesRepository
from app.infrastructure.repositories.oauth_repository import OAuthRepository
from sqlalchemy.ext.asyncio import AsyncSession

class AssistantProfileService(IAssistantProfileService):
    """Service for managing assistant profiles in the database."""

    def __init__(self, db_session: AsyncSession):        
        self._profiles_repository : IAssistantProfilesRepository = OAuthRepository(
            db_session=db_session
            )
    
    async def get_user_assistants(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all assistant profiles for a user."""
        profiles = await self._profiles_repository.get_by_user_id(user_id)
        return [
            {
                "profile_id": profile.id,
                "instruction": profile.instruction,
                "name": profile.name,
                "capabilities": profile.capabilities
            }
            for profile in profiles
        ]
    
    async def create_profile(
        self,
        creator_user_id: UUID,
        assistant_id: str,
        name: str,
        instruction: str,
        capabilities: List[str]
    ) -> Dict[str, Any]:
        """Create a new assistant profile."""
        profile = await self._profiles_repository.create(
            creator_user_id=creator_user_id,
            assistant_id=assistant_id,
            name=name,
            instruction=instruction,
            capabilities=capabilities
        )
        return {
            "profile_id": profile.id,
            "instruction": profile.instruction,
            "name": profile.name,
            "capabilities": profile.capabilities
        }
    
    async def update_profile(
        self,
        assistant_id: str,
        user_id: UUID,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update an existing assistant profile."""
        # Проверяем, что профиль существует и принадлежит пользователю
        profile = await self._profiles_repository.get_by_id(assistant_id)
        if not profile or profile.creator_user_id != user_id:
            return None

        # Обновляем только инструкции, так как это единственное, что можно обновить в репозитории
        if 'instruction' in kwargs:
            updated_profile = await self._profiles_repository.update(
                profile_id=assistant_id,
                instruction=kwargs['instruction']
            )
            if not updated_profile:
                return None
            profile = updated_profile

        return {
            "profile_id": profile.id,
            "instruction": profile.instruction,
            "name": profile.name,
            "capabilities": profile.capabilities
        }
    
    async def delete_profile(self, assistant_id: str, user_id: UUID) -> bool:
        """Delete an assistant profile."""
        return await self._profiles_repository.delete(assistant_id)
