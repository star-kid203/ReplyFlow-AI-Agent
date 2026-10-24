# FILE: backend/app/schemas/approval.py
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.entities import ActionStatus, ConversationStatus


class ApprovalActionResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    action_type: str
    status: ActionStatus
    reasoning: str
    payload: Dict[str, Any]
    requires_approval: bool
    approved_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApproveActionRequest(BaseModel):
    reviewer_name: str = Field(..., min_length=2, description="Staff member approving the action")
    custom_note: Optional[str] = None


class RejectActionRequest(BaseModel):
    reviewer_name: str = Field(..., min_length=2, description="Staff member rejecting the action")
    rejection_reason: str = Field(..., min_length=3, description="Reason for rejection")


class EscalationResponse(BaseModel):
    conversation_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    channel: str
    status: ConversationStatus
    last_customer_message: str
    escalation_reason: str
    created_at: datetime