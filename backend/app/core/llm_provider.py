# FILE: backend/app/core/llm_provider.py
from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

from app.core.config import settings


class LLMProvider(ABC):
    """
    Abstract LLM Interface.
    Allows hot-swapping Groq with OpenAI, Anthropic, or hackathon partners (e.g. Meterless)
    without touching any LangGraph agent logic.
    """
    @abstractmethod
    def get_model(self, temperature: float = 0.0, model_name: Optional[str] = None) -> BaseChatModel:
        pass


class GroqLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY

    def get_model(self, temperature: float = 0.0, model_name: Optional[str] = None) -> BaseChatModel:
        model = model_name or settings.DEFAULT_LLM_MODEL
        return ChatGroq(
            api_key=self.api_key,
            model_name=model,
            temperature=temperature,
        )


def get_llm_provider() -> LLMProvider:
    """Factory function for LLM provider."""
    return GroqLLMProvider()