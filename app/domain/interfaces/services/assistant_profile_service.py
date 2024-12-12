from typing import List, Dict, Any, Optional
from uuid import UUID
from abc import ABC, abstractmethod

class IAssistantProfileService(ABC):
    """Interface for managing assistant profiles in the database."""
    
    @abstractmethod
    async def get_user_assistants(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all assistant profiles for a user."""
        pass
    
    @abstractmethod
    async def create_profile(
        self,
        creator_user_id: UUID,
        assistant_id: str,
        name: str,
        instruction: str,
        capabilities: List[str]
    ) -> Dict[str, Any]:
        """Create a new assistant profile."""
        pass
    
    @abstractmethod
    async def update_profile(
        self,
        assistant_id: str,
        user_id: UUID,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing assistant profile.
        
        Returns:
            Dict with updated profile info if successful, None if profile not found
            or user doesn't have permission to update it.
        """
        pass
    
    @abstractmethod
    async def delete_profile(self, assistant_id: str, user_id: UUID) -> bool:
        """Delete an assistant profile."""
        pass
