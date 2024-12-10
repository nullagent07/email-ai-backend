from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from uuid import UUID

class IAssistantOrchestrator(ABC):
    """Interface for orchestrating OpenAI assistants operations."""

    @abstractmethod
    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the orchestrator with OpenAI credentials.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
        """
        pass

    @abstractmethod
    async def create_assistant(
        self,
        creator_user_id: UUID,
        name: str,
        instructions: str,
        capabilities: List[str],
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new assistant with specified capabilities.
        
        Args:
            creator_user_id: ID of the user creating the assistant
            name: Name of the assistant
            instructions: Instructions for the assistant
            capabilities: List of capabilities to enable
            model: Optional model to use
            description: Optional description
            
        Returns:
            Dict containing the created assistant's information
        """
        pass

    @abstractmethod
    async def update_assistant(
        self,
        assistant_id: str,
        user_id: UUID,
        capabilities: Optional[List[str]] = None,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing assistant.
        
        Args:
            assistant_id: ID of the assistant to update
            user_id: ID of the user making the update
            capabilities: Optional new list of capabilities
            name: Optional new name
            instructions: Optional new instructions
            model: Optional new model
            description: Optional new description
            
        Returns:
            Dict containing the updated assistant's information or None if not found
        """
        pass

    @abstractmethod
    async def delete_assistant(
        self,
        assistant_id: str,
        user_id: UUID
    ) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: ID of the assistant to delete
            user_id: ID of the user making the deletion
            
        Returns:
            bool: True if deletion was successful
        """
        pass

    @abstractmethod
    async def get_user_assistants(
        self,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all assistants for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of assistant information
        """
        pass
