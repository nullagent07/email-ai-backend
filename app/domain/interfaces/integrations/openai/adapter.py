from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.domain.interfaces.integrations.openai.client import OpenAIClientInterface


class IOpenAIAdapter(ABC):
    """Interface for OpenAI adapter that provides higher-level operations for working with assistants."""

    @abstractmethod
    def get_client(self) -> OpenAIClientInterface:
        """
        Get the OpenAI client instance.
        
        Returns:
            OpenAIClientInterface: The initialized OpenAI client
        """
        pass

    @abstractmethod
    async def create_assistant_with_capabilities(
        self,
        name: str,
        instructions: str,
        capabilities: List[str],
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an assistant with specified capabilities.
        
        Args:
            name: Name of the assistant
            instructions: Base instructions for the assistant
            capabilities: List of capability names to enable for the assistant
            description: Optional description of the assistant
            
        Returns:
            Dict containing the created assistant's information
        """
        pass

    @abstractmethod
    async def update_assistant_capabilities(
        self,
        assistant_id: str,
        capabilities: List[str],
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an assistant's capabilities.
        
        Args:
            assistant_id: ID of the assistant to update
            capabilities: New list of capability names
            name: Optional new name for the assistant
            instructions: Optional new base instructions
            description: Optional new description
            
        Returns:
            Dict containing the updated assistant's information
        """
        pass

    @abstractmethod
    async def remove_assistant(self, assistant_id: str) -> bool:
        """
        Remove an assistant and clean up any associated resources.
        
        Args:
            assistant_id: ID of the assistant to remove
            
        Returns:
            bool: True if removal was successful, False otherwise
        """
        pass

    @abstractmethod
    async def initialize_client(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the OpenAI client with provided credentials and settings.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional custom API base URL
            timeout: Optional timeout for API requests in seconds
        """
        pass