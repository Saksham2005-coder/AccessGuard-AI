"""API endpoints for Conversational Accessibility Assistant.

Phase 19 Feature 8: Endpoints for asking grounded accessibility questions,
retrieving conversations, and managing dialogue history.
"""

import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantConversationResponse,
    AssistantMessageResponse,
)
from app.services import assistant_service

router = APIRouter(tags=["assistant"])


@router.post(
    "/assistant/chat",
    response_model=AssistantMessageResponse,
    status_code=status.HTTP_200_OK,
)
async def chat_with_assistant(
    data: AssistantChatRequest,
    current_user: CurrentUserDep,
    db: DbDep,
) -> AssistantMessageResponse:
    """Send a query to the accessibility assistant within an authorized project/scan context."""
    return await assistant_service.process_assistant_chat(
        db=db,
        user_id=current_user.id,
        req=data,
    )


@router.get(
    "/projects/{project_id}/assistant/conversations",
    response_model=list[AssistantConversationResponse],
    status_code=status.HTTP_200_OK,
)
async def list_project_conversations(
    project_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> list[AssistantConversationResponse]:
    """List recent assistant conversation sessions for a project."""
    return await assistant_service.list_user_conversations(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
    )


@router.get(
    "/assistant/conversations/{conversation_id}",
    response_model=AssistantConversationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> AssistantConversationResponse:
    """Retrieve full conversation transcript with messages and citations."""
    return await assistant_service.get_conversation_details(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )


@router.delete(
    "/assistant/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_conversation(
    conversation_id: uuid.UUID,
    current_user: CurrentUserDep,
    db: DbDep,
) -> None:
    """Delete an assistant conversation session."""
    await assistant_service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
