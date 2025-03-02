from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class IOpenAIThreadService(ABC):
    """Interface for managing OpenAI threads and messages."""

    @abstractmethod
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
    async def add_message(
        self,
        thread_id: str,
        content: str,
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to a thread.
        
        Args:
            thread_id: ID of the thread
            content: Message content
            role: Role of the message sender (default: "user")
            metadata: Optional metadata for the message
            
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
            thread_id: ID of the thread
            assistant_id: ID of the assistant to run
            instructions: Optional additional instructions for this run
            model: Optional model to use for this run
            tools: Optional list of tools to use for this run
            metadata: Optional metadata for this run
            
        Returns:
            Dict containing the run information
        """
        pass

    @abstractmethod
    async def get_messages(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a thread.
        
        Args:
            thread_id: ID of the thread
            limit: Maximum number of messages to return
            order: Sort order ("asc" or "desc")
            
        Returns:
            List of message objects
        """
        pass

    @abstractmethod
    async def list_runs(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """
        List runs for a thread.
        
        Args:
            thread_id: ID of the thread
            limit: Maximum number of runs to return
            order: Sort order for runs ("asc" or "desc")
            
        Returns:
            List of runs for the thread
        """
        pass

    @abstractmethod
    async def wait_for_run_completion(
        self,
        thread_id: str,
        run_id: str,
        check_interval: float = 1.0,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Wait for a thread run to complete.
        
        Args:
            thread_id: ID of the thread
            run_id: ID of the run to wait for
            check_interval: How often to check run status in seconds
            timeout: Maximum time to wait in seconds
            
        Returns:
            Dict containing the completed run information
            
        Raises:
            TimeoutError: If the run does not complete within the timeout period
        """
        pass

    @abstractmethod
    async def delete_message(
        self,
        thread_id: str,
        message_id: str
    ) -> None:
        """
        Delete a message from a thread.
        
        Args:
            thread_id: ID of the thread
            message_id: ID of the message to delete
        """
        pass

    @abstractmethod
    async def delete_all_messages(
        self,
        thread_id: str,
    ) -> None:
        """
        Delete all messages from a thread.
        
        Args:
            thread_id: ID of the thread
        """
        pass
