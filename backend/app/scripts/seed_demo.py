# FILE: backend/app/scripts/seed_demo.py
import asyncio
from decimal import Decimal
from pathlib import Path
import sys
import uuid

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parents[2]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import delete, select, text
from app.core.database import AsyncSessionLocal
from app.models.entities import (
    Business,
    BusinessKnowledge,
    ChannelType,
    Conversation,
    ConversationStatus,
    Customer,
    Message,
    MessageSender,
    Product,
    BusinessConnector,
    ConnectorType,
    ConnectorStatus,
)

CAMTECH_ID = uuid.UUID("ed722c20-1307-4748-a9b4-ccf5e454fe21")
DOUATECH_ID = uuid.UUID("a5a8688e-e0a8-4d0a-aa4f-8ca851362291")


async def seed():
    print("🌱 Resetting and Seeding Production Demo Data (CamTech & DouaTech)...")
    async with AsyncSessionLocal() as session:
        # 0. Self-heal Postgres Enums
        enum_values = [
            ("messagesender", ["customer", "CUSTOMER", "agent", "AGENT", "human_operator", "HUMAN_OPERATOR"]),
            ("channeltype", ["instagram_comment", "INSTAGRAM_COMMENT", "instagram_dm", "INSTAGRAM_DM", "facebook_comment", "FACEBOOK_COMMENT", "website_chat", "WEBSITE_CHAT", "whatsapp", "WHATSAPP", "linkedin_comment", "LINKEDIN_COMMENT", "youtube_comment", "YOUTUBE_COMMENT"]),
            ("conversationstatus", ["open", "OPEN", "escalated", "ESCALATED", "pending_approval", "PENDING_APPROVAL", "resolved", "RESOLVED"]),
            ("connectortype", ["shopify", "custom_rest_erp", "zetaris_fabric", "whatsapp_cloud", "meta_graph", "linkedin", "youtube_api", "static_local"]),
        ]
        for enum_name, vals in enum_values:
            for val in vals:
                try:
                    await session.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{val}';"))
                    await session.commit()
                except Exception:
                    await session.rollback()

        # =========================================================================
        # 1. SEED CAMTECH ELECTRONICS (Retail & Supply Chain Case Study)
        # =========================================================================
        query = select(Business).where(Business.id == CAMTECH_ID)
        result = await session.execute(query)
        camtech = result.scalar_one_or_none()

        if not camtech:
            camtech = Business(
                id=CAMTECH_ID,
                name="CamTech Electronics",
                slug="camtech-electronics",
                description="Omnichannel consumer electronics retailer and B2B technology distributor with regional hubs in Douala and Yaoundé.",
                communication_style="warm, professional, and helpful",
                agent_display_name="CamTech AI Assistant",
                business_type="retail",
                plan_tier="business",
                subscription_status="active",
                is_active=True
            )
            session.add(camtech)
            await session.flush()
            print(f"✓ Created Business: {camtech.name} (ID: {camtech.id})")
        else:
            camtech.name = "CamTech Electronics"
            camtech.description = "Omnichannel consumer electronics retailer and B2B technology distributor with regional hubs in Douala and Yaoundé."
            camtech.communication_style = "warm, professional, and helpful"
            camtech.agent_display_name = "CamTech AI Assistant"
            camtech.business_type = "retail"
            camtech.plan_tier = "business"
            print(f"✓ Updated Business: {camtech.name} (ID: {camtech.id})")

        # Attach Zetaris Data Fabric Connector to CamTech
        q_conn = select(BusinessConnector).where(
            BusinessConnector.business_id == camtech.id,
            BusinessConnector.connector_type == ConnectorType.ZETARIS_FABRIC
        )
        r_conn = await session.execute(q_conn)
        zet_conn = r_conn.scalar_one_or_none()
        if not zet_conn:
            session.add(BusinessConnector(
                business_id=camtech.id,
                connector_type=ConnectorType.ZETARIS_FABRIC,
                name="Zetaris Multi-Location Virtual Data Fabric",
                base_url="cloud.zetaris.com:10000",
                status=ConnectorStatus.CONNECTED,
                config={
                    "mode": "zero_copy_federation",
                    "silos": ["douala_pos_register", "yaounde_s3_lakehouse", "corporate_crm"],
                    "latency_target_ms": 140
                }
            ))

        # Wipe and Seed Real Products
        await session.execute(delete(Product).where(Product.business_id == camtech.id))
        products_data = [
            {
                "sku": "IPHONE-17-BLK",
                "name": "Apple iPhone 17 (256GB) - Space Black",
                "description": "Latest generation flagship iPhone featuring titanium frame, A19 chip, and ProMotion display.",
                "price": Decimal("999.00"),
                "min_price": Decimal("920.00"),
                "pricing_model": "fixed",
                "stock_quantity": 14,
                "metadata_info": {"color": "Space Black", "storage": "256GB", "brand": "Apple", "category": "smartphone"}
            },
            {
                "sku": "IPHONE-17-SLV",
                "name": "Apple iPhone 17 (256GB) - Silver",
                "description": "Latest generation iPhone in Silver finish with ProMotion display.",
                "price": Decimal("999.00"),
                "min_price": Decimal("920.00"),
                "pricing_model": "fixed",
                "stock_quantity": 0,
                "metadata_info": {"color": "Silver", "storage": "256GB", "brand": "Apple", "category": "smartphone"}
            },
            {
                "sku": "MACBOOK-AIR-M3",
                "name": "MacBook Air 15-inch M3 (16GB RAM, 512GB SSD)",
                "description": "Ultrathin laptop with Apple M3 silicon, Liquid Retina display, and Midnight finish.",
                "price": Decimal("1499.00"),
                "min_price": Decimal("1380.00"),
                "pricing_model": "fixed",
                "stock_quantity": 5,
                "metadata_info": {"color": "Midnight", "brand": "Apple", "category": "laptop"}
            },
            {
                "sku": "S24-ULTRA-GRY",
                "name": "Samsung Galaxy S24 Ultra (512GB) - Titanium Gray",
                "description": "AI-enhanced smartphone with Snapdragon 8 Gen 3, S-Pen included, and 200MP camera system.",
                "price": Decimal("1199.00"),
                "min_price": Decimal("1100.00"),
                "pricing_model": "fixed",
                "stock_quantity": 8,
                "metadata_info": {"color": "Titanium Gray", "brand": "Samsung", "category": "smartphone"}
            },
            {
                "sku": "SONY-WH1000XM5",
                "name": "Sony WH-1000XM5 Wireless Headphones",
                "description": "Industry-leading noise canceling wireless headphones with 30-hour battery life.",
                "price": Decimal("399.99"),
                "min_price": Decimal("350.00"),
                "pricing_model": "fixed",
                "stock_quantity": 8,
                "metadata_info": {"color": "Midnight Blue", "brand": "Sony", "category": "audio"}
            }
        ]

        for p_data in products_data:
            session.add(Product(business_id=camtech.id, **p_data))

        # Wipe and Seed Verified Policies Aligned to Douala & Yaoundé Hubs
        await session.execute(delete(BusinessKnowledge).where(BusinessKnowledge.business_id == camtech.id))
        knowledge_data = [
            {
                "category": "locations",
                "title": "Showroom & Depot Locations",
                "content": "Our flagship retail showroom is located at Boulevard Akwa, Douala (open Monday-Saturday 9 AM - 8 PM, Sunday 11 AM - 5 PM). Our central distribution logistics hub is located at Bastos, Yaoundé. Pickup is available in Douala immediately, with regional dispatch across Cameroon within 24-48 hours."
            },
            {
                "category": "shipping",
                "title": "Delivery & Shipping Logistics",
                "content": "Same-day courier dispatch is available in Douala for orders confirmed before 2 PM. Express regional transit between Douala, Yaoundé, Bafoussam, and Buea takes 24 to 48 hours. Tracking details are sent automatically via SMS and WhatsApp once dispatched."
            },
            {
                "category": "refund",
                "title": "30-Day Guarantee & Return Policy",
                "content": "Devices in original, unopened packaging can be returned within 30 days for a full refund or exchange. Defective hardware carries a 1-year manufacturer replacement warranty. Refunds over $200 require human manager authorization."
            },
            {
                "category": "wholesale",
                "title": "B2B Wholesale Accounts & Net-30 Terms",
                "content": "Corporate clients ordering 5 or more units qualify for volume tier pricing. Verified enterprises can request Net-30 purchase order financing through our corporate credit department."
            }
        ]

        for k_data in knowledge_data:
            session.add(BusinessKnowledge(business_id=camtech.id, is_active=True, **k_data))

        await session.commit()
        print("🎉 Seeding complete! CamTech Electronics is now 100% aligned with the Zetaris Douala/Yaoundé Data Fabric.")


if __name__ == "__main__":
    asyncio.run(seed())