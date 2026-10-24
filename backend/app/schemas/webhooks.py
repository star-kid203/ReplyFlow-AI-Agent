# FILE: backend/app/schemas/webhooks.py
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GenericSocialWebhookPayload(BaseModel):
    business_id: uuid.UUID
    platform: str = Field(..., description="meta_instagram, meta_facebook, x_twitter, tiktok, youtube, website_chat")
    author_id: str
    author_name: Optional[str] = None
    content: str
    post_id: Optional[str] = None
    media_url: Optional[str] = None
    timestamp: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    status: str
    platform: str
    action_taken: str
    response_text: Optional[str] = None
    requires_human: bool = False