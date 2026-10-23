# FILE: backend/app/integrations/meta_adapter.py
import logging
from typing import Optional
import httpx

logger = logging.getLogger("replyflow.meta")


class MetaAdapter:
    """
    Meta Graph API Outbound Dispatcher.
    Publishes live AI replies to Instagram Comments, Instagram DMs,
    Facebook Page Comments, and Facebook Messenger.
    """

    GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

    @classmethod
    async def reply_to_instagram_comment(
        cls,
        access_token: str,
        comment_id: str,
        reply_text: str
    ) -> bool:
        if not access_token or access_token.startswith("demo_"):
            logger.info(f"[Meta Sandbox] Simulating Instagram reply to {comment_id}: '{reply_text}'")
            return True

        url = f"{cls.GRAPH_API_BASE}/{comment_id}/replies"
        params = {"message": reply_text, "access_token": access_token}

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(url, params=params)
                if res.status_code in [200, 201]:
                    logger.info(f"[Meta Live] Instagram reply posted to comment {comment_id}")
                    return True
                logger.error(f"[Meta Error] Status {res.status_code}: {res.text}")
                return False
        except Exception as exc:
            logger.error(f"[Meta Dispatch Exception] {exc}")
            return False

    @classmethod
    async def send_instagram_direct_message(
        cls,
        access_token: str,
        recipient_id: str,
        message_text: str
    ) -> bool:
        if not access_token or access_token.startswith("demo_"):
            logger.info(f"[Meta Sandbox] Simulating Instagram DM to {recipient_id}: '{message_text}'")
            return True

        url = f"{cls.GRAPH_API_BASE}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "messaging_type": "RESPONSE",
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                return res.status_code in [200, 201]
        except Exception as exc:
            logger.error(f"[Meta DM Exception] {exc}")
            return False

    @classmethod
    async def reply_to_facebook_comment(
        cls,
        access_token: str,
        comment_id: str,
        reply_text: str
    ) -> bool:
        """Publishes public comment reply on a Facebook Page post."""
        if not access_token or access_token.startswith("demo_"):
            logger.info(f"[Meta Sandbox] Simulating Facebook comment reply to {comment_id}: '{reply_text}'")
            return True

        url = f"{cls.GRAPH_API_BASE}/{comment_id}/comments"
        params = {"message": reply_text, "access_token": access_token}

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(url, params=params)
                return res.status_code in [200, 201]
        except Exception as exc:
            logger.error(f"[Facebook Comment Exception] {exc}")
            return False

    @classmethod
    async def send_facebook_messenger(
        cls,
        access_token: str,
        recipient_id: str,
        message_text: str
    ) -> bool:
        """Sends private Messenger message from a Facebook Page."""
        return await cls.send_instagram_direct_message(access_token, recipient_id, message_text)