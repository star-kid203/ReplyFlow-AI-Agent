# FILE: backend/app/api/v1/social.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.social import BatchSocialIngestRequest, BatchSocialIngestResponse
from app.services.social_triage_service import SocialTriageService

router = APIRouter(prefix="/social", tags=["Social Media & Ingestion"])


def get_social_service(db: AsyncSession = Depends(get_db)) -> SocialTriageService:
    return SocialTriageService(db)


@router.post("/batch-ingest", response_model=BatchSocialIngestResponse, status_code=status.HTTP_200_OK)
async def ingest_social_comments_batch(
    payload: BatchSocialIngestRequest,
    service: SocialTriageService = Depends(get_social_service)
):
    """
    High-Volume Social Media Processing Engine:
    - Filters out emoji spam and friend tags.
    - Applies the Creator's Post Directive (e.g. only reply to sarcasm/critics).
    - Protects customer privacy via Public-to-Private DM handoff.
    - Accurately grounds replies in the parent post context.
    """
    return await service.process_batch(payload)