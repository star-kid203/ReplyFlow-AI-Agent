# FILE: backend/app/api/v1/businesses.py
import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import Business, Conversation, Customer, Message
from app.schemas.business import BusinessCreate, BusinessResponse, BusinessUpdate
from app.services.business_service import BusinessService

router = APIRouter(prefix="/businesses", tags=["Businesses"])


def get_business_service(db: AsyncSession = Depends(get_db)) -> BusinessService:
    return BusinessService(db)


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    payload: BusinessCreate,
    service: BusinessService = Depends(get_business_service)
):
    """Register / Provision a new tenant (e.g. Douatech Solutions)."""
    return await service.create_business(payload)


@router.get("", response_model=List[BusinessResponse])
async def list_businesses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: BusinessService = Depends(get_business_service)
):
    """Retrieve all provisioned client organizations."""
    return await service.list_businesses(skip=skip, limit=limit)


@router.get("/platform/metrics", response_model=Dict[str, Any])
async def get_platform_master_metrics(db: AsyncSession = Depends(get_db)):
    """Master Admin Telemetry: Total tenants, active threads, messages, and channel distribution."""
    total_tenants = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    total_convs = (await db.execute(select(func.count(Conversation.id)))).scalar() or 0
    total_messages = (await db.execute(select(func.count(Message.id)))).scalar() or 0

    return {
        "total_tenants": total_tenants,
        "total_conversations": total_convs,
        "total_messages": total_messages,
        "gateway_status": "GROQ LPU Active",
        "isolation_level": "Logical Row-Level (Tenant ID Partitioning)",
    }


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: uuid.UUID,
    service: BusinessService = Depends(get_business_service)
):
    return await service.get_business(business_id)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: uuid.UUID,
    payload: BusinessUpdate,
    service: BusinessService = Depends(get_business_service)
):
    """Update settings, package tier, or comment triage rules for a business."""
    return await service.update_business(business_id, payload)


@router.delete("/{business_id}", status_code=status.HTTP_200_OK)
async def delete_business(
    business_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """De-provision and remove a tenant organization."""
    query = select(Business).where(Business.id == business_id)
    res = await db.execute(query)
    b = res.scalar_one_or_none()
    if not b:
        raise HTTPException(status_code=404, detail="Tenant organization not found")

    await db.delete(b)
    await db.commit()
    return {"status": "success", "message": f"Tenant '{b.name}' de-provisioned successfully"}