from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class IThreadService(ABC):
    """Interface for managing OpenAI threads and messages."""

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
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to a thread.
        
        Args:
            thread_id: ID of the thread
            content: Message content
            role: Role of the message sender (default: "user")
            file_ids: Optional list of file IDs to attach
            metadata: Optional metadata for the message
            
        Returns:
            Dict containing the created message's information
        """
        pass

    @abstractmethod
    async def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run an assistant on a thread.
        
        Args:
            thread_id: ID of the thread
            assistant_id: ID of the assistant to run
            instructions: Optional additional instructions for this run
            
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
