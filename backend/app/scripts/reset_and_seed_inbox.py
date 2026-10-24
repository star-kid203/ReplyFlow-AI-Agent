# backend/app/scripts/reset_and_seed_inbox.py
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
import sys
import uuid

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import delete, text
from app.core.database import AsyncSessionLocal
from app.models.entities import (
    Business,
    Customer,
    Conversation,
    ConversationStatus,
    ChannelType,
    Message,
    MessageSender,
    AgentAction,
    ActionStatus,
)

CAMTECH_ID = uuid.UUID("ed722c20-1307-4748-a9b4-ccf5e454fe21")
DOUATECH_ID = uuid.UUID("a5a8688e-e0a8-4d0a-aa4f-8ca851362291")


async def reset_and_seed():
    print("🧹 Wiping old contaminated chat histories...")
    async with AsyncSessionLocal() as session:
        # 1. Clean wipe messages, actions, conversations, and customers
        await session.execute(text("TRUNCATE TABLE messages, agent_actions, conversations, customers CASCADE;"))
        await session.commit()
        print("✨ Database messages and threads reset to zero.")

        now = datetime.now(timezone.utc)

        # =====================================================================
        # 2. SEED FRESH SHOWCASE THREADS FOR CAMTECH ELECTRONICS (RETAIL)
        # =====================================================================
        print("📱 Seeding fresh consultative retail threads for CamTech...")

        # --- CamTech Customer 1: Sarah Jones (Instagram DM - iPhone In-Stock Inquiry) ---
        c1 = Customer(
            business_id=CAMTECH_ID,
            external_id="ig_sarah_jones",
            name="Sarah Jones",
            email="sarah.jones@gmail.com",
            phone="+237670112233"
        )
        session.add(c1)
        await session.flush()

        conv1 = Conversation(
            business_id=CAMTECH_ID,
            customer_id=c1.id,
            channel=ChannelType.INSTAGRAM_DM,
            status=ConversationStatus.OPEN
        )
        session.add(conv1)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv1.id,
                sender=MessageSender.CUSTOMER,
                content="Hi! Do you have the iPhone 17 in Space Black available in Douala?",
                created_at=now - timedelta(minutes=45)
            ),
            Message(
                conversation_id=conv1.id,
                sender=MessageSender.AGENT,
                content="Yes, the Apple iPhone 17 (256GB) in Space Black is available for $999.00! We have stock ready for immediate pickup at our flagship showroom on Boulevard Akwa, Douala, or we can arrange same-day courier delivery within the city. Would you like to reserve a unit for pickup today?",
                created_at=now - timedelta(minutes=44),
                metadata_info={"intent": "product_service_inquiry", "grounded": True}
            )
        ])

        # --- CamTech Customer 2: David (Instagram DM - Budget Laptop & Lead Capture) ---
        c2 = Customer(
            business_id=CAMTECH_ID,
            external_id="ig_david_buyer",
            name="David",
            email=None,
            phone=None
        )
        session.add(c2)
        await session.flush()

        conv2 = Conversation(
            business_id=CAMTECH_ID,
            customer_id=c2.id,
            channel=ChannelType.INSTAGRAM_DM,
            status=ConversationStatus.OPEN
        )
        session.add(conv2)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv2.id,
                sender=MessageSender.CUSTOMER,
                content="Do you have any MacBooks under $1,000?",
                created_at=now - timedelta(minutes=25)
            ),
            Message(
                conversation_id=conv2.id,
                sender=MessageSender.AGENT,
                content="Currently, our entry-level Apple laptop in stock is the MacBook Air 15-inch M3 at $1,499.00. We do not have sub-$1,000 MacBooks on the floor right now, but we frequently receive certified configurations and shipments. Would you like me to note your contact details and notify you the moment a budget-friendly option arrives?",
                created_at=now - timedelta(minutes=24),
                metadata_info={"intent": "pricing_budget_inquiry", "grounded": True}
            )
        ])

        # --- CamTech Customer 3: Alain Kamga (WhatsApp - French Mobile Phone Inquiry) ---
        c3 = Customer(
            business_id=CAMTECH_ID,
            external_id="wa_237699887766",
            name="Alain Kamga",
            phone="+237699887766"
        )
        session.add(c3)
        await session.flush()

        conv3 = Conversation(
            business_id=CAMTECH_ID,
            customer_id=c3.id,
            channel=ChannelType.WHATSAPP,
            status=ConversationStatus.OPEN
        )
        session.add(conv3)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv3.id,
                sender=MessageSender.CUSTOMER,
                content="Bonjour, avez-vous le Samsung Galaxy S24 Ultra en stock à Douala ?",
                created_at=now - timedelta(minutes=15)
            ),
            Message(
                conversation_id=conv3.id,
                sender=MessageSender.AGENT,
                content="Bonjour ! Oui, le Samsung Galaxy S24 Ultra (512GB) en Gris Titane est disponible au prix de $1,199.00 pour un retrait immédiat à notre showroom de Douala (Boulevard Akwa) ou expédition régionale. Souhaitez-vous que je vous réserve un exemplaire ?",
                created_at=now - timedelta(minutes=14),
                metadata_info={"intent": "product_service_inquiry", "grounded": True}
            )
        ])

        # =====================================================================
        # 3. SEED FRESH SHOWCASE THREADS FOR DOUATECH SOLUTION (B2B SERVICES)
        # =====================================================================
        print("💼 Seeding B2B consulting threads for DouaTech...")

        # --- DouaTech Customer 1: Dr. Emmanuel Fotso (WhatsApp - Meeting Booked) ---
        c4 = Customer(
            business_id=DOUATECH_ID,
            external_id="wa_237670001122",
            name="Dr. Emmanuel Fotso",
            email="e.fotso@clinique-bonanjo.cm",
            phone="+237670001122"
        )
        session.add(c4)
        await session.flush()

        conv4 = Conversation(
            business_id=DOUATECH_ID,
            customer_id=c4.id,
            channel=ChannelType.WHATSAPP,
            status=ConversationStatus.OPEN
        )
        session.add(conv4)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv4.id,
                sender=MessageSender.CUSTOMER,
                content="Can we schedule a discovery call this Friday at 11:00 AM to scope our clinic telehealth and appointment platform?",
                created_at=now - timedelta(minutes=30)
            ),
            Message(
                conversation_id=conv4.id,
                sender=MessageSender.AGENT,
                content="Great, Dr. Emmanuel Fotso! I have confirmed our discovery session for Friday at 11:00 AM GMT+1 via Google Meet with our Senior Technical Solutions Lead.\n\n🔗 **Meeting Link:** https://meet.google.com/bef-a0f-a6\n\nI have reserved this on our calendar and notified our senior engineering team. Looking forward to reviewing your clinic platform requirements!",
                created_at=now - timedelta(minutes=29),
                metadata_info={"intent": "meeting_scheduling", "grounded": True}
            )
        ])

        # --- DouaTech Customer 2: Real Estate Group Africa (LinkedIn - Active Consulting) ---
        c5 = Customer(
            business_id=DOUATECH_ID,
            external_id="li_realestate_group",
            name="Real Estate Group Africa",
            email="contact@realestate-africa.com"
        )
        session.add(c5)
        await session.flush()

        conv5 = Conversation(
            business_id=DOUATECH_ID,
            customer_id=c5.id,
            channel=ChannelType.LINKEDIN_COMMENT,
            status=ConversationStatus.OPEN
        )
        session.add(conv5)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv5.id,
                sender=MessageSender.CUSTOMER,
                content="We are looking for an engineering partner to build a multi-tenant property listing and client portal platform. What is your development approach?",
                created_at=now - timedelta(minutes=20)
            ),
            Message(
                conversation_id=conv5.id,
                sender=MessageSender.AGENT,
                content="At DouaTech Solution Sarl, we architect custom multi-tenant SaaS platforms tailored for African enterprise workflows. For real estate solutions, we build dedicated listing dashboards, agent access portals, and localized payment integrations through milestone-scoped sprints. Would you like to schedule an initial 20-minute technical discovery call to review your feature roadmap?",
                created_at=now - timedelta(minutes=19),
                metadata_info={"intent": "product_service_inquiry", "grounded": True}
            )
        ])

        # --- DouaTech Customer 3: Dr. Ngassa Clinic (Support & Escalated Ticket) ---
        c6 = Customer(
            business_id=DOUATECH_ID,
            external_id="li_dr_ngassa",
            name="Dr. Ngassa Clinic",
            email="admin@ngassa-clinic.org"
        )
        session.add(c6)
        await session.flush()

        conv6 = Conversation(
            business_id=DOUATECH_ID,
            customer_id=c6.id,
            channel=ChannelType.LINKEDIN_COMMENT,
            status=ConversationStatus.ESCALATED,
            handoff_summary={
                "customer_goal": "Demands senior human review for clinic hospital licensing contract.",
                "ai_actions_taken": "Acknowledged urgent contract scope and opened Ticket #E91F0A.",
                "escalation_blocker": "Customer requested direct executive staff consultation.",
                "recommended_action": "Senior Solutions Director should review contract terms and reach out directly."
            }
        )
        session.add(conv6)
        await session.flush()

        session.add_all([
            Message(
                conversation_id=conv6.id,
                sender=MessageSender.CUSTOMER,
                content="Please have a senior human manager review our enterprise SLA terms immediately.",
                created_at=now - timedelta(minutes=10)
            ),
            Message(
                conversation_id=conv6.id,
                sender=MessageSender.AGENT,
                content="I have transferred your request to our operations management team (Support Ticket #E91F0A). Automated replies on this thread are now paused so our senior director can review your SLA terms and connect with you directly.",
                created_at=now - timedelta(minutes=9),
                metadata_info={"intent": "explicit_human_request", "escalated": True}
            )
        ])

        await session.commit()
        print("🎉 Successfully seeded 6 pristine showcase conversations across CamTech and DouaTech!")


if __name__ == "__main__":
    asyncio.run(reset_and_seed())