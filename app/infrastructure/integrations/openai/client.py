from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI
from app.domain.interfaces.integrations.openai.client import IOpenAIClient

class OpenAIClient(IOpenAIClient):
    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        self._client = AsyncOpenAI(
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
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("Client not initialized. Call initialize() first")
            
        response = await self._client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools or [],
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
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("Client not initialized. Call initialize() first")
            
        update_params = {}
        if name is not None:
            update_params["name"] = name
        if instructions is not None:
            update_params["instructions"] = instructions
        if model is not None:
            update_params["model"] = model
        if tools is not None:
            update_params["tools"] = tools
        if description is not None:
            update_params["description"] = description

        response = await self._client.beta.assistants.update(
            assistant_id=assistant_id,
            **update_params
        )
        return response.model_dump()

    async def delete_assistant(self, assistant_id: str) -> bool:
        if not self._client:
            raise RuntimeError("Client not initialized. Call initialize() first")
            
        try:
            await self._client.beta.assistants.delete(assistant_id=assistant_id)
            return True
        except Exception:
            return False
