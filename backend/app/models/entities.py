# FILE: backend/app/models/entities.py
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.packages import PackageTier


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            val_clean = value.strip().lower()
            for member in cls:
                if member.value.lower() == val_clean or member.name.lower() == val_clean:
                    return member
        return None


# --- ENUMS (With dual-casing support to prevent SQLAlchemy LookupError) ---

class ChannelType(CaseInsensitiveEnum):
    INSTAGRAM_COMMENT = "instagram_comment"
    INSTAGRAM_DM = "instagram_dm"
    FACEBOOK_COMMENT = "facebook_comment"
    WHATSAPP = "whatsapp"
    WEBSITE_CHAT = "website_chat"
    LINKEDIN_MESSAGE = "linkedin_message"
    LINKEDIN_COMMENT = "linkedin_comment"
    YOUTUBE_COMMENT = "youtube_comment"
    SPOTIFY_QA = "spotify_qa"
    TIKTOK = "tiktok"
    EMAIL = "email"

    # Uppercase aliases
    INSTAGRAM_COMMENT_UPPER = "INSTAGRAM_COMMENT"
    INSTAGRAM_DM_UPPER = "INSTAGRAM_DM"
    FACEBOOK_COMMENT_UPPER = "FACEBOOK_COMMENT"
    WHATSAPP_UPPER = "WHATSAPP"
    WEBSITE_CHAT_UPPER = "WEBSITE_CHAT"
    LINKEDIN_MESSAGE_UPPER = "LINKEDIN_MESSAGE"
    LINKEDIN_COMMENT_UPPER = "LINKEDIN_COMMENT"
    YOUTUBE_COMMENT_UPPER = "YOUTUBE_COMMENT"
    SPOTIFY_QA_UPPER = "SPOTIFY_QA"
    TIKTOK_UPPER = "TIKTOK"
    EMAIL_UPPER = "EMAIL"

class MessageSender(CaseInsensitiveEnum):
    CUSTOMER = "customer"
    AGENT = "agent"
    HUMAN_OPERATOR = "human_operator"

    CUSTOMER_UPPER = "CUSTOMER"
    AGENT_UPPER = "AGENT"
    HUMAN_OPERATOR_UPPER = "HUMAN_OPERATOR"


class ConversationStatus(CaseInsensitiveEnum):
    OPEN = "open"
    PENDING_APPROVAL = "pending_approval"
    ESCALATED = "escalated"
    RESOLVED = "resolved"

    OPEN_UPPER = "OPEN"
    PENDING_APPROVAL_UPPER = "PENDING_APPROVAL"
    ESCALATED_UPPER = "ESCALATED"
    RESOLVED_UPPER = "RESOLVED"


class ActionStatus(CaseInsensitiveEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

    PENDING_UPPER = "PENDING"
    APPROVED_UPPER = "APPROVED"
    REJECTED_UPPER = "REJECTED"
    EXECUTED_UPPER = "EXECUTED"
    FAILED_UPPER = "FAILED"


class ConnectorType(CaseInsensitiveEnum):
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    SQUARE_POS = "square_pos"
    CUSTOM_REST_ERP = "custom_rest_erp"
    ZETARIS_FABRIC = "zetaris_fabric"
    LINKEDIN = "linkedin"
    WHATSAPP_CLOUD = "whatsapp_cloud"
    META_GRAPH = "meta_graph"
    YOUTUBE_API = "youtube_api"
    STATIC_LOCAL = "static_local"

    SHOPIFY_UPPER = "SHOPIFY"
    WOOCOMMERCE_UPPER = "WOOCOMMERCE"
    SQUARE_POS_UPPER = "SQUARE_POS"
    CUSTOM_REST_ERP_UPPER = "CUSTOM_REST_ERP"
    ZETARIS_FABRIC_UPPER = "ZETARIS_FABRIC"
    LINKEDIN_UPPER = "LINKEDIN"
    WHATSAPP_CLOUD_UPPER = "WHATSAPP_CLOUD"
    META_GRAPH_UPPER = "META_GRAPH"
    YOUTUBE_API_UPPER = "YOUTUBE_API"
    STATIC_LOCAL_UPPER = "STATIC_LOCAL"


class ConnectorStatus(CaseInsensitiveEnum):
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    DISCONNECTED = "disconnected"

    CONNECTED_UPPER = "CONNECTED"
    SYNCING_UPPER = "SYNCING"
    ERROR_UPPER = "ERROR"
    DISCONNECTED_UPPER = "DISCONNECTED"


# --- MODELS ---

class Business(Base):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    communication_style: Mapped[str] = mapped_column(String(100), default="professional, consultative, and concise")
    agent_display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business_type: Mapped[str] = mapped_column(String(50), default="service", nullable=False)
    plan_tier: Mapped[str] = mapped_column(String(50), default=PackageTier.STARTUP.value, nullable=False)
    subscription_status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    
    enabled_channels: Mapped[list] = mapped_column(
        JSONB,
        default=lambda: ["website_chat", "whatsapp", "linkedin_comment", "youtube_comment"],
        nullable=False
    )
    
    comment_rules: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "filter_noise": True,
            "convert_leads": True,
            "route_sensitive_to_dm": True,
            "target_intents": ["inquiry", "pricing", "lead", "criticism"]
        },
        nullable=False
    )

    @property
    def dynamic_agent_name(self) -> str:
        return self.agent_display_name or f"{self.name} AI"

    # Relationships
    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="business", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="business", cascade="all, delete-orphan")
    knowledge_items: Mapped[List["BusinessKnowledge"]] = relationship("BusinessKnowledge", back_populates="business", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    connectors: Mapped[List["BusinessConnector"]] = relationship("BusinessConnector", back_populates="business", cascade="all, delete-orphan")
    usage_records: Mapped[List["TenantUsage"]] = relationship("TenantUsage", back_populates="business", cascade="all, delete-orphan")
    campaign_directives: Mapped[List["CampaignDirective"]] = relationship("CampaignDirective", back_populates="business", cascade="all, delete-orphan")


class CampaignDirective(Base):
    __tablename__ = "campaign_directives"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    post_id_or_url: Mapped[str] = mapped_column(String(500), nullable=False)
    post_caption: Mapped[str] = mapped_column(Text, nullable=False)
    target_intents: Mapped[list] = mapped_column(JSONB, default=lambda: ["lead", "inquiry", "criticism"], nullable=False)
    ignore_generic_praise: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_reply_cap: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    replies_posted_today: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    follow_up_on_replies: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_thread_depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    persona_override: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="campaign_directives")


class TenantUsage(Base):
    __tablename__ = "tenant_usages"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    billing_month: Mapped[str] = mapped_column(String(7), nullable=False)
    responses_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comments_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    customers_serviced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    channel_comment_counts: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="usage_records")

    __table_args__ = (
        Index("ix_tenant_usage_biz_month", "business_id", "billing_month", unique=True),
    )


class BusinessConnector(Base):
    __tablename__ = "business_connectors"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    connector_type: Mapped[ConnectorType] = mapped_column(
        SQLEnum(ConnectorType, values_callable=lambda x: [e.value for e in x], name="connectortype"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    credentials: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[ConnectorStatus] = mapped_column(
        SQLEnum(ConnectorStatus, values_callable=lambda x: [e.value for e in x], name="connectorstatus"),
        default=ConnectorStatus.CONNECTED,
        nullable=False,
    )
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="connectors")


class Customer(Base):
    __tablename__ = "customers"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="customers")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_customers_business_external_id", "business_id", "external_id", unique=True),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[ChannelType] = mapped_column(
        SQLEnum(ChannelType, values_callable=lambda x: [e.value for e in x], name="channeltype"),
        nullable=False
    )
    status: Mapped[ConversationStatus] = mapped_column(
        SQLEnum(ConversationStatus, values_callable=lambda x: [e.value for e in x], name="conversationstatus"),
        default=ConversationStatus.OPEN,
        nullable=False
    )
    handoff_summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="conversations")
    # Corrected: back_populates points to "conversations" on Customer
    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    actions: Mapped[List["AgentAction"]] = relationship("AgentAction", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    sender: Mapped[MessageSender] = mapped_column(
        SQLEnum(MessageSender, values_callable=lambda x: [e.value for e in x], name="messagesender"),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class BusinessKnowledge(Base):
    __tablename__ = "business_knowledge"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="knowledge_items")


class Product(Base):
    __tablename__ = "products"

    business_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    min_price: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    pricing_model: Mapped[str] = mapped_column(String(50), default="custom_quote", nullable=False)

    stock_quantity: Mapped[int] = mapped_column(Integer, default=99, nullable=False)
    metadata_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    business: Mapped["Business"] = relationship("Business", back_populates="products")

    __table_args__ = (
        Index("ix_products_business_sku", "business_id", "sku", unique=True),
    )


class AgentAction(Base):
    __tablename__ = "agent_actions"

    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        SQLEnum(ActionStatus, values_callable=lambda x: [e.value for e in x], name="actionstatus"),
        default=ActionStatus.PENDING,
        nullable=False
    )
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="actions")