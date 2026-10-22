# FILE: backend/app/services/identity_service.py
import logging
import re
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import ChannelType, Conversation, Customer, Message

logger = logging.getLogger("replyflow.identity")


class CustomerIdentityService:
    """
    Enterprise Identity Resolution & Customer 360 Engine.
    Stitches fragmented customer identities across channels (YouTube, WhatsApp, Instagram, Email)
    into a single persistent customer profile with unified cross-channel memory.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def normalize_phone(phone_raw: Optional[str]) -> Optional[str]:
        if not phone_raw:
            return None
        digits = re.sub(r"[^\d]", "", phone_raw)
        return digits if len(digits) >= 8 else None

    @staticmethod
    def normalize_email(email_raw: Optional[str]) -> Optional[str]:
        if not email_raw:
            return None
        clean = email_raw.strip().lower()
        return clean if "@" in clean and "." in clean else None

    async def resolve_or_stitch_customer(
        self,
        business_id: uuid.UUID,
        external_id: str,
        channel: ChannelType,
        customer_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Customer:
        """
        Resolves customer using Identity Graph heuristics:
        1. Exact match on external_id
        2. Match on verified email (if provided)
        3. Match on normalized phone (if provided)
        4. Stitches records and aliases into Customer 360 profile
        """
        clean_email = self.normalize_email(email)
        clean_phone = self.normalize_phone(phone)

        # 1. Look for existing customer by external_id
        q_ext = select(Customer).where(
            Customer.business_id == business_id,
            Customer.external_id == external_id
        )
        res_ext = await self.db.execute(q_ext)
        existing_cust = res_ext.scalar_one_or_none()

        # 2. Look for matching identity via Email or Phone if available
        matched_cust = None
        if clean_email or clean_phone:
            match_conditions = []
            if clean_email:
                match_conditions.append(Customer.email == clean_email)
            if clean_phone:
                match_conditions.append(Customer.phone == clean_phone)

            q_match = select(Customer).where(
                Customer.business_id == business_id,
                or_(*match_conditions)
            )
            res_match = await self.db.execute(q_match)
            matched_cust = res_match.scalars().first()

        # Case A: Found existing customer and discovered new verified contact details -> Update
        if existing_cust:
            cust = existing_cust
            updated = False

            if clean_email and not cust.email:
                cust.email = clean_email
                updated = True
            if clean_phone and not cust.phone:
                cust.phone = clean_phone
                updated = True
            if customer_name and (not cust.name or cust.name.startswith("@") or cust.name.startswith("User_")):
                cust.name = customer_name
                updated = True

            # Register channel in metadata
            meta = dict(cust.metadata_info or {})
            linked_channels = set(meta.get("linked_channels", []))
            linked_channels.add(channel.value)
            meta["linked_channels"] = list(linked_channels)
            cust.metadata_info = meta

            if updated:
                await self.db.commit()
                await self.db.refresh(cust)

            return cust

        # Case B: New external_id, but matches an existing customer's email/phone -> Stitch!
        if matched_cust:
            cust = matched_cust
            meta = dict(cust.metadata_info or {})
            linked_channels = set(meta.get("linked_channels", []))
            linked_channels.add(channel.value)

            aliases = meta.get("aliases", [])
            if external_id not in aliases:
                aliases.append(external_id)
            meta["aliases"] = aliases
            meta["linked_channels"] = list(linked_channels)
            cust.metadata_info = meta

            logger.info(f"[Identity Resolution] Stitched external ID '{external_id}' ({channel.value}) to existing Customer '{cust.name}' (UUID: {cust.id})")
            await self.db.commit()
            await self.db.refresh(cust)
            return cust

        # Case C: Completely new customer profile
        clean_display_name = customer_name or external_id.replace("@", "").replace("_", " ").title()
        cust = Customer(
            business_id=business_id,
            external_id=external_id,
            name=clean_display_name,
            email=clean_email,
            phone=clean_phone,
            metadata_info={
                "linked_channels": [channel.value],
                "aliases": [external_id],
                "created_via_channel": channel.value,
            }
        )
        self.db.add(cust)
        await self.db.commit()
        await self.db.refresh(cust)
        logger.info(f"[Identity Resolution] Provisioned new Customer 360 profile for '{cust.name}' on {channel.value}")
        return cust

    async def get_cross_channel_history(
        self,
        business_id: uuid.UUID,
        customer_id: uuid.UUID,
        limit: int = 12
    ) -> List[Dict[str, str]]:
        """
        Unified Omnichannel Memory Loader:
        Pulls recent conversation history across ALL conversations and channels for this customer,
        tagging each message with the exact channel source (e.g. [YOUTUBE], [WHATSAPP], [INSTAGRAM]).
        """
        # Find all conversations belonging to this customer for this business
        conv_q = select(Conversation).where(
            Conversation.business_id == business_id,
            Conversation.customer_id == customer_id
        ).options(selectinload(Conversation.messages))

        conv_res = await self.db.execute(conv_q)
        all_convs = conv_res.scalars().all()

        unified_messages = []
        for c in all_convs:
            ch_tag = c.channel.value.upper()
            for m in c.messages:
                sender_type = m.sender.value.lower() if hasattr(m.sender, "value") else str(m.sender).lower()
                unified_messages.append({
                    "timestamp": m.created_at,
                    "sender": sender_type,
                    "channel": ch_tag,
                    "content": m.content,
                })

        # Sort chronologically and take the most recent turns
        unified_messages.sort(key=lambda x: x["timestamp"])
        recent = unified_messages[-limit:]

        formatted_history = []
        for item in recent:
            formatted_history.append({
                "sender": item["sender"],
                "channel": item["channel"],
                "content": f"[{item['channel']}] {item['content']}"
            })

        return formatted_history