from typing import Optional, List, Dict, Any, Union, Literal, cast
import openai
from openai.types.beta import Thread as OpenAIThreadType
from openai.types.beta import Assistant as OpenAIAssistantType
from openai.types.beta.threads import Run as OpenAIRunType
from openai.types.beta.threads import Message as OpenAIMessageType
from openai.types.beta.threads.message_content import MessageContent
from openai.types.beta.assistant_tool import AssistantTool
from openai.types.beta.thread_create_params import Message as ThreadMessage
from openai.types.beta.assistant_tool_param import AssistantToolParam
from openai.pagination import SyncCursorPage, AsyncCursorPage

from app.domain.interfaces.integrations.openai.client import IOpenAIClient


class OpenAIClient(IOpenAIClient):
    """Implementation of OpenAI API client."""
    
    def __init__(self) -> None:
        self._client = None

    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """Initialize the OpenAI client."""
        self._client = openai.AsyncOpenAI(
            api_key=api_key,
            organization=organization,
            base_url=api_base,
            timeout=timeout
        )

    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response: OpenAIAssistantType = await self._client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=cast(List[AssistantToolParam], tools) if tools else [],
            description=description
        )
        return response.model_dump()

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
        """Update an existing assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        update_params = {}
        if name is not None:
            update_params["name"] = name
        if instructions is not None:
            update_params["instructions"] = instructions
        if model is not None:
            update_params["model"] = model
        if tools is not None:
            update_params["tools"] = cast(List[AssistantToolParam], tools)
        if description is not None:
            update_params["description"] = description
            
        response: OpenAIAssistantType = await self._client.beta.assistants.update(
            assistant_id=assistant_id,
            **update_params
        )
        return response.model_dump()

    async def delete_assistant(self, assistant_id: str) -> bool:
        """Delete an assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        try:
            await self._client.beta.assistants.delete(assistant_id=assistant_id)
            return True
        except Exception:
            return False

    async def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response: OpenAIThreadType = await self._client.beta.threads.create(
            messages=cast(List[ThreadMessage], messages) if messages else [],
            metadata=metadata
        )
        return response.model_dump()

    async def add_message_to_thread(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to an existing thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response: OpenAIMessageType = await self._client.beta.threads.messages.create(
            thread_id=thread_id,
            role=cast(Literal["user", "assistant"], role),
            content=content,
            metadata=metadata
        )
        return response.model_dump()

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
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response: OpenAIRunType = await self._client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            metadata=metadata
        )
        return response.model_dump()

    async def get_thread_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        params = {}
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
            
        response: AsyncCursorPage[OpenAIMessageType] = await self._client.beta.threads.messages.list(
            thread_id=thread_id,
            **params
        )
        return [message.model_dump() for message in response.data]
