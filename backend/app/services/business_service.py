# FILE: backend/app/services/business_service.py
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import Business, BusinessKnowledge, ConnectorStatus, ConnectorType, BusinessConnector
from app.repositories.business_repository import BusinessRepository
from app.schemas.business import BusinessCreate, BusinessUpdate


class BusinessService:
    """
    Enterprise Tenant Lifecycle Engine.
    Provisions isolated tenant organizations without fake mock data.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BusinessRepository(db)

    async def get_business(self, business_id: uuid.UUID) -> Business:
        business = await self.repo.get_by_id(business_id)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Business with ID {business_id} not found."
            )
        return business

    async def list_businesses(self, skip: int = 0, limit: int = 100) -> List[Business]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_business(self, data: BusinessCreate) -> Business:
        existing = await self.repo.get_by_slug(data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A business with slug '{data.slug}' already exists."
            )

        # 1. Create Isolated Tenant Record with assigned Package Tier & Channels
        business = Business(
            name=data.name,
            slug=data.slug,
            description=data.description,
            communication_style=data.communication_style,
            agent_display_name=data.agent_display_name or f"{data.name} AI",
            plan_tier=data.plan_tier or "growth",
            subscription_status=data.subscription_status or "active",
            enabled_channels=data.enabled_channels or ["website_chat", "whatsapp", "linkedin_comment", "youtube_comment"],
            comment_rules=data.comment_rules or {},
            is_active=data.is_active,
        )
        self.db.add(business)
        await self.db.commit()
        await self.db.refresh(business)

        # 2. Attach default empty channel connectors (NO FAKE SERVICES OR PRICES)
        connectors_to_create = [
            BusinessConnector(
                business_id=business.id,
                connector_type=ConnectorType.STATIC_LOCAL,
                name="Dedicated Ground Truth Knowledge Base",
                base_url="internal://knowledge",
                status=ConnectorStatus.CONNECTED,
                config={"mode": "tenant_isolated"}
            )
        ]

        # If LinkedIn was enabled in the plan, attach the connector
        if "linkedin_comment" in business.enabled_channels or "linkedin_message" in business.enabled_channels:
            connectors_to_create.append(
                BusinessConnector(
                    business_id=business.id,
                    connector_type=ConnectorType.LINKEDIN,
                    name=f"{business.name} LinkedIn Channel Stream",
                    base_url="https://api.linkedin.com/rest/socialActions",
                    status=ConnectorStatus.CONNECTED,
                    config={"lead_capture_enabled": True}
                )
            )

        self.db.add_all(connectors_to_create)
        await self.db.commit()

        return business

    async def update_business(self, business_id: uuid.UUID, data: BusinessUpdate) -> Business:
        business = await self.get_business(business_id)
        return await self.repo.update(business, data)