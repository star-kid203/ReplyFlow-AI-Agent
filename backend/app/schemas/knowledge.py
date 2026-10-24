# FILE: backend/app/schemas/knowledge.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBase(BaseModel):
    category: str = Field(..., max_length=100)
    title: str = Field(..., max_length=255)
    content: str = Field(..., min_length=5)
    is_active: bool = True


class KnowledgeCreate(KnowledgeBase):
    business_id: uuid.UUID


class KnowledgeResponse(KnowledgeBase):
    id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)