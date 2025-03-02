from typing import Optional, Tuple

from app.domain.interfaces.integrations.openai.adapter import IOpenAIAdapter
from app.domain.interfaces.services.openai.assistant_service import IOpenAIAssistantService
from app.domain.interfaces.services.openai.thread_service import IOpenAIThreadService

from app.infrastructure.integrations.openai.adapter import OpenAIAdapter
from app.applications.services.openai.assistant_service import OpenAIAssistantService
from app.applications.services.openai.thread_service import OpenAIThreadService


class OpenAIFactory:
    """Factory for creating OpenAI-related services and adapters."""
    
    @staticmethod
    async def create_adapter(
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> IOpenAIAdapter:
        """
        Create and initialize an OpenAI adapter.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
            
        Returns:
            Initialized OpenAI adapter
        """
        adapter = OpenAIAdapter()
        await adapter.initialize_client(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )
        return adapter
    
    @staticmethod
    async def create_assistant_service(
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> IOpenAIAssistantService:
        """
        Create AssistantService with its own adapter.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
            
        Returns:
            Initialized AssistantService
        """
        adapter = await OpenAIFactory.create_adapter(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )
        return OpenAIAssistantService(adapter)
    
    @staticmethod
    async def create_thread_service(
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> IOpenAIThreadService:
        """
        Create ThreadService with its own adapter.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
            
        Returns:
            Initialized ThreadService
        """
        adapter = await OpenAIFactory.create_adapter(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )
        return OpenAIThreadService(adapter)
    
    @staticmethod
    async def create_services(
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> Tuple[IOpenAIAssistantService, IOpenAIThreadService]:
        """
        Create all OpenAI services with a shared adapter.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
            
        Returns:
            Tuple of (AssistantService, ThreadService)
        """
        adapter = await OpenAIFactory.create_adapter(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )
        
        return (
            OpenAIAssistantService(adapter),
            OpenAIThreadService(adapter)
        )
