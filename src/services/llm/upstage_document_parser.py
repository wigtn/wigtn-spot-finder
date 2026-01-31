"""
Upstage Document Parser Client.
Extracts text and structure from images (especially Instagram post images).
Uses Upstage Document Digitization API.
"""

import logging
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings

logger = logging.getLogger(__name__)


class DocumentParseResult(BaseModel):
    """Result from document parsing."""

    text: str = Field(description="Extracted text from the document/image")
    elements: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Structured elements extracted from the document"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from parsing"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall parsing confidence score"
    )


class UpstageDocumentParser:
    """
    Client for Upstage Document Digitization API.
    Extracts text and structured data from images.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
    ):
        """
        Initialize the document parser.

        Args:
            api_key: Upstage API key (defaults to settings)
            api_url: Upstage Document API URL (defaults to settings)
            model: Document parser model name (defaults to settings)
        """
        self.api_key = api_key or settings.upstage_api_key
        self.api_url = api_url or settings.upstage_document_url
        self.model = model or settings.upstage_document_model

    def _get_mime_type(self, image_path: Path | str) -> str:
        """Get MIME type from file extension."""
        path = Path(image_path)
        suffix = path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_types.get(suffix, "image/jpeg")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def parse_image(
        self,
        image_path: Path | str,
        output_formats: list[str] | None = None,
    ) -> DocumentParseResult:
        """
        Parse an image and extract text/structure.

        Args:
            image_path: Path to the image file
            output_formats: Output formats (default: ["text", "html"])

        Returns:
            DocumentParseResult with extracted content
        """
        if not self.api_key:
            raise ValueError("Upstage API key not configured")

        output_formats = output_formats or ["text", "html"]
        path = Path(image_path)

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # Prepare multipart form data
        with open(path, "rb") as f:
            files = {
                "document": (path.name, f, self._get_mime_type(path)),
            }
            data = {
                "model": self.model,
                "output_formats": ",".join(output_formats),
            }

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        files=files,
                        data=data,
                    )
                    response.raise_for_status()

                    result = response.json()

                    return DocumentParseResult(
                        text=result.get("text", ""),
                        elements=result.get("elements", []),
                        metadata={
                            "model": result.get("model"),
                            "usage": result.get("usage"),
                        },
                        confidence=result.get("confidence", 0.0),
                    )

            except httpx.HTTPStatusError as e:
                logger.error(f"Document parsing API error: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Document parsing error: {e}")
                raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def parse_image_url(
        self,
        image_url: str,
        output_formats: list[str] | None = None,
    ) -> DocumentParseResult:
        """
        Parse an image from URL and extract text/structure.

        Args:
            image_url: URL of the image
            output_formats: Output formats (default: ["text", "html"])

        Returns:
            DocumentParseResult with extracted content
        """
        if not self.api_key:
            raise ValueError("Upstage API key not configured")

        output_formats = output_formats or ["text", "html"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "document_url": image_url,
            "output_formats": output_formats,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()

                return DocumentParseResult(
                    text=result.get("text", ""),
                    elements=result.get("elements", []),
                    metadata={
                        "model": result.get("model"),
                        "usage": result.get("usage"),
                    },
                    confidence=result.get("confidence", 0.0),
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"Document parsing API error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"Document parsing error: {e}")
            raise

    async def parse_multiple_images(
        self,
        image_paths: list[Path | str],
    ) -> list[DocumentParseResult]:
        """
        Parse multiple images concurrently.

        Args:
            image_paths: List of image paths

        Returns:
            List of DocumentParseResult
        """
        import asyncio

        tasks = [self.parse_image(path) for path in image_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        parsed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to parse image {image_paths[i]}: {result}")
                parsed_results.append(
                    DocumentParseResult(
                        text="",
                        elements=[],
                        metadata={"error": str(result)},
                        confidence=0.0,
                    )
                )
            else:
                parsed_results.append(result)

        return parsed_results


# Global instance
_document_parser: UpstageDocumentParser | None = None


def get_document_parser() -> UpstageDocumentParser:
    """Get global document parser instance."""
    global _document_parser
    if _document_parser is None:
        _document_parser = UpstageDocumentParser()
    return _document_parser
