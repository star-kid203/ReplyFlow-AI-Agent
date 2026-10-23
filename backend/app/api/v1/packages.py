# FILE: backend/app/api/v1/packages.py
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.packages import PackageTier, TIER_SPECIFICATIONS, get_tier_config
from app.models.entities import Business, TenantUsage
from app.services.quota_service import QuotaEnforcementService

router = APIRouter(prefix="/packages", tags=["Subscription Packages & Metering"])


class PackageDetailResponse(BaseModel):
    tier_id: str
    display_name: str
    monthly_price_usd: float
    monthly_response_limit: int
    monthly_customer_limit: int
    monthly_comment_limit: int
    per_channel_comment_cap: int
    allowed_channels: List[str]
    features: List[str]
    subscriber_count: int
    subscribers: List[Dict[str, Any]]


class TenantUsageResponse(BaseModel):
    plan_tier: str
    plan_display_name: str
    monthly_price_usd: float
    subscription_status: str
    responses_used: int
    responses_limit: int
    comments_used: int
    comments_limit: int
    customers_serviced: int
    customers_limit: int
    allowed_channels: List[str]


class UpdateTenantPlanRequest(BaseModel):
    plan_tier: PackageTier


@router.get("", response_model=List[PackageDetailResponse])
async def list_all_packages_with_subscribers(db: AsyncSession = Depends(get_db)):
    """Returns the 4 packages, quotas, and subscriber organizations."""
    biz_res = await db.execute(select(Business))
    all_businesses = biz_res.scalars().all()

    response: List[PackageDetailResponse] = []

    for tier_enum, spec in TIER_SPECIFICATIONS.items():
        matching_tenants = [
            {
                "id": str(b.id),
                "name": b.name,
                "slug": b.slug,
                "status": b.subscription_status,
                "is_active": b.is_active,
            }
            for b in all_businesses
            if b.plan_tier == tier_enum.value
        ]

        response.append(
            PackageDetailResponse(
                tier_id=tier_enum.value,
                display_name=spec["display_name"],
                monthly_price_usd=spec["monthly_price_usd"],
                monthly_response_limit=spec["monthly_response_limit"],
                monthly_customer_limit=spec["monthly_customer_limit"],
                monthly_comment_limit=spec["monthly_comment_limit"],
                per_channel_comment_cap=spec["per_channel_comment_cap"],
                allowed_channels=spec["allowed_channels"],
                features=spec["features"],
                subscriber_count=len(matching_tenants),
                subscribers=matching_tenants,
            )
        )

    return response


@router.get("/tenant/{business_id}/usage", response_model=TenantUsageResponse)
async def get_tenant_live_quota_usage(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Returns real-time usage consumption and package limits for a client workspace."""
    b_res = await db.execute(select(Business).where(Business.id == business_id))
    business = b_res.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Tenant organization not found")

    tier_cfg = get_tier_config(business.plan_tier)
    quota_svc = QuotaEnforcementService(db)
    usage = await quota_svc.get_or_create_usage(business.id)

    return TenantUsageResponse(
        plan_tier=business.plan_tier,
        plan_display_name=tier_cfg["display_name"],
        monthly_price_usd=tier_cfg["monthly_price_usd"],
        subscription_status=business.subscription_status,
        responses_used=usage.responses_used,
        responses_limit=tier_cfg["monthly_response_limit"],
        comments_used=usage.comments_used,
        comments_limit=tier_cfg["monthly_comment_limit"],
        customers_serviced=usage.customers_serviced,
        customers_limit=tier_cfg["monthly_customer_limit"],
        allowed_channels=tier_cfg["allowed_channels"],
    )


@router.post("/businesses/{business_id}/change-tier", status_code=status.HTTP_200_OK)
async def update_tenant_subscription_tier(
    business_id: uuid.UUID,
    payload: UpdateTenantPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Business).where(Business.id == business_id))
    business = res.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Business tenant not found")

    business.plan_tier = payload.plan_tier.value
    await db.commit()
    return {
        "status": "success",
        "message": f"Tenant '{business.name}' moved to '{payload.plan_tier.value}' package.",
        "plan_tier": business.plan_tier,
    }