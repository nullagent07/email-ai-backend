from typing import Optional, List, Dict, Any
from app.domain.interfaces.integrations.openai.adapter import IOpenAIAdapter
from app.domain.interfaces.services.openai.assistant_service import IOpenAIAssistantService


class OpenAIAssistantService(IOpenAIAssistantService):
    """Service for managing OpenAI assistants."""

    def __init__(self, adapter: IOpenAIAdapter):
        self._adapter = adapter
    
    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the OpenAI adapter.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
        """
        await self._adapter.initialize_client(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )
    
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
            description: Optional assistant description
            
        Returns:
            Created assistant information
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
            Updated assistant information
        """
        capabilities = capabilities or []
        return await self._adapter.update_assistant_capabilities(
            assistant_id=assistant_id,
            name=name,
            instructions=instructions,
            capabilities=capabilities,
            model=model,
            description=description
        )
    
    async def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: ID of the assistant to delete
            
        Returns:
            True if deletion was successful
        """
        return await self._adapter.remove_assistant(assistant_id)
