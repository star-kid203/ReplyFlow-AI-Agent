# FILE: backend/app/integrations/youtube_adapter.py
import logging
from typing import Optional
import httpx

logger = logging.getLogger("replyflow.youtube")


class YouTubeAdapter:
    """
    Google YouTube Data API v3 Outbound Dispatcher.
    Publishes live replies under Douatech or Client YouTube videos.
    """

    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

    @classmethod
    async def reply_to_youtube_comment(
        cls,
        api_key_or_token: str,
        parent_comment_id: str,
        reply_text: str
    ) -> bool:
        if not api_key_or_token or api_key_or_token.startswith("demo_"):
            logger.info(f"[YouTube Sandbox] Simulating reply to comment {parent_comment_id}: '{reply_text}'")
            return True

        url = f"{cls.YOUTUBE_API_BASE}/comments?part=snippet"
        headers = {
            "Authorization": f"Bearer {api_key_or_token}",
            "Content-Type": "application/json",
        }
        body = {
            "snippet": {
                "parentId": parent_comment_id,
                "textOriginal": reply_text,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json=body, headers=headers)
                if res.status_code in [200, 201]:
                    logger.info(f"[YouTube Live] Comment reply posted to {parent_comment_id}")
                    return True
                logger.error(f"[YouTube Error] Status {res.status_code}: {res.text}")
                return False
        except Exception as exc:
            logger.error(f"[YouTube Dispatch Exception] {exc}")
            return False