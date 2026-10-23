# FILE: backend/app/integrations/whatsapp_adapter.py
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("replyflow.whatsapp")


class WhatsAppAdapter:
    """
    Meta WhatsApp Cloud API Outbound Engine.
    Publishes live AI replies directly back to customer WhatsApp chats.
    """

    GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

    @classmethod
    async def send_text_message(
        cls,
        phone_number_id: str,
        access_token: str,
        recipient_phone: str,
        message_text: str
    ) -> bool:
        """
        Sends an automated reply via WhatsApp Cloud API.
        Endpoint: https://graph.facebook.com/v19.0/{phone_number_id}/messages
        """
        if not access_token or access_token.startswith("demo_"):
            logger.info(f"[WhatsApp Sandbox] Simulating reply to {recipient_phone}: '{message_text}'")
            return True

        url = f"{cls.GRAPH_API_BASE}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        body: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message_text
            }
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=body, headers=headers)
                if res.status_code in [200, 201]:
                    logger.info(f"[WhatsApp Live] Message delivered to {recipient_phone}")
                    return True
                logger.error(f"[WhatsApp Error] Status {res.status_code}: {res.text}")
                return False
        except Exception as exc:
            logger.error(f"[WhatsApp Dispatch Exception] {exc}")
            return False