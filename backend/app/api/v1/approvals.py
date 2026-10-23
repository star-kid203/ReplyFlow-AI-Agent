# FILE: backend/app/api/v1/approvals.py
import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.approval import (
    ApprovalActionResponse,
    ApproveActionRequest,
    EscalationResponse,
    RejectActionRequest,
)
from app.services.approval_service import ApprovalService

# IMPORTANT: prefix must be /approvals
router = APIRouter(prefix="/approvals", tags=["Human Operations & Approvals"])


def get_approval_service(db: AsyncSession = Depends(get_db)) -> ApprovalService:
    return ApprovalService(db)


# Matches BOTH /api/v1/approvals AND /api/v1/approvals/pending
@router.get("", response_model=List[ApprovalActionResponse])
@router.get("/pending", response_model=List[ApprovalActionResponse])
async def list_pending_approvals(
    business_id: uuid.UUID = Query(..., description="Tenant business ID"),
    service: ApprovalService = Depends(get_approval_service)
):
    """List all agent actions waiting for human sign-off."""
    return await service.list_pending_approvals(business_id)


@router.post("/{action_id}/approve", response_model=ApprovalActionResponse)
async def approve_agent_action(
    action_id: uuid.UUID,
    payload: ApproveActionRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """Staff approves an agent action (e.g. approve refund)."""
    return await service.approve_action(action_id, payload)


@router.post("/{action_id}/reject", response_model=ApprovalActionResponse)
async def reject_agent_action(
    action_id: uuid.UUID,
    payload: RejectActionRequest,
    service: ApprovalService = Depends(get_approval_service)
):
    """Staff rejects an agent action with a reason."""
    return await service.reject_action(action_id, payload)