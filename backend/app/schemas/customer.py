# FILE: backend/app/schemas/customer.py
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    external_id: str = Field(..., description="Unique ID on the channel, e.g., @handle or phone number")
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class CustomerCreate(CustomerBase):
    business_id: uuid.UUID


class CustomerResponse(CustomerBase):
    id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)