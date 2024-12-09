from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class OpenAIClientInterface(ABC):
    """Interface for OpenAI API client operations related to assistants."""
    
    @abstractmethod
    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the OpenAI client with necessary credentials and settings.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional custom API base URL
            timeout: Optional timeout for API requests in seconds
        """
        pass
    
    @abstractmethod
    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new assistant.
        
        Args:
            name: The name of the assistant
            instructions: The instructions that the assistant should follow
            model: The model to use for the assistant
            tools: Optional list of tools the assistant can use
            file_ids: Optional list of file IDs attached to the assistant
            description: Optional description of the assistant
            
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
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing assistant.
        
        Args:
            assistant_id: The ID of the assistant to update
            name: Optional new name for the assistant
            instructions: Optional new instructions
            model: Optional new model
            tools: Optional new list of tools
            file_ids: Optional new list of file IDs
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
            assistant_id: The ID of the assistant to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass