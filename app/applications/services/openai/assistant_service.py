from typing import Optional, List, Dict, Any
from app.domain.interfaces.integrations.openai.adapter import IOpenAIAdapter
from app.domain.interfaces.services.openai.assistant_service import IAssistantService


class AssistantService(IAssistantService):
    """Service for managing OpenAI assistants."""

    def __init__(self, adapter: IOpenAIAdapter):
        self._adapter = adapter
    
    async def initialize(self) -> None:
        """Initialize the OpenAI adapter."""
        await self._adapter.initialize_client()
    
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
            model: Optional model to use (defaults to adapter's DEFAULT_MODEL)
            description: Optional description
            
        Returns:
            Dict containing the created assistant's information
        """
        return await self._adapter.create_assistant_with_capabilities(
            name=name,
            instructions=instructions,
            capabilities=capabilities,
            model=model,
            description=description
        )
    
    async def update_assistant(
        self,
        assistant_id: str,
        capabilities: Optional[List[str]] = None,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing assistant.
        
        Args:
            assistant_id: ID of the assistant to update
            capabilities: Optional new list of capabilities
            name: Optional new name
            instructions: Optional new instructions
            model: Optional new model
            description: Optional new description
            
        Returns:
            Dict containing the updated assistant's information
        """
        capabilities = capabilities or []
        return await self._adapter.update_assistant_capabilities(
            assistant_id=assistant_id,
            capabilities=capabilities,
            name=name,
            instructions=instructions,
            model=model,
            description=description
        )
    
    async def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: ID of the assistant to delete
            
        Returns:
            bool: True if deletion was successful
        """
        return await self._adapter.remove_assistant(assistant_id)
