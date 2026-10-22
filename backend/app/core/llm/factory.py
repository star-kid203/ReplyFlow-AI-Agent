# backend/app/core/llm/factory.py
import os
from app.core.config import settings
from app.core.llm.base import BaseLLMProvider
from app.core.llm.meterless_provider import MeterlessNemotronProvider
from app.core.llm.groq_provider import GroqLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Returns the primary LLM Provider.
    Defaults to Meterless (Nightshift + NVIDIA Nemotron) for hackathon compliance.
    Groq is used only when LLM_PROVIDER is explicitly set to groq.
    """
    provider_type = (settings.LLM_PROVIDER or os.getenv("LLM_PROVIDER") or "meterless").strip().lower()

    if provider_type == "groq" and settings.GROQ_API_KEY:
        return GroqLLMProvider(api_key=settings.GROQ_API_KEY)

    return MeterlessNemotronProvider()