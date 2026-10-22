# FILE: backend/app/services/quota_service.py
from datetime import datetime, timezone
import logging
import uuid
from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.packages import PackageTier, get_tier_config
from app.models.entities import Business, TenantUsage

logger = logging.getLogger("replyflow.quota")


class QuotaEnforcementService:
    """
    Tier Quota Enforcement & Metering Engine.
    Equivalent to an enterprise RateLimiting Guard in NestJS.
    Verifies subscription plan caps before allowing AI processing.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _get_current_billing_month(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m")

    async def get_or_create_usage(self, business_id: uuid.UUID) -> TenantUsage:
        month = self._get_current_billing_month()
        query = select(TenantUsage).where(
            TenantUsage.business_id == business_id,
            TenantUsage.billing_month == month
        )
        res = await self.db.execute(query)
        usage = res.scalar_one_or_none()

        if not usage:
            usage = TenantUsage(
                business_id=business_id,
                billing_month=month,
                responses_used=0,
                comments_used=0,
                customers_serviced=0,
                channel_comment_counts={},
            )
            self.db.add(usage)
            await self.db.flush()

        return usage

    async def verify_can_process(
        self,
        business: Business,
        channel: str,
        is_comment: bool = False
    ) -> Tuple[bool, str]:
        """
        Validates channel authorization and monthly quota limits.
        Returns (True, "OK") or (False, reason_string).
        """
        tier_cfg = get_tier_config(business.plan_tier)
        allowed_channels = tier_cfg["allowed_channels"]

        # 1. Channel Permission Check
        if channel not in allowed_channels:
            msg = (
                f"Channel '{channel}' is not included in the '{tier_cfg['display_name']}' plan. "
                f"Please upgrade to 'Business' or 'Business Premium' to activate {channel}."
            )
            logger.warning(f"[Quota Denied] {business.name}: {msg}")
            return False, msg

        # 2. Consumption Limits Check
        usage = await self.get_or_create_usage(business.id)

        if usage.responses_used >= tier_cfg["monthly_response_limit"]:
            msg = f"Monthly response limit ({tier_cfg['monthly_response_limit']}) reached for {tier_cfg['display_name']} plan."
            logger.warning(f"[Quota Exceeded] {business.name}: {msg}")
            return False, msg

        if is_comment:
            if usage.comments_used >= tier_cfg["monthly_comment_limit"]:
                msg = f"Monthly social comment limit ({tier_cfg['monthly_comment_limit']}) reached for {tier_cfg['display_name']} plan."
                return False, msg

            channel_count = usage.channel_comment_counts.get(channel, 0)
            if channel_count >= tier_cfg["per_channel_comment_cap"]:
                msg = f"Per-channel cap of {tier_cfg['per_channel_comment_cap']} reached on {channel} for {tier_cfg['display_name']} plan."
                return False, msg

        return True, "OK"

    async def record_successful_interaction(
        self,
        business_id: uuid.UUID,
        channel: str,
        is_comment: bool = False
    ):
        """Atomically increments consumption meters."""
        usage = await self.get_or_create_usage(business_id)
        usage.responses_used += 1

        if is_comment:
            usage.comments_used += 1
            counts = dict(usage.channel_comment_counts)
            counts[channel] = counts.get(channel, 0) + 1
            usage.channel_comment_counts = counts

        await self.db.commit()