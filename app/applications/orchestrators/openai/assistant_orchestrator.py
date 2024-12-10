from typing import Optional, Dict, Any, List
from uuid import UUID

from app.domain.interfaces.orchestrators.assistant_orchestrator import IAssistantOrchestrator
from app.domain.interfaces.repositories.assistant_profiles_repository import IAssistantProfilesRepository
from app.applications.factories.openai_factory import OpenAIFactory
from app.applications.services.openai.assistant_service import AssistantService
from app.applications.services.openai.thread_service import ThreadService


class AssistantOrchestrator(IAssistantOrchestrator):
    """Orchestrator for managing OpenAI assistants and threads."""

    def __init__(self, profiles_repository: IAssistantProfilesRepository):
        self._assistant_service: Optional[AssistantService] = None
        self._thread_service: Optional[ThreadService] = None
        self._profiles_repository = profiles_repository
    
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
        creator_user_id: UUID,
        name: str,
        instructions: str,
        capabilities: List[str],
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new assistant with specified capabilities.
        
        Args:
            creator_user_id: ID of the user creating the assistant
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
            
        # Create assistant in OpenAI
        openai_assistant = await self._assistant_service.create_assistant(
            name=name,
            instructions=instructions,
            capabilities=capabilities,
            model=model,
            description=description
        )
        
        # Create profile in our database
        profile = await self._profiles_repository.create(
            creator_user_id=creator_user_id,
            instruction=instructions,
            assistant_id=openai_assistant["id"]
        )
        
        # Return combined information
        return {
            **openai_assistant,
            "profile_id": profile.id,
            "creator_user_id": str(profile.creator_user_id)
        }
    
    async def update_assistant(
        self,
        assistant_id: str,
        user_id: UUID,
        capabilities: Optional[List[str]] = None,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing assistant.
        
        Args:
            assistant_id: ID of the assistant to update
            user_id: ID of the user making the update
            capabilities: Optional new list of capabilities
            name: Optional new name
            instructions: Optional new instructions
            model: Optional new model
            description: Optional new description
            
        Returns:
            Dict containing the updated assistant's information or None if not found
        """
        if not self._assistant_service:
            raise RuntimeError("AssistantOrchestrator not initialized")
            
        # Check if profile exists and belongs to user
        profile = await self._profiles_repository.get_by_id(assistant_id)
        if not profile or profile.creator_user_id != user_id:
            return None
            
        # Update in OpenAI
        openai_assistant = await self._assistant_service.update_assistant(
            assistant_id=assistant_id,
            capabilities=capabilities,
            name=name,
            instructions=instructions,
            model=model,
            description=description
        )
        
        # Update profile if instructions changed
        if instructions:
            profile = await self._profiles_repository.update(
                profile_id=assistant_id,
                instruction=instructions
            )
        
        # Return combined information
        return {
            **openai_assistant,
            "profile_id": profile.id,
            "creator_user_id": str(profile.creator_user_id)
        }
    
    async def delete_assistant(self, assistant_id: str, user_id: UUID) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: ID of the assistant to delete
            user_id: ID of the user making the deletion
            
        Returns:
            bool: True if deletion was successful
        """
        if not self._assistant_service:
            raise RuntimeError("AssistantOrchestrator not initialized")
            
        # Check if profile exists and belongs to user
        profile = await self._profiles_repository.get_by_id(assistant_id)
        if not profile or profile.creator_user_id != user_id:
            return False
            
        # Delete from OpenAI first
        if not await self._assistant_service.delete_assistant(assistant_id):
            return False
            
        # Then delete profile
        return await self._profiles_repository.delete(assistant_id)
    
    async def get_user_assistants(self, user_id: UUID) -> List[Dict[str, Any]]:
        """
        Get all assistants for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of assistant information
        """
        # Get all profiles for user
        profiles = await self._profiles_repository.get_by_user_id(user_id)
        
        # TODO: Get OpenAI information for each assistant
        # This would require adding a method to IAssistantService to get assistant info
        
        return [
            {
                "profile_id": profile.id,
                "creator_user_id": str(profile.creator_user_id),
                "instruction": profile.instruction
            }
            for profile in profiles
        ]
