from typing import List, Dict, Any, Optional
from uuid import UUID

from app.domain.interfaces.services.assistant_profile_service import IAssistantProfileService
from app.domain.interfaces.repositories.assistant_profiles_repository import IAssistantProfilesRepository

class AssistantProfileService(IAssistantProfileService):
    """Service for managing assistant profiles in the database."""
    
    def __init__(self, profiles_repository: IAssistantProfilesRepository):
        self._profiles_repository = profiles_repository
    
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
    ) -> Dict[str, Any]:
        """Update an existing assistant profile."""
        profile = await self._profiles_repository.update(
            assistant_id=assistant_id,
            user_id=user_id,
            **kwargs
        )
        return {
            "profile_id": profile.id,
            "instruction": profile.instruction,
            "name": profile.name,
            "capabilities": profile.capabilities
        } if profile else None
    
    async def delete_profile(self, assistant_id: str, user_id: UUID) -> bool:
        """Delete an assistant profile."""
        return await self._profiles_repository.delete(assistant_id)
