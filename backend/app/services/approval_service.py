# FILE: backend/app/services/approval_service.py
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    ActionStatus,
    AgentAction,
    Conversation,
    ConversationStatus,
    Customer,
    Message,
    MessageSender,
)
from app.schemas.approval import (
    ApprovalActionResponse,
    ApproveActionRequest,
    EscalationResponse,
    RejectActionRequest,
)


class ApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_pending_approvals(self, business_id: uuid.UUID) -> List[AgentAction]:
        """Fetch all agent actions requiring human approval for a business."""
        query = (
            select(AgentAction)
            .join(Conversation, AgentAction.conversation_id == Conversation.id)
            .where(
                Conversation.business_id == business_id,
                AgentAction.requires_approval.is_(True),
                AgentAction.status == ActionStatus.PENDING
            )
            .order_by(desc(AgentAction.created_at))
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def approve_action(
        self,
        action_id: uuid.UUID,
        payload: ApproveActionRequest
    ) -> AgentAction:
        """Human approves a proposed agent action (e.g. approve refund or drafted message)."""
        query = select(AgentAction).where(AgentAction.id == action_id)
        result = await self.db.execute(query)
        action = result.scalar_one_or_none()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent action {action_id} not found."
            )

        if action.status != ActionStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Action is already in '{action.status}' state."
            )

        # Update action state
        action.status = ActionStatus.APPROVED
        action.approved_by = payload.reviewer_name
        if payload.custom_note:
            action.payload["approval_note"] = payload.custom_note

        # Append approved message to conversation so customer receives it
        agent_reply = action.payload.get("proposed_action") or "Your request has been approved by our team."
        approved_msg = Message(
            conversation_id=action.conversation_id,
            sender=MessageSender.HUMAN_OPERATOR,
            content=f"[Approved by {payload.reviewer_name}]: {agent_reply}",
            metadata_info={"approved_action_id": str(action.id)}
        )
        self.db.add(approved_msg)

        # Update conversation status back to OPEN / RESOLVED
        conv_query = select(Conversation).where(Conversation.id == action.conversation_id)
        conv_res = await self.db.execute(conv_query)
        conv = conv_res.scalar_one()
        conv.status = ConversationStatus.OPEN

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def reject_action(
        self,
        action_id: uuid.UUID,
        payload: RejectActionRequest
    ) -> AgentAction:
        """Human rejects a proposed agent action."""
        query = select(AgentAction).where(AgentAction.id == action_id)
        result = await self.db.execute(query)
        action = result.scalar_one_or_none()

        if not action:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent action {action_id} not found."
            )

        action.status = ActionStatus.REJECTED
        action.approved_by = payload.reviewer_name
        action.payload["rejection_reason"] = payload.rejection_reason

        # Send polite rejection to customer
        reject_msg = Message(
            conversation_id=action.conversation_id,
            sender=MessageSender.HUMAN_OPERATOR,
            content=(
                f"Your request was reviewed by {payload.reviewer_name}. "
                f"Unfortunately, it cannot be approved at this time: {payload.rejection_reason}"
            ),
            metadata_info={"rejected_action_id": str(action.id)}
        )
        self.db.add(reject_msg)

        await self.db.commit()
        await self.db.refresh(action)
        return action

    async def list_escalations(self, business_id: uuid.UUID) -> List[EscalationResponse]:
        """Fetch all escalated conversations needing human support staff."""
        query = (
            select(Conversation)
            .where(
                Conversation.business_id == business_id,
                Conversation.status == ConversationStatus.ESCALATED
            )
            .options(selectinload(Conversation.messages), selectinload(Conversation.customer))
            .order_by(desc(Conversation.updated_at))
        )
        result = await self.db.execute(query)
        conversations = result.scalars().all()

        escalations = []
        for conv in conversations:
            last_msg = conv.messages[-1].content if conv.messages else "No messages"
            escalations.append(
                EscalationResponse(
                    conversation_id=conv.id,
                    customer_id=conv.customer_id,
                    customer_name=conv.customer.name if conv.customer else "Unknown",
                    channel=conv.channel.value,
                    status=conv.status,
                    last_customer_message=last_msg,
                    escalation_reason="Flagged by ReplyFlow Agent for human intervention.",
                    created_at=conv.created_at,
                )
            )
        return escalations

    async def list_audit_logs(
        self,
        business_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50
    ) -> List[AgentAction]:
        """Audit trail: View all agent actions and reasoning for compliance."""
        query = (
            select(AgentAction)
            .join(Conversation, AgentAction.conversation_id == Conversation.id)
            .where(Conversation.business_id == business_id)
            .order_by(desc(AgentAction.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())