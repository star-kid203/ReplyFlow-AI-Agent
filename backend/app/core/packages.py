# FILE: backend/app/core/packages.py
from enum import Enum
from typing import Any, Dict, List


class PackageTier(str, Enum):
    STARTUP = "startup"
    STELLA = "stella"
    BUSINESS = "business"
    BUSINESS_PREMIUM = "business_premium"


# Comprehensive Tier Definition Matrix
TIER_SPECIFICATIONS: Dict[PackageTier, Dict[str, Any]] = {
    PackageTier.STARTUP: {
        "display_name": "Start Up",
        "monthly_price_usd": 29.00,
        "monthly_response_limit": 1000,
        "monthly_customer_limit": 200,
        "monthly_comment_limit": 500,
        "per_channel_comment_cap": 150,
        "allowed_channels": [
            "website_chat",
            "whatsapp",
        ],
        "features": [
            "Website Live Chat & WhatsApp Integration",
            "Standard Business Brain Grounding",
            "Human-in-the-Loop Escalation",
            "1,000 Automated Responses / Month",
            "Up to 200 Serviced Customers",
        ],
    },
    PackageTier.STELLA: {
        "display_name": "Stella",
        "monthly_price_usd": 79.00,
        "monthly_response_limit": 5000,
        "monthly_customer_limit": 1000,
        "monthly_comment_limit": 2000,
        "per_channel_comment_cap": 1000,
        "allowed_channels": [
            "website_chat",
            "whatsapp",
            "instagram_comment",
            "instagram_dm",
            "facebook_comment",
        ],
        "features": [
            "Meta Suite (Instagram DMs/Comments, FB Page)",
            "Automated Sentiment & Emoji Modulation",
            "5,000 Automated Responses / Month",
            "2,000 Social Comments / Month",
            "Up to 1,000 Serviced Customers",
        ],
    },
    PackageTier.BUSINESS: {
        "display_name": "Business",
        "monthly_price_usd": 199.00,
        "monthly_response_limit": 25000,
        "monthly_customer_limit": 5000,
        "monthly_comment_limit": 10000,
        "per_channel_comment_cap": 5000,
        "allowed_channels": [
            "website_chat",
            "whatsapp",
            "instagram_comment",
            "instagram_dm",
            "facebook_comment",
            "linkedin_comment",
            "linkedin_message",
            "youtube_comment",
        ],
        "features": [
            "LinkedIn Page & Post Comment Automation (Douatech Tier)",
            "YouTube Video Comment Ingestion & Lead Capture",
            "Full Live ERP / POS Workspace Penetration",
            "25,000 Automated Responses / Month",
            "10,000 Social Comments / Month",
            "Continuous Learning Farm & Resolution Audits",
        ],
    },
    PackageTier.BUSINESS_PREMIUM: {
        "display_name": "Business Premium",
        "monthly_price_usd": 499.00,
        "monthly_response_limit": 100000,
        "monthly_customer_limit": 25000,
        "monthly_comment_limit": 50000,
        "per_channel_comment_cap": 50000,
        "allowed_channels": [
            "website_chat",
            "whatsapp",
            "instagram_comment",
            "instagram_dm",
            "facebook_comment",
            "linkedin_comment",
            "linkedin_message",
            "youtube_comment",
            "spotify_qa",
            "tiktok",
        ],
        "features": [
            "All Global Channels (Spotify Podcast Q&A, TikTok, Custom Webhooks)",
            "Zetaris Federated Data Fabric Connectors",
            "100,000 Automated Responses / Month",
            "50,000 Social Comments / Month",
            "24/7 Dedicated Human Operator Escalation Queue",
            "Zero Channel Throttling with SLA Guarantee",
        ],
    },
}


def get_tier_config(tier_str: str) -> Dict[str, Any]:
    try:
        tier_enum = PackageTier(tier_str.lower())
    except ValueError:
        tier_enum = PackageTier.STARTUP
    return TIER_SPECIFICATIONS[tier_enum]