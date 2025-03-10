from typing import Dict, Any, List, Optional

from app.domain.interfaces.integrations.openai.adapter import IOpenAIAdapter
from app.infrastructure.integrations.openai.client import OpenAIClient


class OpenAIAdapter(IOpenAIAdapter):
    """Implementation of OpenAI adapter for working with assistants."""

    DEFAULT_MODEL = "gpt-4"

    def __init__(self):
        self._client: Optional[OpenAIClient] = None
        self._capability_to_tools_map = {
            "code_interpreter": {"type": "code_interpreter"},
            "retrieval": {"type": "retrieval"},
            "function": {"type": "function"},
        }

    def get_client(self) -> OpenAIClient:
        """Get the OpenAI client instance."""
        if not self._client:
            raise RuntimeError("Client not initialized. Call initialize_client() first")
        return self._client

    async def initialize_client(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """Initialize the OpenAI client with provided credentials and settings."""
        self._client = OpenAIClient()
        await self._client.initialize(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )

    def _capabilities_to_tools(self, capabilities: List[str]) -> List[Dict[str, Any]]:
        """Convert capability names to OpenAI tools configuration."""
        tools: List[Dict[str, Any]] = []
        for capability in capabilities:
            if capability in self._capability_to_tools_map:
                tools.append(self._capability_to_tools_map[capability])
        return tools

    def _tools_to_capabilities(self, tools: List[Dict[str, Any]]) -> List[str]:
        """Convert OpenAI tools configuration back to capability names."""
        capabilities = []
        tool_to_capability = {v["type"]: k for k, v in self._capability_to_tools_map.items()}
        for tool in tools:
            if tool["type"] in tool_to_capability:
                capabilities.append(tool_to_capability[tool["type"]])
        return capabilities

    async def create_assistant_with_capabilities(
        self,
        name: str,
        instructions: str,
        capabilities: List[str],
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an assistant with specified capabilities.
        
        Args:
            name: Name of the assistant
            instructions: Base instructions for the assistant
            capabilities: List of capability names to enable for the assistant
            model: Optional model to use (defaults to DEFAULT_MODEL)
            description: Optional description of the assistant
        """
        client = self.get_client()
        tools = self._capabilities_to_tools(capabilities)
        
        response = await client.create_assistant(
            name=name,
            instructions=instructions,
            model=model or self.DEFAULT_MODEL,
            tools=tools,
            description=description
        )
        
        # Convert response to expected format
        return {
            "id": response.id,
            "name": response.name,
            "instructions": response.instructions,
            "capabilities": self._tools_to_capabilities(response.tools),
            "model": response.model,
            "description": getattr(response, "description", None),
            "created_at": response.created_at,
            "modified_at": getattr(response, "modified_at", None)
        }

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
        Update an assistant's capabilities.
        
        Args:
            assistant_id: ID of the assistant to update
            name: Optional new name for the assistant
            instructions: Optional new base instructions
            capabilities: Optional new list of capability names
            model: Optional new model to use
            description: Optional new description
        """
        client = self.get_client()
        tools = self._capabilities_to_tools(capabilities) if capabilities else None
        
        response = await client.update_assistant(
            assistant_id=assistant_id,
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            description=description
        )
        
        # Convert response to expected format
        return {
            "id": response.id,
            "name": response.name,
            "instructions": response.instructions,
            "capabilities": self._tools_to_capabilities(response.tools),
            "model": response.model,
            "description": getattr(response, "description", None),
            "created_at": response.created_at,
            "modified_at": getattr(response, "modified_at", None)
        }

    async def remove_assistant(self, assistant_id: str) -> bool:
        """Remove an assistant and clean up any associated resources."""
        client = self.get_client()
        return await client.delete_assistant(assistant_id)

    async def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new thread."""
        client = self.get_client()
        return await client.create_thread(
            messages=messages,
            metadata=metadata
        )

    async def add_message_to_thread(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a message to an existing thread."""
        client = self.get_client()
        return await client.add_message_to_thread(
            thread_id=thread_id,
            role=role,
            content=content,
            metadata=metadata
        )

    async def list_runs(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List runs for a thread."""
        response = await self._client.list_runs(
            thread_id=thread_id,
            limit=limit,
            order=order
        )
        return response

    async def cancel_run(self, thread_id: str, run_id: str) -> None:
        """Cancel a run."""
        client = self.get_client()
        await client.cancel_run(thread_id=thread_id, run_id=run_id)

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
        client = self.get_client()
        response = await client.run_thread(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            model=model,
            tools=tools,
            metadata=metadata
        )
        print("Adapter - response type:", type(response))
        print("Adapter - response:", response)
        return {
            "id": response["id"],
            "thread_id": response["thread_id"],
            "assistant_id": response["assistant_id"],
            "status": response["status"],
            "created_at": response["created_at"],
            "metadata": response.get("metadata")
        }

    async def get_thread_messages(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get messages from a thread."""
        client = self.get_client()
        return await client.get_thread_messages(
            thread_id=thread_id,
            limit=limit,
            order=order
        )

    async def get_thread_run(
        self,
        thread_id: str,
        run_id: str
    ) -> Dict[str, Any]:
        """Get a thread run."""
        if not self._client:
            raise RuntimeError("Client not initialized")

        return await self._client.get_thread_run(
            thread_id=thread_id,
            run_id=run_id
        )

    async def delete_message(
        self,
        thread_id: str,
        message_id: str
    ) -> None:
        """Delete a message from a thread."""
        client = self.get_client()
        await client.delete_thread_message(thread_id=thread_id, message_id=message_id)