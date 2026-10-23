# FILE: backend/app/integrations/webhooks.py
import hashlib
import hmac
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import ChannelType
from app.schemas.agent import ProcessMessageRequest
from app.api.v1.agent import process_customer_interaction

router = APIRouter(prefix="/webhooks", tags=["Universal Channel Webhooks"])

VERIFY_TOKEN = "replyflow_webhook_verify_token"


class NormalizedEvent(BaseModel):
    channel: ChannelType
    external_customer_id: str
    customer_name: Optional[str] = None
    content: str
    post_id: Optional[str] = None
    metadata_info: Dict[str, Any] = {}


# --- 1. META (Instagram & Facebook) Webhooks ---

@router.get("/meta")
async def meta_webhook_verification(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Meta Handshake verification for Instagram & Facebook comments/DMs.
    """
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@router.post("/meta/{business_id}")
async def meta_webhook_receiver(
    business_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives incoming comments and DMs from Meta (Instagram & Facebook).
    """
    payload = await request.json()

    # Extract Meta comment / message event
    try:
        entry = payload.get("entry", [])[0]
        # Instagram comment change
        if "changes" in entry:
            change = entry["changes"][0]["value"]
            sender_id = change.get("from", {}).get("id", "@social_user")
            sender_name = change.get("from", {}).get("username", "Social User")
            text = change.get("text", "")
            channel = ChannelType.INSTAGRAM_COMMENT
        # Direct Message
        elif "messaging" in entry:
            msg_event = entry["messaging"][0]
            sender_id = msg_event.get("sender", {}).get("id", "@social_user")
            sender_name = "DM User"
            text = msg_event.get("message", {}).get("text", "")
            channel = ChannelType.INSTAGRAM_DM
        else:
            return {"status": "ignored"}

        # Forward directly into ReplyFlow Agent Pipeline!
        agent_req = ProcessMessageRequest(
            business_id=business_id,
            external_customer_id=sender_id,
            channel=channel,
            content=text,
            customer_name=sender_name,
        )
        return await process_customer_interaction(agent_req, db)
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# --- 2. X (Twitter) Webhook Handshake & Ingestion ---

@router.get("/x")
async def x_crc_challenge(crc_token: str = Query(...)):
    """
    Twitter / X Account Activity API CRC challenge response (HMAC SHA-256).
    """
    consumer_secret = "replyflow_consumer_secret"
    digest = hmac.new(
        consumer_secret.encode("utf-8"),
        crc_token.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return {"response_token": f"sha256={digest.hex()}"}


@router.post("/x/{business_id}")
async def x_webhook_receiver(
    business_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives tweets, replies, and mentions from X.
    """
    payload = await request.json()
    try:
        tweet = payload.get("tweet_create_events", [])[0]
        sender_id = f"@{tweet.get('user', {}).get('screen_name')}"
        text = tweet.get("text", "")

        agent_req = ProcessMessageRequest(
            business_id=business_id,
            external_customer_id=sender_id,
            channel=ChannelType.WEBSITE_CHAT,  # Mapped to public stream
            content=text,
            customer_name=sender_id,
        )
        return await process_customer_interaction(agent_req, db)
    except Exception as e:
        return {"status": "ignored", "detail": str(e)}


# --- 3. TikTok & YouTube Video Comments Webhook ---

@router.post("/streaming/{business_id}")
async def streaming_platform_webhook(
    business_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Universal receiver for YouTube comment streams, TikTok video comments, Spotify Q&A, and Audiomack.
    """
    payload = await request.json()
    # Expecting normalized streaming format
    platform = payload.get("platform", "youtube")  # "youtube", "tiktok", "spotify", "audiomack"
    author = payload.get("author", "@listener")
    comment_text = payload.get("content", "")

    agent_req = ProcessMessageRequest(
        business_id=business_id,
        external_customer_id=author,
        channel=ChannelType.WEBSITE_CHAT,
        content=f"[{platform.upper()}]: {comment_text}",
        customer_name=author,
    )
    return await process_customer_interaction(agent_req, db)


# --- 4. Website Chat Widget & Mobile App Webhook ---

@router.post("/website/{business_id}")
async def website_chat_webhook(
    business_id: uuid.UUID,
    payload: ProcessMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Official webhook for website live chat widgets (WordPress, Shopify, Next.js).
    """
    return await process_customer_interaction(payload, db)