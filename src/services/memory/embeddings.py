"""
Embedding service for vector representations.
Supports multiple embedding providers with fallback.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx

from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return embedding dimension."""
        pass


class UpstageEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using Upstage Solar Embedding API.
    Uses solar-embedding-1-large model (4096 dimensions).
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize Upstage embedding provider.

        Args:
            api_key: Upstage API key
            model: Embedding model name
        """
        self.api_key = api_key or settings.upstage_api_key
        self.model = model or settings.upstage_embedding_model
        self._dimension = settings.upstage_embedding_dimension  # 4096

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self.api_key:
            raise ValueError("Upstage API key not configured")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                settings.upstage_embedding_url,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()

            # Sort by index to ensure correct order
            embeddings_data = sorted(data["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in embeddings_data]

            # Update dimension based on actual response
            if embeddings:
                self._dimension = len(embeddings[0])

            return embeddings


class VLLMEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using vLLM server.
    Uses OpenAI-compatible API.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ):
        """
        Initialize vLLM embedding provider.

        Args:
            base_url: vLLM server URL
            model: Embedding model name
            api_key: API key (if required)
        """
        self.base_url = (base_url or settings.vllm_base_url).rstrip("/")
        self.model = model or settings.embedding_model
        self.api_key = api_key or settings.vllm_api_key
        self._dimension = 1536  # Default, will be updated on first call

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()

            # Sort by index to ensure correct order
            embeddings_data = sorted(data["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in embeddings_data]

            # Update dimension based on actual response
            if embeddings:
                self._dimension = len(embeddings[0])

            return embeddings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embedding provider using OpenAI API.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
    ):
        """
        Initialize OpenAI embedding provider.

        Args:
            api_key: OpenAI API key
            model: Embedding model name
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model
        self._dimension = 1536 if "small" in model else 3072

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        embeddings = await self.embed_texts([text])
        return embeddings[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.model,
            "input": texts,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            data = response.json()

            embeddings_data = sorted(data["data"], key=lambda x: x["index"])
            embeddings = [item["embedding"] for item in embeddings_data]

            return embeddings


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding using sentence-transformers.
    Falls back to this when external APIs are unavailable.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize HuggingFace embedding provider.

        Args:
            model_name: HuggingFace model name
        """
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # Default for MiniLM

    @property
    def dimension(self) -> int:
        return self._dimension

    def _load_model(self):
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        self._load_model()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        self._load_model()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


class EmbeddingService:
    """
    High-level embedding service with provider fallback.
    """

    def __init__(self, providers: list[EmbeddingProvider] | None = None):
        """
        Initialize embedding service.

        Args:
            providers: List of providers in priority order
        """
        self.providers = providers or self._get_default_providers()
        self._active_provider: EmbeddingProvider | None = None

    def _get_default_providers(self) -> list[EmbeddingProvider]:
        """Get default provider chain based on configuration."""
        providers = []

        # Primary: Upstage if configured and enabled
        if settings.use_upstage and settings.upstage_api_key:
            providers.append(UpstageEmbeddingProvider())

        # Fallback: vLLM if configured
        if settings.vllm_base_url:
            providers.append(VLLMEmbeddingProvider())

        # Fallback: OpenAI if API key available
        if settings.openai_api_key:
            providers.append(OpenAIEmbeddingProvider())

        # Last resort: Local HuggingFace
        providers.append(HuggingFaceEmbeddingProvider())

        return providers

    @property
    def dimension(self) -> int:
        """Get embedding dimension from active provider."""
        if self._active_provider:
            return self._active_provider.dimension
        return self.providers[0].dimension if self.providers else 1536

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embedding with automatic fallback.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return (await self.embed_texts([text]))[0]

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings with automatic fallback.

        Args:
            texts: Texts to embed

        Returns:
            List of embedding vectors
        """
        last_error = None

        for provider in self.providers:
            try:
                embeddings = await provider.embed_texts(texts)
                self._active_provider = provider
                return embeddings
            except Exception as e:
                logger.warning(
                    f"Embedding provider {type(provider).__name__} failed: {e}"
                )
                last_error = e
                continue

        raise RuntimeError(
            f"All embedding providers failed. Last error: {last_error}"
        )

    async def compute_similarity(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        embeddings = await self.embed_texts([text1, text2])

        # Cosine similarity
        import numpy as np

        vec1 = np.array(embeddings[0])
        vec2 = np.array(embeddings[1])

        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

        return float(similarity)


# Global instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
