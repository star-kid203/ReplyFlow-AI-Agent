# FILE: backend/app/repositories/product_repository.py
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Product
from app.schemas.product import ProductCreate


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: uuid.UUID, business_id: uuid.UUID) -> Optional[Product]:
        query = select(Product).where(
            Product.id == product_id,
            Product.business_id == business_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str, business_id: uuid.UUID) -> Optional[Product]:
        query = select(Product).where(
            Product.sku == sku,
            Product.business_id == business_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_by_name(self, term: str, business_id: uuid.UUID) -> List[Product]:
        query = select(Product).where(
            Product.business_id == business_id,
            Product.name.ilike(f"%{term}%")
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_business(self, business_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[Product]:
        query = select(Product).where(
            Product.business_id == business_id
        ).offset(skip).limit(limit).order_by(Product.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: ProductCreate) -> Product:
        product = Product(
            business_id=data.business_id,
            sku=data.sku,
            name=data.name,
            description=data.description,
            price=data.price,
            stock_quantity=data.stock_quantity,
            metadata_info=data.metadata_info,
        )
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product