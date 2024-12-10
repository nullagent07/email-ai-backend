from typing import Optional, Dict, Any, List

from app.domain.interfaces.orchestrators.assistant_orchestrator import IAssistantOrchestrator
from app.applications.factories.openai_factory import OpenAIFactory
from app.applications.services.openai.assistant_service import AssistantService
from app.applications.services.openai.thread_service import ThreadService


class AssistantOrchestrator(IAssistantOrchestrator):
    """Orchestrator for managing OpenAI assistants and threads."""

    def __init__(self):
        self._assistant_service: Optional[AssistantService] = None
        self._thread_service: Optional[ThreadService] = None
    
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
        self._assistant_service, self._thread_service = await OpenAIFactory.create_services(
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
            model: Optional model to use
            description: Optional description
            
        Returns:
            Dict containing the created assistant's information
        """
        if not self._assistant_service:
            raise RuntimeError("AssistantOrchestrator not initialized")
            
        return await self._assistant_service.create_assistant(
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
        if not self._assistant_service:
            raise RuntimeError("AssistantOrchestrator not initialized")
            
        return await self._assistant_service.update_assistant(
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
        if not self._assistant_service:
            raise RuntimeError("AssistantOrchestrator not initialized")
            
        return await self._assistant_service.delete_assistant(assistant_id)
