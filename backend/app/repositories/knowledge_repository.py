# FILE: backend/app/repositories/knowledge_repository.py
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import BusinessKnowledge
from app.schemas.knowledge import KnowledgeCreate


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, knowledge_id: uuid.UUID, business_id: uuid.UUID) -> Optional[BusinessKnowledge]:
        query = select(BusinessKnowledge).where(
            BusinessKnowledge.id == knowledge_id,
            BusinessKnowledge.business_id == business_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_by_business(
        self,
        business_id: uuid.UUID,
        category: Optional[str] = None
    ) -> List[BusinessKnowledge]:
        query = select(BusinessKnowledge).where(
            BusinessKnowledge.business_id == business_id,
            BusinessKnowledge.is_active == True
        )
        if category:
            query = query.where(BusinessKnowledge.category == category)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: KnowledgeCreate) -> BusinessKnowledge:
        item = BusinessKnowledge(
            business_id=data.business_id,
            category=data.category,
            title=data.title,
            content=data.content,
            is_active=data.is_active,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item