"""Nation IntentKit Agent API Router."""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from intentkit.models.agent import Agent, AgentCreate, AgentUpdate, AgentResponse
from intentkit.models.db import get_db

from app.auth import get_user_id  # Use the refactored get_user_id from auth

logger = logging.getLogger(__name__)

router_rw = APIRouter(tags=["Agent"])
router_ro = APIRouter(tags=["Agent"])


class AgentCreateRequest(BaseModel):
    name: Annotated[
        str,
        Field(
            ...,
            description="Name of the agent",
            examples=["My First Agent"],
            min_length=1,
        ),
    ]
    description: Annotated[
        Optional[str],
        Field(
            None,
            description="Description of the agent",
            examples=["An agent for general inquiries"],
        ),
    ]


@router_rw.post(
    "/agents",
    response_model=AgentResponse,
    operation_id="create_agent",
    summary="Create a new agent",
    description="Create a new agent owned by the current user. The agent will be initialized with the provided details.",
)
async def create_agent(
    request: AgentUpdate,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new agent."""
    agent_create = AgentCreate.model_validate(request)
    agent_create.owner = user_id
    latest_agent = await agent_create.create()
    # No AgentData in this project, so skip post-processing
    agent_response = await AgentResponse.from_agent(latest_agent)
    return agent_response


@router_ro.get(
    "/agents/{aid}",
    response_model=AgentResponse,
    operation_id="get_agent_by_id",
    summary="Get agent by ID",
    description="Retrieve a specific agent by its ID, only if it is owned by the current user. Returns 404 if not found or not owned by the user.",
)
async def get_agent(
    aid: str = Path(..., description="Agent ID"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific agent."""
    agent = await Agent.get(aid)
    if not agent or agent.owner != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        )
    agent_response = await AgentResponse.from_agent(agent)
    return agent_response
