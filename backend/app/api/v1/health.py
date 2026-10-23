# FILE: backend/app/api/v1/health.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Verifies that the backend can execute queries against PostgreSQL."""
    try:
        result = await db.execute(text("SELECT 1"))
        db_alive = result.scalar() == 1
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database check failed: {str(exc)}"
        )

    return {
        "status": "healthy" if db_alive else "unhealthy",
        "database": "connected",
        "system": "ReplyFlow Operations API"
    }