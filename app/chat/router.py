"""Nation IntentKit Chat API Router."""

import logging
from typing import Annotated, List, Optional, Dict

from epyxid import XID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Response,
    status,
    Query,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from intentkit.core.engine import execute_agent, stream_agent
from intentkit.models.agent import Agent
from intentkit.models.chat import (
    ChatMessageAttachment,
    Chat,
    ChatCreate,
    ChatMessage,
    ChatMessageCreate,
    AuthorType,
)
from intentkit.models.db import get_db

from app.auth import get_user_id

logger = logging.getLogger(__name__)

router_rw = APIRouter(tags=["Chat"])
router_ro = APIRouter(tags=["Chat"])


class ChatMessageRequest(BaseModel):
    """Request model for chat messages.

    This model represents the request body for creating a new chat message.
    It contains the necessary fields to identify the chat context, user,
    and message content, along with optional attachments.
    """

    app_id: Annotated[
        Optional[str],
        Field(
            None,
            description="Optional application identifier",
            examples=["app-789"],
        ),
    ]
    user_id: Annotated[
        str,
        Field(
            ...,
            description="Unique identifier of the user sending the message",
            examples=["user-456"],
            min_length=1,
        ),
    ]
    message: Annotated[
        str,
        Field(
            ...,
            description="Content of the message",
            examples=["Hello, how can you help me today?"],
            min_length=1,
            max_length=65535,
        ),
    ]
    stream: Annotated[
        Optional[bool],
        Field(
            None,
            description="Whether to stream the response",
        ),
    ]
    search_mode: Annotated[
        Optional[bool],
        Field(
            None,
            description="Optional flag to enable search mode",
        ),
    ]
    super_mode: Annotated[
        Optional[bool],
        Field(
            None,
            description="Optional flag to enable super mode",
        ),
    ]
    attachments: Annotated[
        Optional[List[ChatMessageAttachment]],
        Field(
            None,
            description="Optional list of attachments (links, images, or files)",
            examples=[[{"type": "link", "url": "https://example.com"}]],
        ),
    ]

    model_config = ConfigDict(
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "chat_id": "chat-123",
                "app_id": "app-789",
                "user_id": "user-456",
                "message": "Hello, how can you help me today?",
                "search_mode": True,
                "super_mode": False,
                "attachments": [
                    {
                        "type": "link",
                        "url": "https://example.com",
                    }
                ],
            }
        },
    )


@router_ro.get(
    "/agents/{aid}/chats",
    response_model=List[Chat],
    operation_id="list_chats_for_agent",
    summary="List chat threads for an agent",
    description="Retrieve all chat threads associated with a specific agent for the current user.",
)
async def get_chats(
    aid: str = Path(..., description="Agent ID"),
    user_id: str = Depends(get_user_id),
):
    """Get a list of chat threads for an agent."""
    return await Chat.get_by_agent_user(aid, user_id)


@router_rw.post(
    "/agents/{aid}/chats",
    response_model=Chat,
    operation_id="create_chat_thread",
    summary="Create a new chat thread",
    description="Create a new chat thread for a specific agent and user.",
)
async def create_chat(
    aid: str = Path(..., description="Agent ID"),
    user_id: str = Depends(get_user_id),
):
    """Create a new chat thread."""
    chat = ChatCreate(
        id=str(XID()),
        agent_id=aid,
        user_id=user_id,
        summary="",
        rounds=0,
    )
    await chat.save()
    # Retrieve the full Chat object with auto-generated fields
    full_chat = await Chat.get(chat.id)
    return full_chat


@router_ro.get(
    "/agents/{aid}/chats/{chat_id}",
    response_model=Chat,
    operation_id="get_chat_thread_by_id",
    summary="Get chat thread by ID",
    description="Retrieve a specific chat thread by its ID for the current user and agent. Returns 404 if not found or not owned by the user.",
)
async def get_chat(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Path(..., description="Chat ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat thread."""
    chat = await Chat.get(chat_id)
    if not chat or chat.agent_id != aid or chat.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    return chat


@router_rw.patch(
    "/agents/{aid}/chats/{chat_id}",
    response_model=Chat,
    operation_id="update_chat_thread",
    summary="Update a chat thread",
    description="Update details of a specific chat thread. Currently only supports updating the summary.",
)
async def update_chat(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Path(..., description="Chat ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a chat thread."""
    # This is a placeholder for now, as the original implementation only updated the summary.
    # We can add more fields to update later.
    chat = await Chat.get(chat_id)
    if not chat or chat.agent_id != aid or chat.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    return chat


@router_rw.delete(
    "/agents/{aid}/chats/{chat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_chat_thread",
    summary="Delete a chat thread",
    description="Delete a specific chat thread for the current user and agent. Returns 404 if not found or not owned by the user.",
)
async def delete_chat(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Path(..., description="Chat ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat thread."""
    chat = await Chat.get(chat_id)
    if not chat or chat.agent_id != aid or chat.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    await chat.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_ro.get(
    "/agents/{aid}/chats/{chat_id}/messages",
    response_model=List[ChatMessage],
    operation_id="list_messages_in_chat",
    summary="List messages in a chat thread",
    description="Retrieve the message history for a specific chat thread with cursor-based pagination.",
)
async def get_messages(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Path(..., description="Chat ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
    cursor: Optional[str] = Query(
        None, description="Cursor for pagination (message id)"
    ),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of messages to return"
    ),
) -> Dict:
    """Get the message history for a chat thread with cursor-based pagination."""
    chat = await Chat.get(chat_id)
    if not chat or chat.agent_id != aid or chat.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
        )
    from sqlalchemy import select, desc
    from intentkit.models.chat import ChatMessageTable

    stmt = (
        select(ChatMessageTable)
        .where(ChatMessageTable.agent_id == aid, ChatMessageTable.chat_id == chat_id)
        .order_by(desc(ChatMessageTable.id))
        .limit(limit + 1)
    )
    if cursor:
        stmt = stmt.where(ChatMessageTable.id < cursor)
    result = await db.scalars(stmt)
    messages = result.all()
    has_more = len(messages) > limit
    messages_to_return = messages[:limit]
    next_cursor = messages_to_return[-1].id if has_more and messages_to_return else None
    # Return as dict for extensibility
    return {
        "data": [ChatMessage.model_validate(m) for m in messages_to_return],
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


@router_rw.post(
    "/agents/{aid}/chats/{chat_id}/messages",
    operation_id="send_message_to_chat",
    summary="Send a message to a chat thread",
    description="Send a new message to a specific chat thread. Supports streaming responses if requested.",
)
async def send_message(
    request: ChatMessageRequest,
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Path(..., description="Chat ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a new message."""
    agent = await Agent.get(aid)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {aid} not found")

    user_message = ChatMessageCreate(
        id=str(XID()),
        agent_id=aid,
        chat_id=chat_id,
        user_id=user_id,
        author_id=user_id,
        author_type=AuthorType.API,
        thread_type=AuthorType.API,
        message=request.message,
        attachments=request.attachments,
        model=None,
        reply_to=None,
        skill_calls=None,
        input_tokens=0,
        output_tokens=0,
        time_cost=0.0,
        credit_event_id=None,
        credit_cost=None,
        cold_start_cost=0.0,
        app_id=request.app_id,
        search_mode=request.search_mode,
        super_mode=request.super_mode,
    )
    await user_message.save_in_session(db)

    if request.stream:

        async def stream_gen():
            async for chunk in stream_agent(user_message):
                yield chunk.model_dump_json() + "\n"

        return StreamingResponse(stream_gen(), media_type="application/json")
    else:
        response_messages = await execute_agent(user_message)
        return response_messages


@router_rw.post(
    "/agents/{aid}/chats/{chat_id}/messages/retry",
    operation_id="retry_message_in_chat",
    summary="Retry a message in a chat thread",
    description="Retry sending the last message in a specific chat thread.",
)
async def retry_message(
    aid: str = Path(..., description="Agent ID"),
    chat_id: str = Path(..., description="Chat ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retry the last message."""
    # This is a placeholder for now. The logic for retrying a message can be complex
    # and depends on the specific requirements of the application.
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router_ro.get(
    "/messages/{message_id}",
    response_model=ChatMessage,
    operation_id="get_message_by_id",
    summary="Get message by ID",
    description="Retrieve a specific chat message by its ID for the current user. Returns 404 if not found or not owned by the user.",
)
async def get_message(
    message_id: str = Path(..., description="Message ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific message."""
    message = await ChatMessage.get(message_id)
    if not message or message.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Message not found"
        )
    return message
