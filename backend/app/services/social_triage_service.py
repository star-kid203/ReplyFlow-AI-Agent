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
    """Generates a frictionless 1-click deep-link to transition public viewers into private chat."""
    clean_topic = urllib.parse.quote(
        f"Hi {business.name}! I saw your post regarding {topic} and would like to get more details."
    )
    if wa_number:
        clean_phone = re.sub(r"[^\d]", "", wa_number)
        return f"https://wa.me/{clean_phone}?text={clean_topic}"

    return f"http://localhost:3000/?tenant={business.id}&ref={channel.value}&author={author_handle.replace('@', '')}"


class SocialTriageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def is_syntactic_noise(self, text: str) -> bool:
        """
        True 0-Cost Noise Filter (Zero Hardcoded Keywords):
        Drops pure emojis, friend tag mentions, and single punctuation without wasting tokens.
        Never checks dictionaries or English/French words—pure syntax only.
        """
        cleaned = text.strip()
        if len(cleaned) == 0:
            return True

        # Drop pure user mentions: "@user1 @user2"
        if re.match(r"^(@\w+\s*)+$", cleaned):
            return True

        # Remove all emojis, symbols, and punctuation
        alphanumeric = re.sub(r"[^\w]", "", cleaned, flags=re.UNICODE).strip()

        # If after stripping emojis and punctuation there are 0 or 1 alphanumeric characters, it is pure emoji/symbol spam
        if len(alphanumeric) <= 1:
            return True

        return False

    async def _resolve_business_whatsapp(self, business_id: uuid.UUID) -> str:
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
        try:
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
                "lead": f"Commercial Lead from {post_id}",
                "partnership": f"B2B Partnership Inquiry from {post_id}",
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
                        "expected_resolution": "Follow up directly via private DM / chat.",
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

                ai_dm_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.AGENT,
                    content=tailored_dm_opening,
                    metadata_info={"generated_by": business.dynamic_agent_name, "delivery_channel": "private_dm"},
                    created_at=now_time,
                )
                self.db.add(ai_dm_msg)
            else:
                conv.updated_at = now_time
                if is_urgent_ticket:
                    conv.status = ConversationStatus.ESCALATED

                cust_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.CUSTOMER,
                    content=f"[Public Comment on {channel.value}]: {content}",
                    created_at=now_time,
                )
                self.db.add(cust_msg)

                ai_dm_msg = Message(
                    conversation_id=conv.id,
                    sender=MessageSender.AGENT,
                    content=tailored_dm_opening,
                    metadata_info={"generated_by": business.dynamic_agent_name, "delivery_channel": "private_dm"},
                    created_at=now_time,
                )
                self.db.add(ai_dm_msg)

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
        business_type = (business.business_type or "service").lower()
        business_desc = business.description or "Enterprise operations"

        # 2. Fetch Corporate WhatsApp for 1-Click Deep Links
        corporate_wa = await self._resolve_business_whatsapp(business.id)

        # 3. Fetch Verified Ground Truth Offerings
        p_res = await self.db.execute(select(Product).where(Product.business_id == business.id))
        offerings = [
            f"- {p.name}: {p.description or ''} (${p.price:,.2f})"
            if p.price > 0 else f"- {p.name}: {p.description or 'Custom Scope / Scoped Quote'}"
            for p in p_res.scalars().all()
        ]
        catalog_summary = "\n".join(offerings) if offerings else "No static catalog. Custom solutions provider."

        k_res = await self.db.execute(
            select(BusinessKnowledge).where(BusinessKnowledge.business_id == business.id, BusinessKnowledge.is_active == True)
        )
        policies = [f"- {k.title}: {k.content}" for k in k_res.scalars().all()]
        knowledge_summary = "\n".join(policies) if policies else "Standard professional terms."

        llm = get_llm_provider()
        results: List[ProcessedSocialComment] = []
        skipped_count = 0
        replies_generated_count = 0

        # Extract Daily Reply Cap
        daily_reply_cap = getattr(payload.directive, "daily_reply_cap", 50) or 50
        allowed_intents = set(payload.directive.target_intents or [])

        # Check if user authorized replying to generic praise/hype
        allow_praise = "praise" in allowed_intents or "hype" in allowed_intents

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

        # Semantic Category Authorization Map
        category_intent_map = {
            "praise": {"praise", "hype"},
            "complaint": {"complaint", "support"},
            "in_domain_lead": {"lead", "pricing", "product_inquiry"},
            "criticism": {"criticism", "sarcasm"},
            "partnership": {"partnership", "api", "integration"},
            "out_of_domain": {"lead", "pricing", "product_inquiry"},
        }

        for comment in payload.comments:
            content = comment.content.strip()

            # LEVEL 1: Zero-Cost Syntactic Noise Filter (0 tokens, no dictionaries)
            # Drops pure emojis or pure tags (e.g. "🔥🔥🔥", "@user1 @user2")
            if not allow_praise and self.is_syntactic_noise(content):
                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="skipped_noise",
                        reason="Noise Filter: Pure emoji or mention spam dropped at 0 token cost.",
                        reply_text=None,
                    )
                )
                skipped_count += 1
                continue

            bridge_url = generate_omnichannel_bridge_link(
                business=business,
                channel=payload.channel,
                author_handle=comment.author_handle,
                topic="inquiry",
                wa_number=corporate_wa
            )

            # LEVEL 2: 100% LLM Cognitive Understanding & Domain Reasoning (Zero Keyword Lists)
            system_prompt = f"""You are {agent_name}, the Lead Operations & Social Intelligence Specialist representing '{brand_name}'.
Business Profile: {business_desc} ({business_type.upper()}).
Brand Voice: {payload.directive.creator_persona or business.communication_style}.
Parent Post Caption: "{payload.directive.post_caption}".

VERIFIED OFFERINGS FOR {brand_name.upper()}:
{catalog_summary}

VERIFIED KNOWLEDGE & POLICIES:
{knowledge_summary}

REASONING DIRECTIVE:
Read the commenter's text naturally regardless of language (English, French, slang, typos).
Analyze the commenter's true intent and classify it into EXACTLY one category:
- "praise": Generic celebratory comments, hype, congratulations, or excitement without an actual inquiry (e.g. 'fire release', 'bravo l'équipe', 'awesome drop').
- "complaint": Customer reporting an order delay, broken product, billing dispute, outage, or anger.
- "in_domain_lead": Commercial buying intent, pricing inquiry, or scoping for products/services {brand_name} ACTUALLY provides.
- "out_of_domain": Inquiries for products or services that {brand_name} DOES NOT SELL (e.g. asking a software firm for physical iPhones or retail electronics).
- "partnership": B2B collaboration, API, reseller, or vendor inquiry.
- "criticism": Skepticism, price pushback, sarcasm, or disbelief.

Return a strictly valid JSON object with:
- "category": one of ["praise", "complaint", "in_domain_lead", "out_of_domain", "partnership", "criticism"]
- "reason": concise 1-sentence audit explanation
- "public_reply": 1-2 natural sentences replying directly to the user in their language. If out-of-domain, politely explain what {brand_name} actually does.
- "private_dm": 2-3 sentences opening a tailored private conversation for the inbox, or null.

Return JSON only without markdown formatting."""

            user_prompt = f"Comment by {comment.author_handle}: \"{content}\"\n\nCognitive analysis and output:"

            try:
                raw_json = await llm.generate(
                    system_prompt,
                    user_prompt,
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                clean_json = raw_json.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                data = json.loads(clean_json)
            except Exception as e:
                logger.warning(f"[Social Triage LLM fallback] {e}")
                data = {
                    "category": "criticism",
                    "reason": "General brand engagement.",
                    "public_reply": f"Thanks for connecting {comment.author_handle}! Reach out directly to our team here: {bridge_url}",
                    "private_dm": None
                }

            cat = data.get("category", "criticism")
            public_reply = data.get("public_reply", "")
            private_dm = data.get("private_dm")
            audit_reason = data.get("reason", "Evaluated by multi-tenant operations core.")

            # GOVERNANCE GATE 1: If categorized by the LLM as generic praise and praise replies are disabled
            if cat == "praise" and not allow_praise:
                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="skipped_noise",
                        reason="Noise Filter: Generic hype/praise dropped per campaign directive.",
                        reply_text=None,
                    )
                )
                skipped_count += 1
                continue

            # GOVERNANCE GATE 2: Is this category authorized by the creator?
            required_tags = category_intent_map.get(cat, set())
            category_is_authorized = bool(allowed_intents.intersection(required_tags))

            if not category_is_authorized:
                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="skipped_by_directive",
                        reason=f"Governance Filter: Category '{cat}' is disabled in campaign rules. Reply muted.",
                        reply_text=None,
                    )
                )
                skipped_count += 1
                continue

            # GOVERNANCE GATE 3: Daily reply cap
            if replies_generated_count >= daily_reply_cap:
                results.append(
                    ProcessedSocialComment(
                        comment_id=comment.comment_id,
                        author_handle=comment.author_handle,
                        content=content,
                        action_taken="skipped_cap_exceeded",
                        reason=f"Daily Cap Filter: Reached ceiling of {daily_reply_cap} public replies. Reply suppressed to protect quota.",
                        reply_text=None,
                    )
                )
                skipped_count += 1
                continue

            # Route to private inbox if in-domain lead, complaint, or partnership
            action_taken = "replied_publicly"
            if cat == "complaint":
                action_taken = "sent_private_dm"
                if not private_dm:
                    private_dm = f"Hello {comment.author_handle.replace('@', '')}. We take your feedback seriously. Please share your account reference so our team can resolve this immediately."
                await self._provision_inbox_thread(
                    business=business,
                    author_handle=comment.author_handle,
                    content=content,
                    channel=resolved_channel,
                    post_id=payload.directive.post_id,
                    ticket_type="complaint",
                    tailored_dm_opening=private_dm,
                )
            elif cat == "in_domain_lead":
                action_taken = "sent_private_dm"
                if not private_dm:
                    private_dm = f"Hi {comment.author_handle.replace('@', '')}! Thanks for reaching out regarding your inquiry. Let's discuss your requirements directly."
                await self._provision_inbox_thread(
                    business=business,
                    author_handle=comment.author_handle,
                    content=content,
                    channel=resolved_channel,
                    post_id=payload.directive.post_id,
                    ticket_type="lead",
                    tailored_dm_opening=private_dm,
                )
            elif cat == "partnership":
                action_taken = "partnership_engaged"
                if not private_dm:
                    private_dm = f"Hello {comment.author_handle.replace('@', '')}! Thanks for your partnership inquiry with {brand_name}. Let's schedule a brief sync to explore collaboration."
                await self._provision_inbox_thread(
                    business=business,
                    author_handle=comment.author_handle,
                    content=content,
                    channel=resolved_channel,
                    post_id=payload.directive.post_id,
                    ticket_type="partnership",
                    tailored_dm_opening=private_dm,
                )

            # Attach bridge link for platforms without DMs
            if is_no_dm_platform and bridge_url and bridge_url not in public_reply and cat in ["complaint", "in_domain_lead", "partnership"]:
                public_reply = f"{public_reply} Connect with us directly here: {bridge_url}"

            replies_generated_count += 1

            results.append(
                ProcessedSocialComment(
                    comment_id=comment.comment_id,
                    author_handle=comment.author_handle,
                    content=content,
                    action_taken=action_taken,
                    reason=audit_reason,
                    reply_text=public_reply,
                )
            )

        return BatchSocialIngestResponse(
            total_received=len(payload.comments),
            total_processed=len(payload.comments) - skipped_count,
            total_skipped=skipped_count,
            results=results,
        )