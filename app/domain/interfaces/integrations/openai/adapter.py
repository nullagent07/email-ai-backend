from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.infrastructure.integrations.openai.client import OpenAIClient


class IOpenAIAdapter(ABC):
    """Interface for OpenAI adapter."""

    @abstractmethod
    def get_client(self) -> OpenAIClient:
        """Get the OpenAI client instance."""
        pass

    @abstractmethod
    async def initialize_client(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """Initialize the OpenAI client with provided credentials and settings."""
        pass

    @abstractmethod
    async def create_assistant_with_capabilities(
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
    async def update_assistant_capabilities(
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
    async def remove_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: ID of the assistant to delete
            
        Returns:
            bool: True if deletion was successful
        """
        pass