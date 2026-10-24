# FILE: backend/app/schemas/business.py
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BusinessBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    communication_style: str = Field(default="professional, consultative, and concise")
    agent_display_name: Optional[str] = None
    plan_tier: Optional[str] = Field(default="growth", description="startup, stella, business, business_premium")
    subscription_status: Optional[str] = Field(default="active", description="active, past_due, canceled")
    enabled_channels: Optional[List[str]] = Field(
        default_factory=lambda: ["website_chat", "whatsapp", "linkedin_comment", "youtube_comment"]
    )
    comment_rules: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "filter_noise": True,
            "convert_leads": True,
            "route_sensitive_to_dm": True,
            "target_intents": ["inquiry", "pricing", "lead", "criticism"]
        }
    )
    is_active: bool = True


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    communication_style: Optional[str] = None
    agent_display_name: Optional[str] = None
    plan_tier: Optional[str] = None
    subscription_status: Optional[str] = None
    enabled_channels: Optional[List[str]] = None
    comment_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class BusinessResponse(BusinessBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)