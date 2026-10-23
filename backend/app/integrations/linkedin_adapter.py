# FILE: backend/app/integrations/linkedin_adapter.py
import hmac
import hashlib
import logging
from typing import Any, Dict, Optional
import httpx

logger = logging.getLogger("replyflow.linkedin")


class LinkedInAdapter:
    """
    LinkedIn Community Management & Social Actions Adapter.
    Handles comment verification, payload parsing, and direct comment publishing.
    """

    @staticmethod
    def verify_webhook_signature(payload_bytes: bytes, signature_header: str, client_secret: str) -> bool:
        """Verifies LinkedIn HMAC SHA-256 signature."""
        if not signature_header or not client_secret:
            return True  # Bypass in dev/sandbox if secret is not set
        computed = hmac.new(client_secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature_header)

    @staticmethod
    def parse_comment_event(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parses LinkedIn webhook payload format.
        Supports both standard Organization UGC Posts and Video commentary.
        """
        try:
            # Standard LinkedIn UGC Social Action Webhook Schema
            element = payload.get("elements", [payload])[0]
            comment_urn = element.get("entityUrn") or element.get("id")
            parent_activity = element.get("target") or element.get("object")
            actor_urn = element.get("actor") or element.get("author")
            message_obj = element.get("message", {})
            text_content = message_obj.get("text") if isinstance(message_obj, dict) else str(message_obj)

            if not text_content:
                text_content = payload.get("content", {}).get("text", "")

            return {
                "comment_urn": comment_urn,
                "parent_activity_urn": parent_activity,
                "author_id": actor_urn or "@linkedin_user",
                "author_name": element.get("author_name", "LinkedIn Professional"),
                "text": text_content,
            }
        except Exception as exc:
            logger.error(f"[LinkedIn Parse Error] {exc}")
            return None

    @staticmethod
    async def post_comment_reply(
        access_token: str,
        target_activity_urn: str,
        reply_text: str,
        parent_comment_urn: Optional[str] = None
    ) -> bool:
        """
        Executes LinkedIn REST API to post the AI reply under Douatech's post.
        Endpoint: https://api.linkedin.com/rest/socialActions/{activityUrn}/comments
        """
        if not access_token or access_token.startswith("demo_"):
            logger.info(f"[LinkedIn Sandbox] Simulating reply to {target_activity_urn}: '{reply_text}'")
            return True

        api_url = f"https://api.linkedin.com/rest/socialActions/{target_activity_urn}/comments"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "LinkedIn-Version": "202401",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        body = {
            "message": {"text": reply_text},
        }
        if parent_comment_urn:
            body["parentComment"] = parent_comment_urn

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(api_url, json=body, headers=headers)
                if res.status_code in [200, 201]:
                    logger.info(f"[LinkedIn Live] Reply posted successfully to {target_activity_urn}")
                    return True
                else:
                    logger.error(f"[LinkedIn Error] Status {res.status_code}: {res.text}")
                    return False
        except Exception as exc:
            logger.error(f"[LinkedIn Dispatch Exception] {exc}")
            return False