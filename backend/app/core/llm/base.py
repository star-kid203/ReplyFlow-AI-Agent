# FILE: backend/app/core/llm/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseLLMProvider(ABC):
    """
    Abstract Interface for LLM Providers.
    Decouples ReplyFlow from any single LLM vendor (Groq, OpenAI, Anthropic, etc.).
    """
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        pass
        