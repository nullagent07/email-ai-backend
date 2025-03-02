from typing import Optional, List, Dict, Any, Union, Literal, cast
import openai
from openai.types.beta import Thread as OpenAIThreadType
from openai.types.beta import Assistant as OpenAIAssistantType
from openai.types.beta.threads import Run as OpenAIRunType
from openai.types.beta.threads import Message as OpenAIMessageType
from openai.types.beta.threads import MessageContent
from openai.pagination import SyncCursorPage, AsyncCursorPage

from app.domain.interfaces.integrations.openai.client import IOpenAIClient


class OpenAIClient(IOpenAIClient):
    """Implementation of OpenAI API client."""
    
    def __init__(self) -> None:
        self._client: Optional[openai.AsyncOpenAI] = None

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
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> OpenAIAssistantType:
        """Create a new assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        create_params = {
            "name": name,
            "instructions": instructions,
            "model": model,
            "tools": tools if tools else [],
        }
        
        if file_ids:
            create_params["file_ids"] = file_ids
        if metadata:
            create_params["metadata"] = metadata
        if description:
            create_params["description"] = description
            
        response: OpenAIAssistantType = await self._client.beta.assistants.create(**create_params)
        return response

    async def update_assistant(
        self,
        assistant_id: str,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
    ) -> OpenAIAssistantType:
        """Update an existing assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        update_params = {"assistant_id": assistant_id}
        
        if name is not None:
            update_params["name"] = name
        if instructions is not None:
            update_params["instructions"] = instructions
        if model is not None:
            update_params["model"] = model
        if tools is not None:
            update_params["tools"] = tools
        if file_ids is not None:
            update_params["file_ids"] = file_ids
        if metadata is not None:
            update_params["metadata"] = metadata
        if description is not None:
            update_params["description"] = description
            
        response: OpenAIAssistantType = await self._client.beta.assistants.update(**update_params)
        return response

    async def delete_assistant(self, assistant_id: str) -> None:
        """Delete an assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        await self._client.beta.assistants.delete(assistant_id=assistant_id)

    async def get_assistant(self, assistant_id: str) -> OpenAIAssistantType:
        """Get an assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response: OpenAIAssistantType = await self._client.beta.assistants.retrieve(assistant_id=assistant_id)
        return response

    async def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.beta.threads.create(
            messages=messages,
            metadata=metadata
        )
        return response.model_dump()

    async def create_thread_and_run(
        self,
        assistant_id: str,
        thread: Dict[str, Any],
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a thread and run it with an assistant."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.beta.threads.create_and_run(
            assistant_id=assistant_id,
            thread=thread,
            instructions=instructions,
            tools=tools,
            metadata=metadata
        )
        return {
            "id": response.id,
            "thread_id": response.thread_id,
            "assistant_id": response.assistant_id,
            "status": response.status,
            "created_at": response.created_at,
            "metadata": response.metadata
        }

    async def get_thread_run(
        self,
        thread_id: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """Get a thread run."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        return {
            "id": response.id,
            "thread_id": response.thread_id,
            "assistant_id": response.assistant_id,
            "status": response.status,
            "created_at": response.created_at,
            "metadata": response.metadata
        }

    async def list_runs(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List runs for a thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        response = await self._client.beta.threads.runs.list(
            thread_id=thread_id,
            limit=limit,
            order=order
        )
        return [run.model_dump() for run in response.data]

    async def cancel_run(
        self,
        thread_id: str,
        run_id: str
    ) -> None:
        """Cancel a run."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        await self._client.beta.threads.runs.cancel(
            thread_id=thread_id,
            run_id=run_id
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
        if not self._client:
            raise RuntimeError("Client not initialized")

        # Check for active runs
        runs = await self.list_runs(thread_id, limit=1)
        if runs and runs[0].get("status") in ["queued", "in_progress"]:
            try:
                # Cancel the active run
                await self.cancel_run(thread_id, runs[0]["id"])
            except Exception as e:
                # Log error but continue with creating new run
                print(f"Error cancelling run: {e}")
            
        # Create new run
        response = await self._client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            model=model,
            tools=tools,
            metadata=metadata
        )
        print("Raw response type:", type(response))
        print("Raw response:", response)
        
        try:
            response_dict = response.model_dump()
            print("Response dict:", response_dict)
            return response_dict
        except Exception as e:
            print(f"Error converting response to dict: {e}")
            # Fallback to manual conversion
            return {
                "id": response.id,
                "thread_id": response.thread_id,
                "assistant_id": response.assistant_id,
                "status": response.status,
                "created_at": response.created_at,
                "metadata": getattr(response, "metadata", None)
            }

    async def get_thread_messages(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc",
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get messages from a thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.beta.threads.messages.list(
            thread_id=thread_id,
            limit=limit,
            order=order,
            after=after,
            before=before
        )
        return [message.model_dump() for message in response.data]

    async def add_message_to_thread(
        self,
        thread_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to a thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        response = await self._client.beta.threads.messages.create(
            thread_id=thread_id,
            content=content,
            role=role,
            metadata=metadata
        )
        return response.model_dump()

    async def delete_thread_message(
        self,
        thread_id: str,
        message_id: str
    ) -> None:
        """Delete a message from a thread."""
        if not self._client:
            raise RuntimeError("Client not initialized")
            
        await self._client.beta.threads.messages.delete(
            thread_id=thread_id,
            message_id=message_id
        )
