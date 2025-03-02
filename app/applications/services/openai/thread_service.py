from typing import Optional, List, Dict, Any
from app.domain.interfaces.integrations.openai.adapter import IOpenAIAdapter
from app.domain.interfaces.services.openai.thread_service import IOpenAIThreadService
import time
import asyncio
from datetime import datetime, timedelta


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
        result = await self._adapter.run_thread(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions,
            model=model,
            tools=tools,
            metadata=metadata
        )
        print("Thread service - result type:", type(result))
        print("Thread service - result:", result)
        return result

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

    async def list_runs(
        self,
        thread_id: str,
        limit: int = 100,
        order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """List runs for a thread."""
        runs = await self._adapter.list_runs(
            thread_id=thread_id,
            limit=limit,
            order=order
        )
        return runs  # runs already converted to list of dicts in the adapter

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
            run_dict = run.model_dump() if hasattr(run, 'model_dump') else run
            
            if run_dict["status"] in ["completed", "failed", "cancelled", "expired"]:
                return run_dict
                
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Run {run_id} did not complete within {timeout} seconds")
                
            await asyncio.sleep(check_interval)

    async def cancel_run(
        self,
        thread_id: str,
        run_id: str
    ) -> None:
        """Cancel a run."""
        await self._adapter.cancel_run(
            thread_id=thread_id,
            run_id=run_id
        )

    async def delete_message(
        self,
        thread_id: str,
        message_id: str
    ) -> None:
        """Delete a message from a thread."""
        await self._adapter.delete_message(
            thread_id=thread_id,
            message_id=message_id
        )

    async def delete_all_messages(
        self,
        thread_id: str,
    ) -> None:
        """Delete all messages from a thread."""
        try:
            # Get all messages first
            messages = await self.get_messages(thread_id)
            
            # Delete each message
            for message in messages:
                message_id = message.get("id")
                if message_id:
                    try:
                        await self.delete_message(thread_id, message_id)
                    except Exception as e:
                        if "No message found" in str(e):
                            # Message was already deleted, skip it
                            continue
                        raise  # Re-raise other exceptions
        except Exception as e:
            print(f"Error deleting messages: {e}")
            raise

    async def get_run_status(self, thread_id: str, run_id: str) -> str:
        """Get the current status of a run."""
        try:
            run = await self._adapter.get_thread_run(thread_id=thread_id, run_id=run_id)
            return run.get("status", "unknown")
        except Exception as e:
            print(f"Error getting run status: {e}")
            return "unknown"

    async def is_run_active(self, thread_id: str, run_id: str) -> bool:
        """Check if a run is still active."""
        active_statuses = ["queued", "in_progress", "requires_action"]
        status = await self.get_run_status(thread_id, run_id)
        return status in active_statuses

    async def wait_for_run_cancellation(
        self, 
        thread_id: str, 
        run_id: str, 
        max_attempts: int = 5,
        timeout: float = 60.0,
        check_interval: float = 5.0
    ) -> bool:
        """
        Wait for a run to be cancelled with retries and timeout.
        Returns True if run was successfully cancelled, False otherwise.
        """
        attempt = 0
        start_time = datetime.now()
        max_wait_time = timedelta(seconds=timeout)

        while attempt < max_attempts and (datetime.now() - start_time) < max_wait_time:
            try:
                status = await self.get_run_status(thread_id, run_id)
                if status in ["cancelled", "completed", "failed", "expired"]:
                    print(f"Run {run_id} is no longer active (status: {status})")
                    return True
                
                print(f"Run {run_id} is still {status} (attempt {attempt + 1}/{max_attempts}, waiting {check_interval} seconds)")
                attempt += 1
                await asyncio.sleep(check_interval)
            except Exception as e:
                print(f"Error checking run status: {e}")
                attempt += 1
                await asyncio.sleep(check_interval)

        print(f"Failed to wait for run {run_id} cancellation after {attempt} attempts and {(datetime.now() - start_time).total_seconds():.1f} seconds")
        return False

    async def ensure_no_active_runs(
        self, 
        thread_id: str,
        max_attempts: int = 3,
        timeout: float = 120.0
    ) -> bool:
        """
        Ensure there are no active runs in the thread.
        Returns True if all runs are inactive, False if there are still active runs.
        """
        try:
            # Get all runs for the thread
            runs = await self.list_runs(thread_id)
            active_runs = [
                run for run in runs 
                if run.get("status") in ["queued", "in_progress", "requires_action", "cancelling"]
            ]

            if not active_runs:
                print("No active runs found")
                return True

            print(f"Found {len(active_runs)} active runs")
            
            # Try to cancel each active run
            for run in active_runs:
                run_id = run.get("id")
                status = run.get("status")
                
                if status != "cancelling":
                    try:
                        print(f"Cancelling run {run_id}...")
                        await self.cancel_run(thread_id=thread_id, run_id=run_id)
                        print(f"Successfully requested cancellation for run {run_id}")
                    except Exception as e:
                        print(f"Error requesting cancellation for run {run_id}: {e}")
                
                # Wait for the run to be cancelled
                cancelled = await self.wait_for_run_cancellation(
                    thread_id=thread_id,
                    run_id=run_id,
                    max_attempts=max_attempts,
                    timeout=timeout
                )
                
                if not cancelled:
                    print(f"Failed to cancel run {run_id}")
                    return False

            # Double check that all runs are now inactive
            runs = await self.list_runs(thread_id)
            active_runs = [
                run for run in runs 
                if run.get("status") in ["queued", "in_progress", "requires_action", "cancelling"]
            ]
            
            if active_runs:
                print(f"Still found {len(active_runs)} active runs after cancellation")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error ensuring no active runs: {e}")
            return False
