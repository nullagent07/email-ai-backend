from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class IOpenAIClient(ABC):
    """Interface for OpenAI API client operations related to assistants."""
    
    @abstractmethod
    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the OpenAI client with necessary credentials and settings.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional custom API base URL
            timeout: Optional timeout for API requests in seconds
        """
        pass
    
    @abstractmethod
    async def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new assistant.
        
        Args:
            name: The name of the assistant
            instructions: The instructions that the assistant should follow
            model: The model to use for the assistant
            tools: Optional list of tools the assistant can use
            file_ids: Optional list of file IDs attached to the assistant
            description: Optional description of the assistant
            
        Returns:
            Dict containing the created assistant's information
        """
        pass
    
    @abstractmethod
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
        """
        Update an existing assistant.
        
        Args:
            assistant_id: The ID of the assistant to update
            name: Optional new name for the assistant
            instructions: Optional new instructions
            model: Optional new model
            tools: Optional new list of tools
            file_ids: Optional new list of file IDs
            description: Optional new description
            
        Returns:
            Dict containing the updated assistant's information
        """
        pass
    
    @abstractmethod
    async def delete_assistant(self, assistant_id: str) -> bool:
        """
        Delete an assistant.
        
        Args:
            assistant_id: The ID of the assistant to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    async def create_thread(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new thread.
        
        Args:
            messages: Optional list of messages to start the thread with
            metadata: Optional metadata to attach to the thread
            
        Returns:
            Dict containing the created thread's information
        """
        pass

    @abstractmethod
    async def add_message_to_thread(
        self,
        thread_id: str,
        role: str,
        content: str,
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to an existing thread.
        
        Args:
            thread_id: The ID of the thread to add the message to
            role: The role of the message sender (e.g., 'user', 'assistant')
            content: The content of the message
            file_ids: Optional list of file IDs to attach to the message
            metadata: Optional metadata to attach to the message
            
        Returns:
            Dict containing the created message's information
        """
        pass

    @abstractmethod
    async def run_thread(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run an assistant on a thread.
        
        Args:
            thread_id: The ID of the thread to run
            assistant_id: The ID of the assistant to use
            instructions: Optional additional instructions for this run
            model: Optional model override for this run
            tools: Optional tools override for this run
            metadata: Optional metadata for this run
            
        Returns:
            Dict containing the run information
        """
        pass

    @abstractmethod
    async def get_thread_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None,
        order: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: The ID of the thread to get messages from
            limit: Optional maximum number of messages to return
            order: Optional sort order ('asc' or 'desc')
            after: Optional cursor for pagination (get messages after this ID)
            before: Optional cursor for pagination (get messages before this ID)
            
        Returns:
            List of message objects
        """
        pass