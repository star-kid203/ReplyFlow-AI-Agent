# FILE: backend/app/schemas/conversation.py
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.entities import ChannelType, ConversationStatus, MessageSender


# Message schemas
class MessageCreate(BaseModel):
    sender: MessageSender
    content: str = Field(..., min_length=1)
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender: MessageSender
    content: str
    metadata_info: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Conversation schemas
class ConversationCreate(BaseModel):
    business_id: uuid.UUID
    customer_id: uuid.UUID
    channel: ChannelType


class ConversationResponse(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: Optional[str] = None
    customer_handle: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    linked_channels: List[str] = Field(default_factory=list)
    channel: ChannelType
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    handoff_summary: Dict[str, Any] = Field(default_factory=dict)
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)