# FILE: backend/app/schemas/social.py
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.entities import ChannelType


class PostDirective(BaseModel):
    post_id: str = Field(..., description="Unique ID of the Instagram/Facebook post")
    post_caption: str = Field(..., description="Original post caption/content for context")
    creator_persona: str = Field(
        default="witty, polite, confident, concise",
        description="Tone instructions for the creator"
    )
    target_intents: List[str] = Field(
        default=["sarcasm", "criticism", "product_inquiry"],
        description="Filter rule: only reply to these categories"
    )
    ignore_generic_praise: bool = Field(
        default=True,
        description="If True, skips generic comments like 'Love this!' or '🔥'"
    )


class SocialCommentPayload(BaseModel):
    comment_id: str
    author_handle: str
    content: str
    parent_comment_id: Optional[str] = None


class BatchSocialIngestRequest(BaseModel):
    business_id: uuid.UUID
    channel: ChannelType
    directive: PostDirective
    comments: List[SocialCommentPayload]


class ProcessedSocialComment(BaseModel):
    comment_id: str
    author_handle: str
    content: str
    action_taken: str  # "replied_publicly", "sent_private_dm", "skipped_noise", "escalated"
    reason: str
    reply_text: Optional[str] = None


class BatchSocialIngestResponse(BaseModel):
    total_received: int
    total_processed: int
    total_skipped: int
    results: List[ProcessedSocialComment]