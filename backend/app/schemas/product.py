# FILE: backend/app/schemas/product.py
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0, decimal_places=2)
    stock_quantity: int = Field(default=0, ge=0)
    metadata_info: Dict[str, Any] = Field(default_factory=dict)


class ProductCreate(ProductBase):
    business_id: uuid.UUID


class ProductResponse(ProductBase):
    id: uuid.UUID
    business_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)