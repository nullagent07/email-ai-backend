from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class IAssistantOrchestrator(ABC):
    """Interface for orchestrating OpenAI assistants operations."""

    @abstractmethod
    async def create_email_assistant(
        self,
        name: str,
        instructions: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an assistant specifically configured for email processing.
        
        Args:
            name: Name of the assistant
            instructions: Base instructions for the assistant
            description: Optional description
            
        Returns:
            Dict containing the created assistant's information
        """
        pass

    @abstractmethod
    async def get_or_create_assistant(
        self,
        assistant_type: str,
        name: str,
        instructions: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get an existing assistant of the specified type or create a new one.
        
        Args:
            assistant_type: Type of assistant (e.g., 'email', 'code', etc.)
            name: Name for the assistant if creation is needed
            instructions: Instructions if creation is needed
            description: Optional description if creation is needed
            
        Returns:
            Dict containing the assistant's information
        """
        pass

    @abstractmethod
    async def ensure_assistant_capabilities(
        self,
        assistant_id: str,
        required_capabilities: List[str]
    ) -> bool:
        """
        Ensure that an assistant has all the required capabilities.
        
        Args:
            assistant_id: ID of the assistant to check/update
            required_capabilities: List of capabilities that must be present
            
        Returns:
            bool: True if all capabilities are present or were successfully added
        """
        pass

    @abstractmethod
    async def get_assistant_state(
        self,
        assistant_id: str
    ) -> Dict[str, Any]:
        """
        Get the current state and configuration of an assistant.
        
        Args:
            assistant_id: ID of the assistant
            
        Returns:
            Dict containing the assistant's current state and configuration
        """
        pass

    @abstractmethod
    async def cleanup_inactive_assistants(
        self,
        max_inactive_days: int = 30
    ) -> List[str]:
        """
        Clean up assistants that haven't been active for a specified period.
        
        Args:
            max_inactive_days: Maximum number of days of inactivity before cleanup
            
        Returns:
            List of IDs of assistants that were cleaned up
        """
        pass
