from typing import Optional, List, Dict, Any
from app.domain.interfaces.integrations.openai.adapter import IOpenAIAdapter
from app.domain.interfaces.services.openai.thread_service import IOpenAIThreadService
import time
import asyncio


class OpenAIThreadService(IOpenAIThreadService):
    """Service for managing OpenAI threads."""

    def __init__(self, adapter: IOpenAIAdapter) -> None:
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
    
    async def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new thread."""
        return await self._adapter.create_thread(
            messages=messages,
            metadata=metadata
        )

    async def add_message(
        self,
        thread_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to a thread."""
        return await self._adapter.add_message_to_thread(
            thread_id=thread_id,
            role=role,
            content=content,
            metadata=metadata
        )

    async def run_thread(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run an assistant on a thread."""
        return await self._adapter.run_thread(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            model=model,
            tools=tools,
            metadata=metadata
        )

    async def get_messages(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get messages from a thread."""
        messages = await self._adapter.get_thread_messages(
            thread_id=thread_id,
            limit=limit,
            order=order
        )
        return messages

    async def wait_for_run_completion(
        self,
        thread_id: str,
        run_id: str,
        check_interval: float = 1.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """Wait for a thread run to complete."""
        start_time = time.time()
        while True:
            run = await self._adapter.get_thread_run(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run["status"] in ["completed", "failed", "cancelled", "expired"]:
                return run
                
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")
                
            await asyncio.sleep(check_interval)
