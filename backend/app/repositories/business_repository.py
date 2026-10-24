# FILE: backend/app/repositories/business_repository.py
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Business
from app.schemas.business import BusinessCreate, BusinessUpdate


class BusinessRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, business_id: uuid.UUID) -> Optional[Business]:
        query = select(Business).where(Business.id == business_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Business]:
        query = select(Business).where(Business.slug == slug)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Business]:
        query = select(Business).offset(skip).limit(limit).order_by(Business.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: BusinessCreate) -> Business:
        business = Business(
            name=data.name,
            slug=data.slug,
            description=data.description,
            communication_style=data.communication_style,
            is_active=data.is_active,
        )
        self.db.add(business)
        await self.db.commit()
        await self.db.refresh(business)
        return business

    async def update(self, business: Business, data: BusinessUpdate) -> Business:
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(business, key, value)
        await self.db.commit()
        await self.db.refresh(business)
        return business