from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from app.presentation.schemas.assistant import (
    AssistantCreate,
    AssistantUpdate,
    AssistantResponse,
    AssistantProfileResponse
)
from core.dependency_injection import AssistantOrchestratorDependency, CurrentUserDependency


router = APIRouter(prefix="/assistants", tags=["assistants"])


@router.post(
    "",
    response_model=AssistantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assistant"
)
async def create_assistant(
    data: AssistantCreate,
    orchestrator: AssistantOrchestratorDependency,
    user_id: CurrentUserDependency
):
    """
    Create a new OpenAI assistant with specified capabilities.
    
    Args:
        data: Assistant creation data
        orchestrator: Assistant orchestrator dependency
        user_id: ID of the authenticated user
        
    Returns:
        Created assistant information
        
    Raises:
        HTTPException: If assistant creation fails
    """
    try:
        assistant = await orchestrator.create_assistant(
            creator_user_id=user_id,
            name=data.name,
            instructions=data.instructions,
            capabilities=data.capabilities,
            model=data.model,
            description=data.description
        )
        return AssistantResponse(**assistant)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assistant: {str(e)}"
        )


@router.patch(
    "/{assistant_id}",
    response_model=AssistantResponse,
    summary="Update an existing assistant"
)
async def update_assistant(
    assistant_id: str,
    data: AssistantUpdate,
    orchestrator: AssistantOrchestratorDependency,
    user_id: CurrentUserDependency
):
    """
    Update an existing OpenAI assistant.
    
    Args:
        assistant_id: ID of the assistant to update
        data: Assistant update data
        orchestrator: Assistant orchestrator dependency
        user_id: ID of the authenticated user
        
    Returns:
        Updated assistant information
        
    Raises:
        HTTPException: If assistant update fails or user is not authorized
    """
    try:
        assistant = await orchestrator.update_assistant(
            assistant_id=assistant_id,
            user_id=user_id,
            capabilities=data.capabilities,
            name=data.name,
            instructions=data.instructions,
            model=data.model,
            description=data.description
        )
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant not found or you don't have permission to update it"
            )
        return AssistantResponse(**assistant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update assistant: {str(e)}"
        )


@router.delete(
    "/{assistant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assistant"
)
async def delete_assistant(
    assistant_id: str,
    orchestrator: AssistantOrchestratorDependency,
    user_id: CurrentUserDependency
):
    """
    Delete an OpenAI assistant.
    
    Args:
        assistant_id: ID of the assistant to delete
        orchestrator: Assistant orchestrator dependency
        user_id: ID of the authenticated user
        
    Raises:
        HTTPException: If assistant deletion fails or user is not authorized
    """
    try:
        success = await orchestrator.delete_assistant(assistant_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant not found or you don't have permission to delete it"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete assistant: {str(e)}"
        )


@router.get(
    "",
    response_model=List[AssistantProfileResponse],
    summary="Get all assistants for current user"
)
async def get_user_assistants(
    orchestrator: AssistantOrchestratorDependency,
    user_id: CurrentUserDependency
):
    """
    Get all assistants for the authenticated user.
    
    Args:
        orchestrator: Assistant orchestrator dependency
        user_id: ID of the authenticated user
        
    Returns:
        List of assistant profiles
        
    Raises:
        HTTPException: If retrieving assistants fails
    """
    try:
        return await orchestrator.get_user_assistants(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assistants: {str(e)}"
        )