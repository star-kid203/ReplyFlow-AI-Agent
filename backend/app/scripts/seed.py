# FILE: backend/app/scripts/seed.py
import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.database import AsyncSessionLocal
from app.models.entities import Business, BusinessKnowledge, Product
from sqlalchemy import select


async def seed_camtech():
    async with AsyncSessionLocal() as session:
        # 1. Check if CamTech already exists
        query = select(Business).where(Business.slug == "camtech-electronics")
        result = await session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            print("✓ CamTech Electronics already seeded!")
            return

        print("Seeding CamTech Electronics...")

        # 2. Create Business
        camtech = Business(
            name="CamTech Electronics",
            slug="camtech-electronics",
            description="Premium consumer electronics, smartphones, laptops, and audio gear.",
            communication_style="professional, helpful, and concise",
            is_active=True,
        )
        session.add(camtech)
        await session.flush()  # Populates camtech.id

        # 3. Add Verified Knowledge & Policies
        policies = [
            BusinessKnowledge(
                business_id=camtech.id,
                category="policy",
                title="Return and Refund Policy",
                content=(
                    "Customers are eligible for a full refund within 14 days of delivery if the item "
                    "is unopened, in its original packaging, and has proof of purchase. Opened items "
                    "or refund requests past 14 days require manual manager approval."
                ),
            ),
            BusinessKnowledge(
                business_id=camtech.id,
                category="policy",
                title="Warranty Policy",
                content=(
                    "All brand-new electronic devices come with a 1-year limited manufacturer warranty "
                    "covering hardware defects. Accidental damage or water damage is excluded."
                ),
            ),
            BusinessKnowledge(
                business_id=camtech.id,
                category="shipping",
                title="Shipping and Delivery Times",
                content=(
                    "Standard domestic shipping takes 3-5 business days. Express shipping takes 1-2 business days. "
                    "Orders placed before 2 PM EST ship the same day. Tracking links are emailed immediately upon dispatch."
                ),
            ),
            BusinessKnowledge(
                business_id=camtech.id,
                category="faq",
                title="Store Hours and Support Availability",
                content=(
                    "Our customer support team is available Monday through Friday from 9 AM to 6 PM EST. "
                    "Physical store hours: Monday-Saturday 10 AM to 8 PM EST, Sunday 11 AM to 5 PM EST."
                ),
            ),
        ]
        session.add_all(policies)

        # 4. Add Products Catalog
        products = [
            Product(
                business_id=camtech.id,
                sku="IPHONE-17-BLK",
                name="iPhone 17 (256GB, Black)",
                description="Latest flagship smartphone with A19 chip, 256GB storage, Black finish.",
                price=999.00,
                stock_quantity=15,
                metadata_info={"color": "Black", "storage": "256GB", "brand": "Apple"},
            ),
            Product(
                business_id=camtech.id,
                sku="IPHONE-17-SLV",
                name="iPhone 17 (256GB, Silver)",
                description="Latest flagship smartphone with A19 chip, 256GB storage, Silver finish.",
                price=999.00,
                stock_quantity=0,  # Out of stock to test agent behavior
                metadata_info={"color": "Silver", "storage": "256GB", "brand": "Apple"},
            ),
            Product(
                business_id=camtech.id,
                sku="S24-ULTRA-GRY",
                name="Samsung Galaxy S24 Ultra (512GB, Titanium Gray)",
                description="AI-enhanced smartphone with Snapdragon 8 Gen 3, S-Pen included.",
                price=1199.00,
                stock_quantity=8,
                metadata_info={"color": "Titanium Gray", "storage": "512GB", "brand": "Samsung"},
            ),
            Product(
                business_id=camtech.id,
                sku="MACBOOK-AIR-M3",
                name="MacBook Air 15-inch M3 (16GB RAM, 512GB SSD)",
                description="Ultrathin laptop with Apple M3 silicon, Midnight finish.",
                price=1499.00,
                stock_quantity=5,
                metadata_info={"color": "Midnight", "brand": "Apple"},
            ),
        ]
        session.add_all(products)

        await session.commit()
        print(f"✓ Successfully seeded CamTech Electronics! (ID: {camtech.id})")


if __name__ == "__main__":
    asyncio.run(seed_camtech())