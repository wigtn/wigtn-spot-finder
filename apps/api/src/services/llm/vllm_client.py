"""
vLLM Client wrapper using OpenAI-compatible API.
Provides LangChain-compatible LLM interface.
"""

import logging
from functools import lru_cache
from typing import Any

from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings

logger = logging.getLogger(__name__)


class VLLMClient:
    """
    Wrapper for vLLM server using OpenAI-compatible API.
    Used for both main inference and summarization.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model_name: str | None = None,
        api_key: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self.base_url = base_url or settings.vllm_base_url
        self.model_name = model_name or settings.vllm_model_name
        self.api_key = api_key or settings.vllm_api_key
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.max_tokens = max_tokens or settings.llm_max_tokens

        self._client: ChatOpenAI | None = None

    @property
    def client(self) -> ChatOpenAI:
        """Lazy initialization of ChatOpenAI client."""
        if self._client is None:
            self._client = ChatOpenAI(
                base_url=self.base_url,
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                streaming=False,
            )
        return self._client

    def get_streaming_client(self) -> ChatOpenAI:
        """Get a streaming-enabled client for SSE responses."""
        return ChatOpenAI(
            base_url=self.base_url,
            model=self.model_name,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            streaming=True,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def invoke(self, messages: list[dict[str, Any]]) -> str:
        """
        Invoke the LLM with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Generated response text

        Raises:
            Exception: After 3 failed attempts
        """
        try:
            response = await self.client.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"vLLM invocation failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if vLLM server is responsive."""
        try:
            response = await self.client.ainvoke([{"role": "user", "content": "Hi"}])
            return bool(response.content)
        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")
            return False


@lru_cache
def get_vllm_client() -> VLLMClient:
    """Get cached vLLM client instance."""
    return VLLMClient()


def get_chat_model() -> ChatOpenAI:
    """Get ChatOpenAI model for LangGraph agent."""
    return ChatOpenAI(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model_name,
        api_key=settings.vllm_api_key,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )


def get_summarization_model() -> ChatOpenAI:
    """
    Get ChatOpenAI model for summarization.
    Uses same vLLM server but with lower temperature for consistency.
    """
    return ChatOpenAI(
        base_url=settings.vllm_base_url,
        model=settings.vllm_model_name,
        api_key=settings.vllm_api_key,
        temperature=0.3,  # Lower temperature for consistent summaries
        max_tokens=1024,
    )
