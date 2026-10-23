# FILE: backend/app/api/v1/webhooks.py
import asyncio
import logging
from typing import Any, Dict, List, Optional
import uuid
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.integrations.dispatcher import OutboundSocialDispatcher
from app.integrations.linkedin_adapter import LinkedInAdapter
from app.models.entities import (
    Business,
    BusinessConnector,
    ChannelType,
    ConnectorType,
    Conversation,
)
from app.schemas.agent import ProcessMessageRequest
from app.schemas.webhooks import GenericSocialWebhookPayload, WebhookResponse
from app.services.quota_service import QuotaEnforcementService
from app.api.v1.agent import process_customer_interaction

logger = logging.getLogger("replyflow.webhooks")
router = APIRouter(prefix="/webhooks", tags=["Social Media Webhooks"])


# --- 1. LINKEDIN WEBHOOK & DISPATCH ENGINE ---

@router.post("/linkedin", status_code=status.HTTP_200_OK)
async def handle_linkedin_webhook(
    request: Request,
    business_id: uuid.UUID = Query(..., description="Tenant Organization ID"),
    x_li_signature: Optional[str] = Header(None, alias="X-LI-Signature"),
    db: AsyncSession = Depends(get_db)
):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignored_empty_payload"}

    b_res = await db.execute(select(Business).where(Business.id == business_id))
    business = b_res.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Tenant organization not found")

    quota_service = QuotaEnforcementService(db)
    can_proceed, reason = await quota_service.verify_can_process(
        business=business,
        channel=ChannelType.LINKEDIN_COMMENT.value,
        is_comment=True
    )
    if not can_proceed:
        logger.warning(f"[LinkedIn Webhook Quota Block] {business.name}: {reason}")
        return {"status": "quota_exceeded", "detail": reason}

    parsed = LinkedInAdapter.parse_comment_event(body)
    if not parsed or not parsed.get("text"):
        return {"status": "ignored_non_comment_event"}

    agent_result = await process_customer_interaction(
        payload=ProcessMessageRequest(
            business_id=business.id,
            external_customer_id=parsed["author_id"],
            channel=ChannelType.LINKEDIN_COMMENT,
            content=parsed["text"],
            customer_name=parsed.get("author_name"),
        ),
        db=db,
    )

    conn_res = await db.execute(select(BusinessConnector).where(
        BusinessConnector.business_id == business.id,
        BusinessConnector.connector_type == ConnectorType.LINKEDIN
    ))
    li_conn = conn_res.scalar_one_or_none()
    access_token = li_conn.credentials.get("access_token", "demo_sandbox_token") if li_conn else "demo_sandbox_token"

    if agent_result.response_text and parsed.get("parent_activity_urn"):
        await LinkedInAdapter.post_comment_reply(
            access_token=access_token,
            target_activity_urn=parsed["parent_activity_urn"],
            reply_text=agent_result.response_text,
            parent_comment_urn=parsed.get("comment_urn"),
        )

    await quota_service.record_successful_interaction(
        business_id=business.id,
        channel=ChannelType.LINKEDIN_COMMENT.value,
        is_comment=True
    )

    return {
        "status": "success",
        "action": agent_result.decision,
        "reply": agent_result.response_text,
    }


# --- 2. META (WHATSAPP, INSTAGRAM & FACEBOOK) WEBHOOK PIPELINE ---

@router.get("/meta")
async def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """
    Universal Meta Handshake verification for WhatsApp, Instagram, and Facebook.
    """
    VERIFY_TOKEN = "replyflow_meta_token_secret"
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info(f"[Meta Webhook] Successfully verified handshake with challenge: {hub_challenge}")
        return Response(content=str(hub_challenge), media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


async def _process_meta_incoming_event(body: Dict[str, Any], business_id: Optional[uuid.UUID], db: AsyncSession):
    """
    Parses and handles Meta webhooks across WhatsApp Cloud API, Instagram Comments/DMs, and Facebook Pages.
    """
    obj_type = body.get("object")
    entries = body.get("entry", [])

    target_biz_id = business_id
    if not target_biz_id:
        b_res = await db.execute(
            select(Business).where(Business.is_active == True).order_by(Business.created_at).limit(1)
        )
        first_biz = b_res.scalars().first()
        if first_biz:
            target_biz_id = first_biz.id

    if not target_biz_id:
        logger.warning("[Meta Webhook] No active tenant organization found to handle interaction.")
        return

    # A. WHATSAPP CLOUD API PARSER
    if obj_type == "whatsapp_business_account":
        for entry in entries:
            for change in entry.get("changes", []):
                val = change.get("value", {})
                metadata = val.get("metadata", {})
                phone_number_id = str(metadata.get("phone_number_id", ""))

                resolved_biz_id = target_biz_id
                if phone_number_id:
                    conn_query = select(BusinessConnector).where(
                        BusinessConnector.connector_type == ConnectorType.WHATSAPP_CLOUD,
                        BusinessConnector.is_active == True,
                    )
                    conn_res = await db.execute(conn_query)
                    for c in conn_res.scalars().all():
                        cfg_pid = str(c.config.get("phone_number_id") or c.config.get("phone_id") or "")
                        if cfg_pid == phone_number_id:
                            resolved_biz_id = c.business_id
                            logger.info(f"[Multi-Tenant Router] WhatsApp {phone_number_id} dynamically mapped to tenant {resolved_biz_id}")
                            break

                for msg in val.get("messages", []):
                    sender_wa_id = msg.get("from")
                    msg_text = msg.get("text", {}).get("body", "") if msg.get("type") == "text" else ""
                    contact_name = val.get("contacts", [{}])[0].get("profile", {}).get("name", sender_wa_id)

                    if msg_text and sender_wa_id:
                        logger.info(f"[WhatsApp Inbound] Received message from {contact_name} ({sender_wa_id}): '{msg_text}'")
                        agent_res = await process_customer_interaction(
                            payload=ProcessMessageRequest(
                                business_id=resolved_biz_id,
                                external_customer_id=sender_wa_id,
                                channel=ChannelType.WHATSAPP,
                                content=msg_text,
                                customer_name=contact_name,
                            ),
                            db=db,
                        )

                        if agent_res.response_text:
                            from sqlalchemy.orm import selectinload
                            conv_q = select(Conversation).where(Conversation.id == agent_res.conversation_id).options(selectinload(Conversation.customer))
                            c_res = await db.execute(conv_q)
                            conv = c_res.scalar_one_or_none()
                            if conv:
                                dispatcher = OutboundSocialDispatcher(db)
                                await dispatcher.dispatch_reply(conv, agent_res.response_text)

    # B. INSTAGRAM & FACEBOOK PARSER
    elif obj_type in ["instagram", "page"]:
        for entry in entries:
            for change in entry.get("changes", []):
                val = change.get("value", {})
                text_msg = val.get("text") or val.get("message")
                sender_id = val.get("from", {}).get("id") or val.get("sender", {}).get("id")
                s_name = val.get("from", {}).get("username") or val.get("from", {}).get("name")

                if text_msg and sender_id:
                    ch = ChannelType.INSTAGRAM_COMMENT if obj_type == "instagram" else ChannelType.FACEBOOK_COMMENT
                    logger.info(f"[{obj_type.upper()} Comment] From {s_name}: '{text_msg}'")
                    await process_customer_interaction(
                        payload=ProcessMessageRequest(
                            business_id=target_biz_id,
                            external_customer_id=f"@{s_name or sender_id}",
                            channel=ch,
                            content=text_msg,
                            customer_name=s_name,
                        ),
                        db=db,
                    )

            for msg_event in entry.get("messaging", []):
                sender_id = msg_event.get("sender", {}).get("id")
                text_msg = msg_event.get("message", {}).get("text", "")

                if text_msg and sender_id:
                    logger.info(f"[{obj_type.upper()} DM] From {sender_id}: '{text_msg}'")
                    await process_customer_interaction(
                        payload=ProcessMessageRequest(
                            business_id=target_biz_id,
                            external_customer_id=sender_id,
                            channel=ChannelType.INSTAGRAM_DM,
                            content=text_msg,
                            customer_name=f"User_{sender_id[:6]}",
                        ),
                        db=db,
                    )


@router.post("/meta", status_code=status.HTTP_200_OK)
async def handle_meta_webhook_root(
    request: Request,
    background_tasks: BackgroundTasks,
    business_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignored_empty_payload"}

    background_tasks.add_task(_process_meta_incoming_event, body, business_id, db)
    return {"status": "accepted"}


@router.post("/meta/{business_id}", status_code=status.HTTP_200_OK)
async def handle_meta_webhook_for_tenant(
    business_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignored_empty_payload"}

    background_tasks.add_task(_process_meta_incoming_event, body, business_id, db)
    return {"status": "accepted"}


# --- 3. UNIFIED INGESTION (X, TIKTOK, YOUTUBE, SPOTIFY, WEB) ---

@router.post("/ingest", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def ingest_platform_webhook(
    payload: GenericSocialWebhookPayload,
    db: AsyncSession = Depends(get_db)
):
    b_res = await db.execute(select(Business).where(Business.id == payload.business_id))
    business = b_res.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Tenant business not found")

    channel_map = {
        "meta_instagram": ChannelType.INSTAGRAM_COMMENT,
        "meta_facebook": ChannelType.FACEBOOK_COMMENT,
        "whatsapp": ChannelType.WHATSAPP,
        "website_chat": ChannelType.WEBSITE_CHAT,
        "linkedin_comment": ChannelType.LINKEDIN_COMMENT,
        "linkedin_message": ChannelType.LINKEDIN_MESSAGE,
        "youtube_comment": ChannelType.YOUTUBE_COMMENT,
        "spotify_qa": ChannelType.SPOTIFY_QA,
        "tiktok": ChannelType.TIKTOK,
    }

    resolved_channel = channel_map.get(payload.platform, ChannelType.WEBSITE_CHAT)

    quota_service = QuotaEnforcementService(db)
    is_comm = "comment" in payload.platform
    can_proceed, reason = await quota_service.verify_can_process(
        business=business,
        channel=resolved_channel.value,
        is_comment=is_comm
    )
    if not can_proceed:
        return WebhookResponse(
            status="quota_exceeded",
            platform=payload.platform,
            action_taken="blocked_by_plan_limit",
            response_text=f"[Quota Exceeded: {reason}]",
            requires_human=True,
        )

    agent_result = await process_customer_interaction(
        payload=ProcessMessageRequest(
            business_id=payload.business_id,
            external_customer_id=payload.author_id,
            channel=resolved_channel,
            content=payload.content,
            customer_name=payload.author_name,
        ),
        db=db,
    )

    await quota_service.record_successful_interaction(
        business_id=business.id,
        channel=resolved_channel.value,
        is_comment=is_comm
    )

    return WebhookResponse(
        status="success",
        platform=payload.platform,
        action_taken=agent_result.decision,
        response_text=agent_result.response_text,
        requires_human=agent_result.requires_human,
    )


# --- 4. UNIVERSAL WEBSITE FORM & SUPPORT TICKET INTERCEPTOR ---

class WebsiteFormWebhookPayload(BaseModel):
    name: Optional[str] = "Website Visitor"
    email: Optional[str] = None
    phone: Optional[str] = None
    subject: Optional[str] = "Website Inquiry"
    message: str = Field(..., min_length=2, description="Form submission content or ticket text")
    ticket_id: Optional[str] = None
    form_source: Optional[str] = "contact_form"


@router.post("/forms/{business_id}", status_code=status.HTTP_200_OK)
async def handle_website_form_interceptor(
    business_id: uuid.UUID,
    payload: WebsiteFormWebhookPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Universal Website Form & Support Ticket Interceptor.
    Intercepts web forms, contact inquiries, and support tickets:
    - Enforces sub-second triage and resolution.
    - Resolves routine inquiries immediately via branded Email/WhatsApp.
    - Escalates high-risk disputes with an Executive Staff Brief.
    """
    b_res = await db.execute(select(Business).where(Business.id == business_id))
    business = b_res.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Tenant organization not found")

    external_id = payload.email or payload.phone or f"web_visitor_{uuid.uuid4().hex[:6]}"

    agent_result = await process_customer_interaction(
        payload=ProcessMessageRequest(
            business_id=business.id,
            external_customer_id=external_id,
            channel=ChannelType.WEBSITE_CHAT,
            content=f"[{payload.form_source.upper()} - {payload.subject}]: {payload.message}",
            customer_name=payload.name,
        ),
        db=db,
    )

    if payload.email and agent_result.response_text:
        try:
            from app.integrations.email_adapter import EmailAdapter
            asyncio.create_task(
                EmailAdapter.send_meeting_invite_email(
                    recipient_email=payload.email,
                    recipient_name=payload.name or "Valued Client",
                    business_name=business.name,
                    meeting_time="Immediate Inquiry Confirmation",
                    meeting_link="http://localhost:3000/?tenant=" + str(business.id),
                    project_scope=agent_result.response_text[:120],
                )
            )
        except Exception as e:
            logger.warning(f"[Form Interceptor Email Notice] {e}")

    return {
        "status": "success",
        "interceptor_action": agent_result.decision,
        "resolution_delivery": "email_dispatched" if payload.email else "inbox_provisioned",
        "response_summary": agent_result.response_text,
        "requires_human": agent_result.requires_human,
        "ticket_reference": payload.ticket_id or str(agent_result.conversation_id)[:8].upper(),
    }