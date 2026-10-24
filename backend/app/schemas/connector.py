# // FILE: backend/app/schemas/connector.py

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.connector import ConnectorStatus, ConnectorType


class ConnectorBase(BaseModel):
    connector_type: ConnectorType
    name: str = Field(..., min_length=2, max_length=255)
    base_url: Optional[str] = Field(None, description="API endpoint of the client's live ERP/store")
    config: Dict[str, Any] = Field(
        default_factory=lambda: {"safety_stock_buffer": 2, "cache_ttl_seconds": 60},
        description="Operational rules like safety stock thresholds"
    )
    is_active: bool = True


class ConnectorCreate(ConnectorBase):
    business_id: uuid.UUID
    credentials: Dict[str, Any] = Field(
        default_factory=dict, 
        description="API keys, Storefront tokens, or Basic Auth"
    )


class ConnectorUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[ConnectorStatus] = None
    is_active: Optional[bool] = None


class ConnectorResponse(ConnectorBase):
    id: uuid.UUID
    business_id: uuid.UUID
    status: ConnectorStatus
    last_synced_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LiveInventoryCheckResult(BaseModel):
    sku: str
    in_stock: bool
    available_quantity: int
    source: str  # "shopify_api", "pos_live", "cached_db"
    is_low_stock: bool
    safety_buffer_applied: bool