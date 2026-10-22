# FILE: backend/app/services/knowledge_service.py
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import BusinessKnowledge
from app.repositories.knowledge_repository import KnowledgeRepository
from app.schemas.knowledge import KnowledgeCreate


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.repo = KnowledgeRepository(db)

    async def add_knowledge(self, data: KnowledgeCreate) -> BusinessKnowledge:
        return await self.repo.create(data)

    async def list_knowledge(
        self,
        business_id: uuid.UUID,
        category: Optional[str] = None
    ) -> List[BusinessKnowledge]:
        return await self.repo.list_by_business(business_id, category=category)