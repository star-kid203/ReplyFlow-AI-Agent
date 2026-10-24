# FILE: backend/app/schemas/incoming_message.py
import uuid
from typing import Optional
from pydantic import BaseModel, Field
from app.models.entities import ChannelType


class IncomingCustomerMessageRequest(BaseModel):
    business_id: uuid.UUID
    external_customer_id: str = Field(..., description="Unique ID on the channel, e.g. @sarah_tech on Instagram")
    channel: ChannelType
    content: str = Field(..., min_length=1, description="Message text")
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None