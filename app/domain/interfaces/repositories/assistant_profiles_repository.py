from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.domain.models.assistant_profiles import AssistantProfiles


class IAssistantProfilesRepository(ABC):
    """Interface for assistant profiles repository."""
    
    @abstractmethod
    async def create(
        self,
        creator_user_id: UUID,
        instruction: str,
        assistant_id: str
    ) -> AssistantProfiles:
        """
        Create a new assistant profile.
        
        Args:
            creator_user_id: ID of the user creating the assistant
            instruction: Assistant instructions
            assistant_id: OpenAI assistant ID
            
        Returns:
            Created assistant profile
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, profile_id: str) -> Optional[AssistantProfiles]:
        """
        Get assistant profile by ID.
        
        Args:
            profile_id: Profile ID to find
            
        Returns:
            Assistant profile if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> List[AssistantProfiles]:
        """
        Get all assistant profiles for a user.
        
        Args:
            user_id: User ID to find profiles for
            
        Returns:
            List of assistant profiles
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        profile_id: str,
        instruction: Optional[str] = None
    ) -> Optional[AssistantProfiles]:
        """
        Update assistant profile.
        
        Args:
            profile_id: Profile ID to update
            instruction: New instructions
            
        Returns:
            Updated assistant profile if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, profile_id: str) -> bool:
        """
        Delete assistant profile.
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            True if profile was deleted, False if not found
        """
        pass
