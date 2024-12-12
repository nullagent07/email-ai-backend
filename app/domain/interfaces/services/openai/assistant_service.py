from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class IOpenAIAssistantService(ABC):
    """Interface for managing OpenAI assistants."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the OpenAI adapter."""
        pass

    @abstractmethod
    async def create_assistant(
        self,
        name: str,
        instructions: str,
        capabilities: List[str],
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new assistant with specified capabilities.
        
        Args:
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
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing assistant.
        
        Args:
            assistant_id: ID of the assistant to update
            name: Optional new name
            instructions: Optional new instructions
            capabilities: Optional new capabilities
            model: Optional new model
            description: Optional new description
            
        Returns:
            Dict containing the updated assistant's information
        """
        pass

    @abstractmethod
    async def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: ID of the assistant to delete
            
        Returns:
            bool: True if deletion was successful
        """
        pass
