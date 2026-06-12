"""
DashScope LLM wrapper for Band Agents Hackathon.
Uses compatible-mode endpoint for OpenAI-compatible API.
Uses httpx with explicit per-request timeout for reliable control in threaded Flask.
"""
import os
import json
import logging
import time
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load .env file - use absolute path to project root
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

# Configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.7-plus")


class LLMClient:
    """Unified LLM client for DashScope compatible-mode API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.base_url = (base_url or DASHSCOPE_BASE_URL).rstrip("/")
        self.model = model or LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens

    def chat(
        self,
        messages: list,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """Send chat completion request to DashScope using httpx.

        Uses explicit per-request timeout (600s) to handle long code generation.
        httpx is used instead of requests because requests' timeout is unreliable
        in Flask threaded mode.
        """
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": stream,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        url = f"{self.base_url}/chat/completions"

        try:
            resp = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=httpx.Timeout(timeout=600.0, connect=30.0, read=600.0, write=600.0),
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPError as e:
            logger.error(f"LLM request failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"LLM response parsing failed: {e}")
            raise RuntimeError(f"Invalid response from LLM: {e}")

    def chat_with_retry(self, messages: list, system: str = "", max_retries: int = 3, **kwargs) -> str:
        """Chat with automatic retry on failure."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return self.chat(messages, system=system, **kwargs)
            except Exception as e:
                last_error = e
                if attempt == max_retries - 1:
                    break
                wait = (attempt + 1) * 2
                logger.warning(f"LLM attempt {attempt + 1} failed, retrying in {wait}s... ({e})")
                time.sleep(wait)
        raise RuntimeError(f"All {max_retries} retry attempts exhausted. Last error: {last_error}")


# Global instance
llm = LLMClient()
