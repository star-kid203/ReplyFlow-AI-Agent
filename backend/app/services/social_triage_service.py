# FILE: backend/app/services/social_triage_service.py
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional
import urllib.parse
import uuid
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.llm.factory import get_llm_provider
from app.models.entities import (
    Business,
    BusinessConnector,
    BusinessKnowledge,
    ChannelType,
    ConnectorType,
    Conversation,
    ConversationStatus,
    Customer,
    Message,
    MessageSender,
    Product,
)
from app.schemas.social import (
    BatchSocialIngestRequest,
    BatchSocialIngestResponse,
    ProcessedSocialComment,
)

logger = logging.getLogger("replyflow.social_triage")


def generate_omnichannel_bridge_link(
    business: Business,
    channel: ChannelType,
    author_handle: str,
    topic: str,
    wa_number: str = ""
) -> str:
    """
    Generates a frictionless 1-click deep-link to transition public viewers from
    YouTube/public comments into an active private chat with pre-filled context.
    """
    clean_topic = urllib.parse.quote(
        f"Hi {business.name}! I saw your post regarding {topic} and would like to get more details."
    )
    if wa_number:
        clean_phone = re.sub(r"[^\d]", "", wa_number)
        return f"https://wa.me/{clean_phone}?text={clean_topic}"

    return f"http://localhost:3000/?tenant={business.id}&ref={channel.value}&author={author_handle.replace('@', '')}"


class SocialTriageService:
    """
    Enterprise Social Media & Campaign Comment Ingestion Engine.
    Handles 5 operational categories:
    1. Zero-Cost Noise Filter (0 tokens)
    2. Customer Support & Grievances (Escalates & redirects private)
    3. Commercial Sales Leads (Captures & provides 1-click bridge)
    4. Technical & B2B Partnerships (Specs & partnership discovery)
    5. Brand Defense (Witty, grounded response to sarcasm & skepticism)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def is_generic_noise(self, text: str) -> bool:
        """
        Fast Zero-Cost Noise Filter:
        Drops pure emojis, @mentions, and empty praise without wasting LLM tokens.
        """
        cleaned = text.strip().lower()
        if len(cleaned) < 2:
            return True

        if re.match(r"^(@\w+\s*)+$", cleaned):
            return True

        alphanumeric_only = re.sub(r"[^\w\s]", "", cleaned).strip()
        if len(alphanumeric_only) <= 1:
            return True

        praise_words = {
            "love", "nice", "fire", "awesome", "amazing", "great", "cool",
            "so good", "wow", "congrats", "bravo", "first", "top", "good job",
            "love this", "love it", "super", "clap", "beautiful", "clean",
            "so much", "best", "legend", "goat", "great tech company", "great company",
            "tech company", "great tech", "impressive"
        }

        inquiry_triggers = {
            "how", "what", "where", "can", "price", "cost", "dm", "quote",
            "available", "stock", "when", "buy", "start", "build", "hire",
            "need", "deliver", "scam", "late", "refund", "broken", "order", "api", "partner"
        }
        words = set(alphanumeric_only.split())
        if words.intersection(inquiry_triggers):
            return False

        non_fluff_words = [w for w in words if w not in {"the", "a", "an", "this", "is", "so", "very", "tech", "company", "firm"}]
        if non_fluff_words and all(w in praise_words for w in non_fluff_words):
            return True

        for phrase in praise_words:
            if alphanumeric_only == phrase:
                return True

        return False

    def classify_comment_intent(self, text: str) -> Dict[str, bool]:
        t_lower = text.lower().strip()

        complaint_triggers = [
            "delayed", "delay", "not working", "broken", "scam", "lawyer", "police",
            "refund", "invoice", "still waiting", "haven't received", "where is my",
            "bad service", "poor service", "poor quality", "unresponsive", "pending",
            "ticket", "issue", "problem", "cancel", "disappointed", "late delivery",
            "complaint", "order status"
        ]

        lead_triggers = [
            "build", "develop", "looking for an agency", "looking for a firm",
            "looking for someone", "hire", "quote", "how do we start", "how to start",
            "proposal", "contract", "marketplace app", "telehealth", "pricing",
            "cost", "need an agency", "need a team", "consultation", "rates",
            "how much", "can you create", "inquire", "discovery call", "scope",
            "buy", "in stock", "available today", "purchase", "place an order", "where can i buy"
        ]

        criticism_triggers = [
            "yeah right", "marketing hype", "doubt it", "overpriced", "fake",
            "impossible", "not true", "too expensive", "waste of money", "another scam",
            "scam company", "ridiculous", "who buys this", "bad", "garbage"
        ]

        partnership_triggers = [
            "api", "sdk", "partnership", "collaborate", "integrate", "integration",
            "documentation", "github", "tech stack", "vendor", "partner", "b2b partnership",
            "resell", "agency collaboration", "white label"
        ]

        return {
            "is_complaint": any(trigger in t_lower for trigger in complaint_triggers),
            "is_lead": any(trigger in t_lower for trigger in lead_triggers),
            "is_criticism": any(trigger in t_lower for trigger in criticism_triggers),
            "is_partnership": any(trigger in t_lower for trigger in partnership_triggers),
        }

    async def _resolve_business_whatsapp(self, business_id: uuid.UUID) -> str:
        """Fetches configured corporate WhatsApp number for generating deep-links."""
        query = select(BusinessConnector).where(
            BusinessConnector.business_id == business_id,
            BusinessConnector.connector_type == ConnectorType.WHATSAPP_CLOUD,
            BusinessConnector.is_active.is_(True)
        )
        res = await self.db.execute(query)
        conn = res.scalar_one_or_none()
        if conn and conn.config:
            return conn.config.get("phone_number", "")
        return ""

    async def _provision_inbox_thread(
        self,
        business: Business,
        author_handle: str,
        content: str,
        channel: ChannelType,
        post_id: str,
        ticket_type: str,
        tailored_dm_opening: str
    ):
        """
        Thread Continuity Engine: Reuses the latest active conversation for that customer
        without throwing MultipleResultsFound, updates its timestamp, and appends the tailored AI outreach.
        """
        try:
            # 1. Resolve or Create Customer
            c_query = select(Customer).where(
                Customer.business_id == business.id,
                Customer.external_id == author_handle
            )
            c_res = await self.db.execute(c_query)
            cust = c_res.scalar_one_or_none()

            clean_name = author_handle.replace("@", "").replace("_", " ").title()
            if not cust:
                cust = Customer(
                    business_id=business.id,
                    external_id=author_handle,
                    name=clean_name
                )
                self.db.add(cust)
                await self.db.flush()

            # 2. Safely find the MOST RECENT active conversation
            conv_q = (
                select(Conversation)
                .where(
                    Conversation.business_id == business.id,
                    Conversation.customer_id == cust.id,
                    Conversation.channel == channel,
                    Conversation.status.in_([
                        ConversationStatus.OPEN,
                        ConversationStatus.ESCALATED,
                        ConversationStatus.PENDING_APPROVAL,
                    ])
                )
                .order_by(desc(Conversation.updated_at))
                .limit(1)
            )
            conv_res = await self.db.execute(conv_q)
            conv = conv_res.scalars().first()

            is_urgent_ticket = (ticket_type == "complaint")
            status = ConversationStatus.ESCALATED if is_urgent_ticket else ConversationStatus.OPEN
            now_time = datetime.now(timezone.utc)

            ticket_label = {
                "complaint": "Public Support Complaint / Escalation",
                "lead": f"High-Intent Commercial Lead from {post_id}",
                "partnership": f"B2B Partnership / Integration Inquiry from {post_id}",
            }.get(ticket_type, "Social Inquiry")

            if not conv:
                conv = Conversation(
                    business_id=business.id,
                    customer_id=cust.id,
                    channel=channel,
                    status=status,
                    created_at=now_time,
                    updated_at=now_time,
                    handoff_summary={
                        "problem": ticket_label,
                        "expected_resolution": "Review customer case and follow up directly via private DM / chat.",
                        "lead_source": post_id,
                        "initial_comment": content,
                        "ticket_status": "open_pending_human" if is_urgent_ticket else "lead_engaged"
                    }
                )
                self.db.add(conv)
                await self.db.flush()

                cust_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.CUSTOMER,
                    content=f"[Public Comment on {channel.value}]: {content}",
                    created_at=now_time,
                )
                self.db.add(cust_msg)

                ai_agent_name = business.dynamic_agent_name
                ai_dm_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.AGENT,
                    content=tailored_dm_opening,
                    metadata_info={"generated_by": ai_agent_name, "delivery_channel": "private_dm"},
                    created_at=now_time,
                )
                self.db.add(ai_dm_msg)
                logger.info(f"[Triage Engine] Created fresh private thread #{conv.id} for {author_handle}")
            else:
                conv.updated_at = now_time
                if is_urgent_ticket:
                    conv.status = ConversationStatus.ESCALATED
                else:
                    conv.status = ConversationStatus.OPEN

                cust_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.CUSTOMER,
                    content=f"[Public Comment on {channel.value}]: {content}",
                    created_at=now_time,
                )
                self.db.add(cust_msg)

                ai_agent_name = business.dynamic_agent_name
                ai_dm_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.AGENT,
                    content=tailored_dm_opening,
                    metadata_info={"generated_by": ai_agent_name, "delivery_channel": "private_dm"},
                    created_at=now_time,
                )
                self.db.add(ai_dm_msg)
                logger.info(f"[Triage Engine] Updated existing private thread #{conv.id} for {author_handle}")

            await self.db.commit()
        except Exception as db_err:
            logger.error(f"[Triage Provisioning Error] {db_err}", exc_info=True)
            await self.db.rollback()

    async def process_batch(self, payload: BatchSocialIngestRequest) -> BatchSocialIngestResponse:
        # 1. Fetch Tenant Organization
        b_res = await self.db.execute(select(Business).where(Business.id == payload.business_id))
        business = b_res.scalar_one_or_none()
        if not business:
            raise ValueError(f"Tenant organization {payload.business_id} not found.")

        agent_name = business.dynamic_agent_name
        brand_name = business.name
        business_type = business.business_type or "service"

        # 2. Fetch Corporate WhatsApp for 1-Click Deep Links
        corporate_wa = await self._resolve_business_whatsapp(business.id)

        # 3. Fetch Verified Ground Truth Offerings
        p_res = await self.db.execute(select(Product).where(Product.business_id == business.id))
        offerings = [
            {
                "name": p.name,
                "description": p.description,
                "price": f"${p.price}" if p.price > 0 else "Custom Scope / Scoped Quote",
                "in_stock": p.stock_quantity > 0,
                "stock_quantity": p.stock_quantity,
            }
            for p in p_res.scalars().all()
        ]

        llm = get_llm_provider()
        results: List[ProcessedSocialComment] = []
        skipped_count = 0

        # Channel resolution for private handoff inbox
        ch_val = payload.channel.value.lower()
        if "instagram" in ch_val:
            resolved_channel = ChannelType.INSTAGRAM_DM
        elif "linkedin" in ch_val:
            resolved_channel = ChannelType.LINKEDIN_MESSAGE
        elif "youtube" in ch_val:
            resolved_channel = ChannelType.YOUTUBE_COMMENT
        else:
            resolved_channel = ChannelType.WEBSITE_CHAT

        is_no_dm_platform = payload.channel in [ChannelType.YOUTUBE_COMMENT, ChannelType.FACEBOOK_COMMENT]

        for comment in payload.comments:
            content = comment.content.strip()

            # CATEGORY 1: Zero-Cost Spam & Emoji Filter (Saves 80% tokens)
            if payload.directive.ignore_generic_praise and self.is_generic_noise(content):
                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="skipped_noise",
                        reason="Noise Filter: Pure emoji or generic praise dropped (0 tokens wasted).",
                        reply_text=None,
                    )
                )
                skipped_count += 1
                continue

            intent_info = self.classify_comment_intent(content)
            is_complaint = intent_info["is_complaint"]
            is_lead = intent_info["is_lead"]
            is_criticism = intent_info["is_criticism"]
            is_partnership = intent_info["is_partnership"]

            # CATEGORY 2: Customer Support Grievance / Dispute
            if is_complaint:
                tailored_dm = (
                    f"Hello {comment.author_handle.replace('@', '')}. We saw your comment regarding: \"{content[:80]}...\". "
                    "Your case has been escalated with high priority. Please share your registered email, contract reference, or invoice number "
                    "so our senior support team can resolve this for you directly."
                )

                await self._provision_inbox_thread(
                    business=business,
                    author_handle=comment.author_handle,
                    content=content,
                    channel=resolved_channel,
                    post_id=payload.directive.post_id,
                    ticket_type="complaint",
                    tailored_dm_opening=tailored_dm,
                )

                if is_no_dm_platform:
                    bridge_url = generate_omnichannel_bridge_link(
                        business=business,
                        channel=payload.channel,
                        author_handle=comment.author_handle,
                        topic="support escalation",
                        wa_number=corporate_wa
                    )
                    public_reply = (
                        f"Hi {comment.author_handle}! We take this very seriously. "
                        f"To review your account and resolve this securely, please connect directly with our support desk here: {bridge_url}"
                    )
                else:
                    public_reply = (
                        f"Hi {comment.author_handle}! We take this very seriously and want to review your case directly. "
                        f"To protect your privacy, please send us a quick direct message (DM) with your reference or email, "
                        f"and our senior support team will prioritize this right away."
                    )

                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="sent_private_dm",
                        reason="Customer Support De-escalation: Public complaint acknowledged and redirected to private channels for privacy.",
                        reply_text=public_reply,
                    )
                )
                continue

            # CATEGORY 3: High-Intent Commercial Sales Lead
            if is_lead and any(intent in payload.directive.target_intents for intent in ["lead", "pricing", "product_inquiry"]):
                tailored_dm = (
                    f"Hi {comment.author_handle.replace('@', '')}! Thanks for reaching out regarding your inquiry: \"{content}\".\n\n"
                    f"At {brand_name}, we specialize in building scalable solutions tailored to these exact requirements. "
                    "Could you share a brief overview of your target timeline and key deliverables so we can prepare an initial discovery outline for you?"
                )

                await self._provision_inbox_thread(
                    business=business,
                    author_handle=comment.author_handle,
                    content=content,
                    channel=resolved_channel,
                    post_id=payload.directive.post_id,
                    ticket_type="lead",
                    tailored_dm_opening=tailored_dm,
                )

                if is_no_dm_platform:
                    bridge_url = generate_omnichannel_bridge_link(
                        business=business,
                        channel=payload.channel,
                        author_handle=comment.author_handle,
                        topic="project scoping & pricing",
                        wa_number=corporate_wa
                    )
                    public_reply = (
                        f"Great connecting with you {comment.author_handle}! We specialize in custom solutions for this. "
                        f"To scope your requirements and outline a tailored proposal, jump straight into our chat here: {bridge_url}"
                    )
                else:
                    public_reply = (
                        f"Great connecting with you {comment.author_handle}! We specialize in exactly this. "
                        f"We'd love to scope your requirements—please send us a direct message (or check your DMs) "
                        f"so we can share our technical specs and schedule a discovery discussion."
                    )

                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="sent_private_dm",
                        reason="Sales Conversion: High-intent prospect captured and provisioned in Live Inbox with tailored private outreach.",
                        reply_text=public_reply,
                    )
                )
                continue

            # CATEGORY 4: Technical & B2B Partnership Inquiries
            if is_partnership:
                bridge_url = generate_omnichannel_bridge_link(
                    business=business,
                    channel=payload.channel,
                    author_handle=comment.author_handle,
                    topic="technical API & B2B partnership",
                    wa_number=corporate_wa
                )

                tailored_dm = (
                    f"Hello {comment.author_handle.replace('@', '')}! Thanks for reaching out regarding partnerships & technical integration with {brand_name}.\n\n"
                    "Our engineering team supports custom API architectures, enterprise integrations, and agency collaborations. "
                    "Let's schedule a brief technical sync to explore how our teams can work together."
                )

                await self._provision_inbox_thread(
                    business=business,
                    author_handle=comment.author_handle,
                    content=content,
                    channel=resolved_channel,
                    post_id=payload.directive.post_id,
                    ticket_type="partnership",
                    tailored_dm_opening=tailored_dm,
                )

                public_reply = (
                    f"Hello {comment.author_handle}! We actively collaborate on enterprise integrations and technical partnerships. "
                    f"You can review our technical documentation and connect directly with our partnership engineering team here: {bridge_url}"
                )

                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="partnership_engaged",
                        reason="B2B Partnership: Technical collaboration inquiry captured and routed to engineering discovery.",
                        reply_text=public_reply,
                    )
                )
                continue

            # CATEGORY 5: Brand Sarcasm, Skepticism & General Public Engagement
            if business_type == "retail":
                model_instructions = (
                    "RETAIL OPERATIONS:\n"
                    "- State stock availability and exact prices from verified catalog.\n"
                    "- If asked about out-of-stock items, politely let them know and offer in-stock alternatives."
                )
            else:
                model_instructions = (
                    "B2B & PROFESSIONAL SERVICES:\n"
                    "- Explain deliverables and invite them to schedule a discovery scoping call for custom quotes."
                )

            system_prompt = (
                f"You are {agent_name}, responding publicly on behalf of '{brand_name}'.\n"
                f"Brand Voice: {payload.directive.creator_persona or business.communication_style}.\n"
                f"Post Caption: \"{payload.directive.post_caption}\".\n\n"
                "STRICT GROUNDING RULES:\n"
                f"1. You represent ONLY '{brand_name}'. Never confuse this brand with any other organization.\n"
                f"{model_instructions}\n"
                "3. If the comment is skeptical, sarcastic, or critical: respond with wit, polite pride, and confidence grounded in facts.\n"
                "4. Keep the reply short (1 to 2 sentences max) suitable for public social media comments."
            )

            context_str = f"VERIFIED OFFERINGS FOR {brand_name.upper()}:\n{json.dumps(offerings, indent=2)}"
            user_prompt = f"{context_str}\n\nComment by {comment.author_handle}: \"{content}\"\nYour public reply:"

            try:
                reply = await llm.generate(system_prompt, user_prompt, temperature=0.3)
                action = "replied_publicly"
                reason = "Brand Engagement: Addressed public inquiry/criticism with verified facts and brand confidence."
            except Exception as exc:
                reply = f"Thanks for connecting, {comment.author_handle}! Feel free to send us a direct message and our team will assist you."
                action = "replied_publicly"
                reason = "Standard brand engagement."

            results.append(
                ProcessedSocialComment(
                    comment_id=comment.comment_id,
                    author_handle=comment.author_handle,
                    content=content,
                    action_taken=action,
                    reason=reason,
                    reply_text=reply,
                )
            )

        return BatchSocialIngestResponse(
            total_received=len(payload.comments),
            total_processed=len(payload.comments) - skipped_count,
            total_skipped=skipped_count,
            results=results,
        )