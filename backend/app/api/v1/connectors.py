# FILE: backend/app/api/v1/connectors.py
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Business, BusinessConnector, ConnectorStatus, ConnectorType
from app.schemas.connector import (
    ConnectorCreate,
    ConnectorResponse,
    ConnectorUpdate,
    LiveInventoryCheckResult,
)

logger = logging.getLogger("replyflow.connectors")
router = APIRouter(prefix="/connectors", tags=["Connectors & ERP Ground Truth"])


class CreateConnectorPayload(BaseModel):
    business_id: uuid.UUID
    connector_type: str
    name: str
    credentials: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    base_url: Optional[str] = None
    status: Optional[str] = "connected"


class UpdateCredentialsRequest(BaseModel):
    credentials: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = None
    base_url: Optional[str] = None


class VerifyLinkedInResponse(BaseModel):
    is_valid: bool
    status: str
    organization_urn: str
    message: str


@router.get("", response_model=List[ConnectorResponse])
async def list_business_connectors(
    business_id: uuid.UUID = Query(..., description="Tenant Business ID"),
    db: AsyncSession = Depends(get_db)
):
    query = select(BusinessConnector).where(BusinessConnector.business_id == business_id)
    res = await db.execute(query)
    connectors = res.scalars().all()

    if connectors:
        return list(connectors)

    # Auto-provision standard connector set for new business
    b_res = await db.execute(select(Business).where(Business.id == business_id))
    business = b_res.scalar_one_or_none()
    desc_l = (business.description or "").lower() if business else ""
    is_service = any(w in desc_l for w in ["software", "consulting", "it", "cloud", "service"])

    if is_service:
        seed = [
            BusinessConnector(
                business_id=business_id,
                connector_type=ConnectorType.LINKEDIN,
                name=f"{business.name if business else 'Organization'} LinkedIn Showcase Stream",
                base_url="https://api.linkedin.com/rest/socialActions",
                status=ConnectorStatus.CONNECTED,
                config={"lead_capture": True},
            ),
            BusinessConnector(
                business_id=business_id,
                connector_type=ConnectorType.WHATSAPP_CLOUD,
                name="WhatsApp Business Cloud API Gateway",
                base_url="https://graph.facebook.com/v19.0",
                status=ConnectorStatus.CONNECTED,
                config={"auto_qualification": True},
            ),
            BusinessConnector(
                business_id=business_id,
                connector_type=ConnectorType.STATIC_LOCAL,
                name="Dedicated Ground Truth Knowledge Base",
                base_url="internal://services",
                status=ConnectorStatus.CONNECTED,
                config={"catalog_type": "services"},
            ),
        ]
    else:
        seed = [
            BusinessConnector(
                business_id=business_id,
                connector_type=ConnectorType.SHOPIFY,
                name="Shopify / E-Commerce Store",
                base_url="https://store.myshopify.com",
                status=ConnectorStatus.CONNECTED,
                config={"safety_stock_buffer": 1},
            ),
            BusinessConnector(
                business_id=business_id,
                connector_type=ConnectorType.CUSTOM_REST_ERP,
                name="Warehouse POS Endpoint",
                base_url="https://pos.local/api",
                status=ConnectorStatus.CONNECTED,
                config={"sync_mode": "live_lookup"},
            ),
        ]

    db.add_all(seed)
    await db.commit()
    return seed


@router.post("", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def create_or_upsert_connector(
    payload: CreateConnectorPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates or updates a platform connector (WhatsApp, LinkedIn, POS, Shopify)
    for a tenant with full credentials and configuration.
    """
    b_res = await db.execute(select(Business).where(Business.id == payload.business_id))
    business = b_res.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Tenant organization not found")

    c_type_str = payload.connector_type.lower()
    matched_type = ConnectorType.WHATSAPP_CLOUD
    for member in ConnectorType:
        if member.value.lower() == c_type_str or member.name.lower() == c_type_str:
            matched_type = member
            break

    q = select(BusinessConnector).where(
        BusinessConnector.business_id == payload.business_id,
        BusinessConnector.connector_type == matched_type
    )
    res = await db.execute(q)
    conn = res.scalar_one_or_none()

    if conn:
        conn.name = payload.name
        conn.credentials = {**conn.credentials, **payload.credentials}
        conn.config = {**conn.config, **payload.config}
        if payload.base_url:
            conn.base_url = payload.base_url
        conn.status = ConnectorStatus.CONNECTED
        conn.is_active = True
    else:
        conn = BusinessConnector(
            business_id=payload.business_id,
            connector_type=matched_type,
            name=payload.name,
            base_url=payload.base_url or "https://graph.facebook.com/v19.0",
            credentials=payload.credentials,
            config=payload.config,
            status=ConnectorStatus.CONNECTED,
            is_active=True,
        )
        db.add(conn)

    await db.commit()
    await db.refresh(conn)
    logger.info(f"[Connector Activated] Tenant {business.name} activated {matched_type.value}")
    return conn


@router.post("/{connector_id}/credentials", response_model=ConnectorResponse)
async def update_connector_credentials(
    connector_id: uuid.UUID,
    payload: UpdateCredentialsRequest,
    db: AsyncSession = Depends(get_db)
):
    query = select(BusinessConnector).where(BusinessConnector.id == connector_id)
    res = await db.execute(query)
    conn = res.scalar_one_or_none()

    if not conn:
        raise HTTPException(status_code=404, detail="Connector not found")

    conn.credentials = {**conn.credentials, **payload.credentials}
    if payload.config:
        conn.config = {**conn.config, **payload.config}
    if payload.base_url:
        conn.base_url = payload.base_url
    conn.status = ConnectorStatus.CONNECTED
    conn.is_active = True

    await db.commit()
    await db.refresh(conn)
    return conn


# --- OAUTH: LINKEDIN 1-CLICK CONNECTION ---

@router.get("/linkedin/authorize")
async def linkedin_oauth_authorize(
    business_id: uuid.UUID = Query(..., description="Tenant Business ID")
):
    client_id = getattr(settings, "LINKEDIN_CLIENT_ID", "") or "770ay95magstar"
    redirect_uri = "https://pork-sample-charm.ngrok-free.dev/api/v1/connectors/linkedin/callback"

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": str(business_id),
        "scope": "openid profile email w_member_social",
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return RedirectResponse(auth_url)


@router.get("/linkedin/callback")
async def linkedin_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if error or not code:
        return RedirectResponse("http://localhost:3000/knowledge?error=linkedin_cancelled")

    try:
        business_uuid = uuid.UUID(state)
    except Exception:
        business_uuid = None

    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    client_id = getattr(settings, "LINKEDIN_CLIENT_ID", "") or "770ay95magstar"
    client_secret = getattr(settings, "LINKEDIN_CLIENT_SECRET", "")
    redirect_uri = "https://pork-sample-charm.ngrok-free.dev/api/v1/connectors/linkedin/callback"

    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(token_url, data=token_payload)
        if resp.status_code == 200:
            token_data = resp.json()
            access_token = token_data.get("access_token")

            if business_uuid and access_token:
                q = select(BusinessConnector).where(
                    BusinessConnector.business_id == business_uuid,
                    BusinessConnector.connector_type == ConnectorType.LINKEDIN
                )
                res = await db.execute(q)
                conn = res.scalar_one_or_none()

                if not conn:
                    conn = BusinessConnector(
                        business_id=business_uuid,
                        connector_type=ConnectorType.LINKEDIN,
                        name="LinkedIn Channel Stream",
                        status=ConnectorStatus.CONNECTED,
                        credentials={"access_token": access_token},
                        config={"live_dispatch": True},
                    )
                    db.add(conn)
                else:
                    conn.credentials = {"access_token": access_token}
                    conn.status = ConnectorStatus.CONNECTED

                await db.commit()
                return RedirectResponse(f"http://localhost:3000/knowledge?tenant={business_uuid}&connector_success=linkedin")

    return RedirectResponse("http://localhost:3000/knowledge?connector_status=verified")


# --- OAUTH: YOUTUBE 1-CLICK CONNECTION ---

@router.get("/youtube/authorize")
async def youtube_oauth_authorize(
    business_id: uuid.UUID = Query(..., description="Tenant Business ID")
):
    client_id = getattr(settings, "YOUTUBE_CLIENT_ID", "")
    redirect_uri = "https://pork-sample-charm.ngrok-free.dev/api/v1/connectors/youtube/callback"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.force-ssl",
        "access_type": "offline",
        "prompt": "consent",
        "state": str(business_id),
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(auth_url)


@router.get("/youtube/callback")
async def youtube_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    if error or not code:
        return RedirectResponse("http://localhost:3000/knowledge?error=youtube_cancelled")

    try:
        business_uuid = uuid.UUID(state)
    except Exception:
        business_uuid = None

    token_url = "https://oauth2.googleapis.com/token"
    client_id = getattr(settings, "YOUTUBE_CLIENT_ID", "")
    client_secret = getattr(settings, "YOUTUBE_CLIENT_SECRET", "")
    redirect_uri = "https://pork-sample-charm.ngrok-free.dev/api/v1/connectors/youtube/callback"

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(token_url, data=data)
        if resp.status_code == 200:
            token_data = resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            if business_uuid and access_token:
                # 1. Fetch live YouTube Channel identity using the new token
                channel_info_url = "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"
                headers = {"Authorization": f"Bearer {access_token}"}
                ch_resp = await client.get(channel_info_url, headers=headers)

                channel_title = "YouTube Channel"
                channel_id = ""
                channel_handle = ""
                channel_avatar = ""

                if ch_resp.status_code == 200:
                    ch_data = ch_resp.json()
                    items = ch_data.get("items", [])
                    if items:
                        first_channel = items[0]
                        channel_id = first_channel.get("id", "")
                        snippet = first_channel.get("snippet", {})
                        channel_title = snippet.get("title", "My YouTube Channel")
                        channel_handle = snippet.get("customUrl", "")
                        channel_avatar = snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                        logger.info(f"[YouTube OAuth] Linked Channel: '{channel_title}' ({channel_handle}) [ID: {channel_id}]")
                    else:
                        logger.warning("[YouTube OAuth] No channel exists for this Google Account.")
                        channel_title = "Personal Google Account"

                # 2. Upsert into database
                q = select(BusinessConnector).where(
                    BusinessConnector.business_id == business_uuid,
                    BusinessConnector.connector_type == ConnectorType.YOUTUBE_API
                )
                res = await db.execute(q)
                conn = res.scalar_one_or_none()

                creds = {"access_token": access_token}
                if refresh_token:
                    creds["refresh_token"] = refresh_token

                config_data = {
                    "channel_id": channel_id,
                    "channel_title": channel_title,
                    "channel_handle": channel_handle,
                    "channel_avatar": channel_avatar,
                    "connected_at": datetime.now(timezone.utc).isoformat(),
                    "comment_triage": True,
                }

                if not conn:
                    conn = BusinessConnector(
                        business_id=business_uuid,
                        connector_type=ConnectorType.YOUTUBE_API,
                        name=f"YouTube Stream: {channel_title}",
                        status=ConnectorStatus.CONNECTED,
                        credentials=creds,
                        config=config_data,
                        is_active=True,
                    )
                    db.add(conn)
                else:
                    conn.credentials = {**conn.credentials, **creds}
                    conn.config = {**conn.config, **config_data}
                    conn.status = ConnectorStatus.CONNECTED
                    conn.name = f"YouTube Stream: {channel_title}"
                    conn.is_active = True

                await db.commit()
                return RedirectResponse(f"http://localhost:3000/knowledge?tenant={business_uuid}&connector_success=youtube")

    return RedirectResponse("http://localhost:3000/knowledge?error=youtube_auth_failed")