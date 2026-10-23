# FILE: backend/app/api/v1/conversations.py
from datetime import datetime, timezone
import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.entities import (
    AgentAction,
    BusinessKnowledge,
    ChannelType,
    Conversation,
    ConversationStatus,
    Customer,
    Message,
    MessageSender,
)
from app.schemas.conversation import ConversationResponse, MessageResponse
from app.services.conversation_service import ConversationService

logger = logging.getLogger("replyflow.conversations")
router = APIRouter(prefix="/conversations", tags=["Conversations & Learning Farm"])


def get_conversation_service(db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(db)


class StaffReplyRequest(BaseModel):
    content: str = Field(..., min_length=1)
    operator_name: str = Field(default="Support Specialist")


class ResolveTicketRequest(BaseModel):
    operator_name: str = Field(default="Support Specialist")
    problem_summary: str = Field(..., min_length=3)
    solution_summary: str = Field(..., min_length=3)
    train_ai_agent: bool = Field(default=False)


class AuditLogItem(BaseModel):
    id: str
    conversation_id: str
    channel: str
    customer_handle: str
    resolved_by: str
    resolution_type: str
    problem_statement: str
    solution_statement: str
    learned_by_ai: bool
    created_at: str


@router.post("/{conversation_id}/staff-reply", response_model=MessageResponse)
async def post_human_staff_reply(
    conversation_id: uuid.UUID,
    payload: StaffReplyRequest,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
    )
    res = await db.execute(query)
    conv = res.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    staff_msg = Message(
        conversation_id=conv.id,
        sender=MessageSender.HUMAN_OPERATOR,
        content=payload.content,
        metadata_info={"operator_name": payload.operator_name, "role": "staff_support"}
    )
    db.add(staff_msg)
    await db.commit()
    await db.refresh(staff_msg)

    # Dispatch outbound to live channel before returning response
    if conv.channel == ChannelType.WHATSAPP:
        try:
            from app.integrations.dispatcher import OutboundSocialDispatcher
            dispatcher = OutboundSocialDispatcher(db)
            await dispatcher.dispatch_reply(conv, payload.content)
        except Exception as e:
            logger.warning(f"[Staff Outbound WhatsApp Notice] {e}")

    return staff_msg


@router.post("/{conversation_id}/resolve", response_model=ConversationResponse)
async def resolve_ticket_and_feed_learning_farm(
    conversation_id: uuid.UUID,
    payload: ResolveTicketRequest,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
    )
    res = await db.execute(query)
    conv = res.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.status = ConversationStatus.OPEN
    conv.handoff_summary = {}

    resolve_msg = Message(
        conversation_id=conv.id,
        sender=MessageSender.HUMAN_OPERATOR,
        content=f"[Ticket Resolved by {payload.operator_name}]: {payload.solution_summary}",
        metadata_info={"problem": payload.problem_summary, "solution": payload.solution_summary}
    )
    db.add(resolve_msg)

    # Only train the brain if it is a genuine staff resolution, not a placeholder
    if payload.train_ai_agent and "handed back to ai" not in payload.solution_summary.lower():
        learning_item = BusinessKnowledge(
            business_id=conv.business_id,
            category="historical_resolution",
            title=f"Learned Solution: {payload.problem_summary[:80]}",
            content=f"When customer experiences: '{payload.problem_summary}', the approved resolution is: '{payload.solution_summary}'.",
            is_active=True,
        )
        db.add(learning_item)

    await db.commit()
    await db.refresh(conv)

    handoff = dict(conv.handoff_summary or {})
    if conv.customer:
        handoff["customer_email"] = conv.customer.email
        handoff["customer_phone"] = conv.customer.phone
        handoff["linked_channels"] = (conv.customer.metadata_info or {}).get("linked_channels", [conv.channel.value])

    return ConversationResponse(
        id=conv.id,
        business_id=conv.business_id,
        customer_id=conv.customer_id,
        customer_name=conv.customer.name if conv.customer else None,
        customer_handle=conv.customer.external_id if conv.customer else None,
        channel=conv.channel,
        status=conv.status,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        handoff_summary=handoff,
        messages=[MessageResponse.model_validate(m) for m in conv.messages]
    )


@router.get("/audit-logs", response_model=List[AuditLogItem])
async def list_audit_learning_logs(
    business_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Conversation)
        .where(Conversation.business_id == business_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
        .order_by(desc(Conversation.updated_at))
        .limit(40)
    )
    res = await db.execute(query)
    conversations = res.scalars().all()

    logs: List[AuditLogItem] = []
    for c in conversations:
        has_human = any(m.sender == MessageSender.HUMAN_OPERATOR for m in c.messages)
        last_cust_msg = next((m.content for m in reversed(c.messages) if m.sender == MessageSender.CUSTOMER), "General Inquiry")
        last_sol_msg = next((m.content for m in reversed(c.messages) if m.sender in [MessageSender.AGENT, MessageSender.HUMAN_OPERATOR]), "In progress")

        ch_name = c.channel.value if hasattr(c.channel, "value") else str(c.channel)

        logs.append(
            AuditLogItem(
                id=str(c.id)[:8],
                conversation_id=str(c.id),
                channel=ch_name.replace("_", " ").title(),
                customer_handle=c.customer.name or c.customer.external_id if c.customer else "@customer",
                resolved_by="Staff Specialist" if has_human else "AI Agent",
                resolution_type="Human Operator Intervention" if has_human else "AI Autonomous Grounding",
                problem_statement=last_cust_msg[:90],
                solution_statement=last_sol_msg[:120],
                learned_by_ai=True,
                created_at=c.created_at.strftime("%b %d, %I:%M %p"),
            )
        )
    return logs


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    business_id: uuid.UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists conversations with customer identity, cross-channel links, and message history,
    sorted by most recently updated.
    """
    try:
        query = (
            select(Conversation)
            .where(Conversation.business_id == business_id)
            .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
            .offset(skip)
            .limit(limit)
            .order_by(desc(Conversation.updated_at))
        )
        result = await db.execute(query)
        items = result.scalars().all()

        response = []
        for c in items:
            handoff = dict(c.handoff_summary or {})
            if c.customer:
                handoff["customer_email"] = c.customer.email
                handoff["customer_phone"] = c.customer.phone
                handoff["linked_channels"] = (c.customer.metadata_info or {}).get("linked_channels", [c.channel.value])

            c_dict = {
                "id": c.id,
                "business_id": c.business_id,
                "customer_id": c.customer_id,
                "customer_name": c.customer.name if c.customer else None,
                "customer_handle": c.customer.external_id if c.customer else None,
                "channel": c.channel,
                "status": c.status,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "handoff_summary": handoff,
                "messages": [MessageResponse.model_validate(m) for m in c.messages],
            }
            response.append(ConversationResponse(**c_dict))
        return response
    except Exception as exc:
        logger.error(f"[Conversations List Error] {exc}", exc_info=True)
        return []


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
    )
    res = await db.execute(query)
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")

    handoff = dict(c.handoff_summary or {})
    if c.customer:
        handoff["customer_email"] = c.customer.email
        handoff["customer_phone"] = c.customer.phone
        handoff["linked_channels"] = (c.customer.metadata_info or {}).get("linked_channels", [c.channel.value])

    return ConversationResponse(
        id=c.id,
        business_id=c.business_id,
        customer_id=c.customer_id,
        customer_name=c.customer.name if c.customer else None,
        customer_handle=c.customer.external_id if c.customer else None,
        channel=c.channel,
        status=c.status,
        created_at=c.created_at,
        updated_at=c.updated_at,
        handoff_summary=handoff,
        messages=[MessageResponse.model_validate(m) for m in c.messages]
    )