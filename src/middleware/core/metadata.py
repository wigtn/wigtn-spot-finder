"""
Turn Metadata Middleware.
Tracks and manages metadata for each conversation turn.
"""

import logging
import time
from datetime import datetime
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.models.state import TurnMetadata
from src.utils.tokens import count_tokens

logger = logging.getLogger(__name__)


class MetadataMiddleware:
    """
    Middleware to track and manage conversation turn metadata.

    Tracks:
    - Turn number
    - Timestamps
    - Token counts
    - Latency
    - User intent classification
    """

    def __init__(self):
        """Initialize the metadata middleware."""
        self._start_time: float | None = None

    def start_turn(self) -> None:
        """Mark the start of a turn for latency tracking."""
        self._start_time = time.time()

    def end_turn(self) -> float:
        """
        Mark the end of a turn and return latency.

        Returns:
            Latency in milliseconds
        """
        if self._start_time is None:
            return 0.0

        latency_ms = (time.time() - self._start_time) * 1000
        self._start_time = None
        return latency_ms

    def update_metadata(
        self,
        current_metadata: TurnMetadata,
        user_message: str,
        assistant_message: str | None = None,
    ) -> TurnMetadata:
        """
        Update turn metadata with new information.

        Args:
            current_metadata: Current metadata state
            user_message: The user's message
            assistant_message: The assistant's response (if available)

        Returns:
            Updated TurnMetadata
        """
        # Increment turn number
        new_turn = current_metadata.turn_number + 1

        # Calculate latency
        latency = self.end_turn()

        # Count tokens
        token_count = count_tokens(user_message)
        if assistant_message:
            token_count += count_tokens(assistant_message)

        # Classify user intent
        intent = self._classify_intent(user_message)

        return TurnMetadata(
            turn_number=new_turn,
            timestamp=datetime.utcnow(),
            user_intent=intent,
            latency_ms=latency if latency > 0 else current_metadata.latency_ms,
            token_count=token_count,
        )

    def _classify_intent(self, message: str) -> str:
        """
        Classify the user's intent from their message.

        Args:
            message: User's message text

        Returns:
            Intent classification string
        """
        message_lower = message.lower()

        # Intent classification based on keywords
        if any(word in message_lower for word in ["hello", "hi", "hey", "안녕", "你好", "こんにちは"]):
            return "greeting"

        if any(word in message_lower for word in ["thank", "thanks", "감사", "谢谢", "ありがとう"]):
            return "thanks"

        if any(word in message_lower for word in ["bye", "goodbye", "see you", "안녕히", "再见", "さようなら"]):
            return "farewell"

        if "?" in message or any(word in message_lower for word in ["what", "where", "when", "how", "why", "which", "can you"]):
            return "question"

        if any(word in message_lower for word in ["find", "search", "look for", "recommend", "suggest"]):
            return "search_request"

        if any(word in message_lower for word in ["direction", "route", "how to get", "way to"]):
            return "directions_request"

        if any(word in message_lower for word in ["itinerary", "schedule", "plan", "day trip"]):
            return "itinerary_request"

        if any(word in message_lower for word in ["save", "remember", "note"]):
            return "save_request"

        if any(word in message_lower for word in ["change", "modify", "update", "instead"]):
            return "modification"

        return "general"

    def extract_entities_from_turn(
        self,
        user_message: str,
        assistant_message: str | None = None,
    ) -> list[str]:
        """
        Extract potential entities from the conversation turn.

        Args:
            user_message: User's message
            assistant_message: Assistant's response

        Returns:
            List of extracted entity strings
        """
        entities = []

        # Combine messages for extraction
        combined = user_message
        if assistant_message:
            combined += " " + assistant_message

        # Simple pattern matching for common entities
        # (Full NER would use a proper model)
        import re

        # Korean place patterns (한글 장소명)
        korean_places = re.findall(r'[가-힣]{2,}(?:궁|사|역|동|구|시|도|산|강|해변|공원|시장|거리)', combined)
        entities.extend([f"place:{p}" for p in korean_places])

        # English place patterns
        english_places = re.findall(
            r'\b(?:Gyeongbokgung|Bukchon|Myeongdong|Hongdae|Gangnam|Itaewon|'
            r'Insadong|Namdaemun|Dongdaemun|N Seoul Tower|Lotte Tower|'
            r'Namsan|Han River|Cheonggyecheon)\b',
            combined,
            re.IGNORECASE,
        )
        entities.extend([f"place:{p}" for p in english_places])

        # Date patterns
        dates = re.findall(
            r'\b(?:\d{1,2}/\d{1,2}|\d{4}-\d{2}-\d{2}|'
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}|'
            r'tomorrow|today|next (?:week|month)|'
            r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*day)\b',
            combined,
            re.IGNORECASE,
        )
        entities.extend([f"date:{d}" for d in dates])

        # Budget patterns
        budgets = re.findall(r'\b(\d{1,3}(?:,\d{3})*)\s*(?:won|krw|원)\b', combined, re.IGNORECASE)
        entities.extend([f"budget:{b}" for b in budgets])

        # Time patterns
        times = re.findall(r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\b', combined)
        entities.extend([f"time:{t}" for t in times])

        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.lower() not in seen:
                seen.add(entity.lower())
                unique_entities.append(entity)

        return unique_entities


def create_metadata_middleware() -> MetadataMiddleware:
    """Factory function for creating metadata middleware."""
    return MetadataMiddleware()
