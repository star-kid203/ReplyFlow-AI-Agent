# FILE: backend/app/api/v1/products.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import Product
from app.schemas.product import ProductCreate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products & Catalog Engine"])


class PaginatedProductsResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    total_pages: int


@router.get("", response_model=PaginatedProductsResponse)
async def list_products(
    business_id: uuid.UUID = Query(..., description="Tenant business ID"),
    search: Optional[str] = Query(None, description="Search query across SKU or name"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * limit
    base_query = select(Product).where(Product.business_id == business_id)

    if search:
        search_filter = f"%{search.strip()}%"
        base_query = base_query.where(
            (Product.name.ilike(search_filter)) | (Product.sku.ilike(search_filter))
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    data_query = base_query.order_by(Product.name).offset(offset).limit(limit)
    res = await db.execute(data_query)
    items = list(res.scalars().all())

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return PaginatedProductsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_or_service(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a verified service solution or catalog product for a specific tenant."""
    product = Product(
        business_id=payload.business_id,
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        stock_quantity=payload.stock_quantity,
        metadata_info=payload.metadata_info,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/clear-all", status_code=status.HTTP_200_OK)
async def clear_all_products_for_tenant(
    business_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Wipes all offerings for this tenant, returning their Business Brain to an empty state."""
    query = select(Product).where(Product.business_id == business_id)
    res = await db.execute(query)
    items = res.scalars().all()
    for item in items:
        await db.delete(item)
    await db.commit()
    return {"status": "success", "message": f"Cleared {len(items)} offerings for tenant {business_id}"}


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product_or_service(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a single product or service offering by its ID."""
    query = select(Product).where(Product.id == product_id)
    res = await db.execute(query)
    product = res.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Offering not found")

    await db.delete(product)
    await db.commit()
    return {"status": "success", "message": f"Deleted offering '{product.name}'"}