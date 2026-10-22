# FILE: backend/app/core/llm/meterless_provider.py
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import httpx

from app.core.config import settings
from app.core.llm.base import BaseLLMProvider

logger = logging.getLogger("replyflow.llm.meterless")

NVIDIA_CHAT_URL = "https://integrate.api.nvidia.com/v1"
PLACEHOLDER_KEYS = {
    "",
    "in-tab",
    "paste here",
    "nvapi-dummy-key",
    "rt-local",
    "not-used",
    "your-meterless-or-nvidia-key",
    "your-meterless-runtime-token",
}


def _clean_secret(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).strip().strip('"').strip("'")
    while text.startswith("="):
        text = text[1:].strip().strip('"').strip("'")
    return text


def _is_usable_key(value: Optional[str]) -> bool:
    key = _clean_secret(value)
    if key.lower() in PLACEHOLDER_KEYS:
        return False
    if key.lower().startswith("your-"):
        return False
    return len(key) >= 8


def _normalize_base_url(raw: Optional[str]) -> str:
    text = _clean_secret(raw)
    if not text:
        return ""
    if "://" not in text:
        text = f"http://{text}"
    parsed = urlparse(text)
    path = parsed.path or ""
    for suffix in (
        "/v1/chat/completions",
        "/v1/models",
        "/healthz",
        "/connect",
    ):
        if path.endswith(suffix):
            path = path[: -len(suffix)]
            break
    if path.endswith("/v1"):
        path = path[: -len("/v1")]
    path = path.rstrip("/")
    rebuilt = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
    return f"{rebuilt.rstrip('/')}/v1"


def _is_local_runtime(base_url: str) -> bool:
    host = (urlparse(base_url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def _extract_message_text(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text") or item.get("content") or "")
        content = "".join(parts)
    if not str(content).strip():
        content = message.get("reasoning_content") or message.get("reasoning") or ""
    text = str(content).strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    return text


class MeterlessNemotronProvider(BaseLLMProvider):
    """
    Meterless Nightshift + NVIDIA Nemotron live provider.
    All agent text and triage JSON come from the model. There is no keyword stub.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.nvidia_model = (
            os.getenv("NEMOTRON_MODEL")
            or getattr(settings, "NEMOTRON_MODEL", "")
            or "nvidia/nemotron-3.5-lightning-30b-a3b"
        )
        self.nightshift_model = os.getenv("METERLESS_MODEL") or "meterless/auto"
        self._endpoints = self._build_endpoints(api_key=api_key, base_url=base_url)
        if not self._endpoints:
            logger.error(
                "[Model Provider] No usable Meterless/NVIDIA credentials. "
                "Set MODEL_API_KEY (nvapi-...) or a Nightshift runtime token."
            )

    def _build_endpoints(self, api_key: Optional[str], base_url: Optional[str]) -> List[Dict[str, str]]:
        nightshift_token = next(
            (
                _clean_secret(candidate)
                for candidate in (
                    os.getenv("METERLESS_RUNTIME_TOKEN"),
                    getattr(settings, "METERLESS_RUNTIME_TOKEN", ""),
                    os.getenv("METERLESS_API_KEY"),
                    getattr(settings, "METERLESS_API_KEY", ""),
                )
                if _is_usable_key(candidate)
            ),
            "",
        )
        nvidia_key = next(
            (
                _clean_secret(candidate)
                for candidate in (
                    api_key,
                    os.getenv("MODEL_API_KEY"),
                    os.getenv("NVIDIA_API_KEY"),
                    getattr(settings, "MODEL_API_KEY", ""),
                    getattr(settings, "NVIDIA_API_KEY", ""),
                )
                if _is_usable_key(candidate)
            ),
            "",
        )

        configured = _normalize_base_url(
            base_url or os.getenv("MODEL_BASE_URL") or getattr(settings, "MODEL_BASE_URL", "")
        )
        nightshift_url = _normalize_base_url(
            os.getenv("METERLESS_BASE_URL") or getattr(settings, "METERLESS_BASE_URL", "") or "http://127.0.0.1:8088/v1"
        )
        nvidia_url = NVIDIA_CHAT_URL

        endpoints: List[Dict[str, str]] = []
        seen = set()

        def add(url: str, key: str, model: str, kind: str) -> None:
            if not url or not key:
                return
            marker = (url, kind)
            if marker in seen:
                return
            seen.add(marker)
            endpoints.append({"url": url, "key": key, "model": model, "kind": kind})

        if nightshift_token:
            add(nightshift_url, nightshift_token, self.nightshift_model, "nightshift")
            if configured and _is_local_runtime(configured):
                add(configured, nightshift_token, self.nightshift_model, "nightshift")

        if nvidia_key:
            if configured and not _is_local_runtime(configured):
                model = self.nvidia_model if "nvidia.com" in configured else self.nightshift_model
                add(configured, nvidia_key, model, "nvidia" if "nvidia.com" in configured else "openai-compat")
            add(nvidia_url, nvidia_key, self.nvidia_model, "nvidia")
            if configured and _is_local_runtime(configured):
                add(configured, nvidia_key, self.nightshift_model, "nightshift")

        return endpoints

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self._endpoints:
            raise RuntimeError(
                "Meterless/NVIDIA provider has no usable API key. "
                "Live model reasoning is required; offline keyword replies are disabled."
            )

        errors: List[str] = []
        for endpoint in self._endpoints:
            try:
                text = await self._complete(
                    endpoint=endpoint,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                    response_format=response_format,
                )
                if text:
                    logger.info(
                        "[Model Provider] Live completion via %s (%s)",
                        endpoint["kind"],
                        endpoint["model"],
                    )
                    return text
                errors.append(f"{endpoint['kind']}: empty completion")
            except Exception as exc:
                errors.append(f"{endpoint['kind']}: {exc}")
                logger.warning("[Model Provider] %s call failed: %s", endpoint["kind"], exc)

        raise RuntimeError(
            "All Meterless/NVIDIA endpoints failed without a live completion. "
            + " | ".join(errors)
        )

    async def _complete(
        self,
        endpoint: Dict[str, str],
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        response_format: Optional[Dict[str, Any]],
    ) -> str:
        want_json = bool(response_format and response_format.get("type") == "json_object")
        body: Dict[str, Any] = {
            "model": endpoint["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": 2048 if want_json else 4096,
            "stream": False,
        }
        # Nemotron 3.5 spends max_tokens on thinking unless this is off.
        body["chat_template_kwargs"] = {"enable_thinking": False}

        attempts: List[Dict[str, Any]] = [body]
        if want_json:
            with_format = dict(body)
            with_format["response_format"] = {"type": "json_object"}
            attempts = [with_format, body]

        timeout = httpx.Timeout(180.0, connect=2.5)
        headers = {
            "Authorization": f"Bearer {endpoint['key']}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "meterless-app": "replyflow-operations",
            "meterless-scope": "user",
        }

        last_error: Optional[Exception] = None
        async with httpx.AsyncClient(timeout=timeout) as client:
            for payload in attempts:
                try:
                    response = await client.post(
                        f"{endpoint['url']}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if response.status_code >= 400:
                        last_error = RuntimeError(
                            f"HTTP {response.status_code}: {response.text[:240]}"
                        )
                        if response.status_code in {400, 422} and "response_format" in payload:
                            continue
                        raise last_error
                    data = response.json()
                    text = _extract_message_text(data)
                    if not text:
                        last_error = RuntimeError("Model returned an empty completion.")
                        continue
                    if want_json:
                        try:
                            return self._coerce_json(text)
                        except json.JSONDecodeError as exc:
                            last_error = exc
                            continue
                    return text
                except httpx.HTTPError as exc:
                    last_error = exc
                    break
        if last_error:
            raise last_error
        raise RuntimeError("Model returned an empty completion.")

    @staticmethod
    def _coerce_json(text: str) -> str:
        cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        json.loads(cleaned)
        return cleaned
