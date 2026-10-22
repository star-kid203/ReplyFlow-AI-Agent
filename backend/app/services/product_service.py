# FILE: backend/app/services/product_service.py
import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self, db: AsyncSession):
        self.repo = ProductRepository(db)

    async def create_product(self, data: ProductCreate) -> Product:
        existing = await self.repo.get_by_sku(data.sku, data.business_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{data.sku}' already exists for this business."
            )
        return await self.repo.create(data)

    async def list_products(self, business_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[Product]:
        return await self.repo.list_by_business(business_id, skip=skip, limit=limit)

    async def find_products(self, query: str, business_id: uuid.UUID) -> List[Product]:
        return await self.repo.search_by_name(query, business_id)

    async def get_product(self, product_id: uuid.UUID, business_id: uuid.UUID) -> Product:
        product = await self.repo.get_by_id(product_id, business_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID '{product_id}' not found."
            )
        return product