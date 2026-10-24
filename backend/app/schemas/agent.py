# FILE: backend/app/schemas/agent.py
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.entities import ChannelType


class ProcessMessageRequest(BaseModel):
    business_id: uuid.UUID
    external_customer_id: str = Field(..., description="Customer handle, e.g. @sarah_jones")
    channel: ChannelType
    content: str = Field(..., min_length=1, description="Incoming message text")
    customer_name: Optional[str] = None
    conversation_id: Optional[uuid.UUID] = Field(
        None, 
        description="ID of existing active conversation thread to maintain chat continuity and memory"
    )


class ProcessMessageResponse(BaseModel):
    conversation_id: uuid.UUID
    customer_id: uuid.UUID
    intent: str
    sentiment: str
    decision: str
    requires_human: bool
    escalation_reason: Optional[str] = None
    response_text: str
    retrieved_products_count: int
    agent_trace_logs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Dynamic LangGraph execution logs showing how each agent node reasoned"
    )