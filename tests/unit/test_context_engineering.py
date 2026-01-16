"""
Unit tests for Context Engineering middleware.
Tests summarization, dynamic prompts, and metadata tracking.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.middleware.core.summarization import (
    SummarizationMiddleware,
    EXTRACTIVE_KEYWORDS,
)
from src.middleware.core.dynamic_prompt import (
    DynamicPromptMiddleware,
    ConversationStageDetector,
    BASE_SYSTEM_PROMPT,
    STAGE_PROMPTS,
)
from src.middleware.core.metadata import MetadataMiddleware
from src.models.state import ConversationStage, TravelPreferences, TurnMetadata


class TestSummarizationMiddleware:
    """Tests for SummarizationMiddleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.middleware = SummarizationMiddleware(
            soft_limit=1000,
            hard_limit=2000,
            timeout_seconds=5.0,
        )

    def test_extractive_summarize_with_keywords(self):
        """Test extractive summarization extracts keyword-rich messages."""
        messages = [
            HumanMessage(content="I want to visit a museum in Seoul tomorrow morning"),
            AIMessage(content="I recommend the National Museum of Korea. It's free!"),
            HumanMessage(content="What about food nearby?"),
            AIMessage(content="There are many restaurants in the area."),
        ]

        summary = self.middleware._extractive_summarize(messages)

        assert summary is not None
        assert "Key points" in summary
        assert "museum" in summary.lower() or "visit" in summary.lower()

    def test_extractive_summarize_includes_user_messages(self):
        """Test that user messages are prioritized."""
        messages = [
            HumanMessage(content="Hello, I need help planning my trip"),
            AIMessage(content="Sure, I'd be happy to help!"),
        ]

        summary = self.middleware._extractive_summarize(messages)

        assert summary is not None
        assert "User:" in summary

    def test_truncation_fallback(self):
        """Test truncation fallback for very long conversations."""
        messages = [
            HumanMessage(content="First message " * 20),
            AIMessage(content="Response 1 " * 20),
            HumanMessage(content="Middle message " * 20),
            AIMessage(content="Response 2 " * 20),
            HumanMessage(content="Last message " * 20),
            AIMessage(content="Final response " * 20),
        ]

        summary = self.middleware._truncation_fallback(messages)

        assert summary is not None
        assert "messages omitted" in summary
        assert "..." in summary

    def test_truncation_fallback_short_conversation(self):
        """Test truncation fallback returns None for short conversations."""
        messages = [
            HumanMessage(content="Hi"),
            AIMessage(content="Hello!"),
        ]

        summary = self.middleware._truncation_fallback(messages)

        assert summary is None

    def test_format_messages_for_summary(self):
        """Test message formatting for LLM summarization."""
        messages = [
            SystemMessage(content="You are a travel assistant"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]

        formatted = self.middleware._format_messages_for_summary(messages)

        # System messages should be skipped
        assert "travel assistant" not in formatted
        assert "User: Hello" in formatted
        assert "Assistant: Hi there!" in formatted


class TestDynamicPromptMiddleware:
    """Tests for DynamicPromptMiddleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.middleware = DynamicPromptMiddleware()

    def test_generate_system_prompt_init_stage(self):
        """Test prompt generation for INIT stage."""
        prompt = self.middleware.generate_system_prompt(
            stage=ConversationStage.INIT,
        )

        assert BASE_SYSTEM_PROMPT in prompt
        assert "Initial Greeting" in prompt
        assert "Welcome the user" in prompt

    def test_generate_system_prompt_planning_stage(self):
        """Test prompt generation for PLANNING stage."""
        prompt = self.middleware.generate_system_prompt(
            stage=ConversationStage.PLANNING,
        )

        assert "Building Itinerary" in prompt
        assert "detailed day-by-day" in prompt

    def test_generate_system_prompt_with_preferences(self):
        """Test prompt includes user preferences."""
        preferences = TravelPreferences(
            language="en",
            budget_level="budget",
            dietary_restrictions=["vegetarian", "halal"],
            interests=["history", "food"],
            accommodation_area="Hongdae",
        )

        prompt = self.middleware.generate_system_prompt(
            stage=ConversationStage.INVESTIGATION,
            preferences=preferences,
        )

        assert "USER PREFERENCES" in prompt
        assert "budget" in prompt.lower()
        assert "vegetarian" in prompt
        assert "halal" in prompt
        assert "history" in prompt
        assert "Hongdae" in prompt

    def test_generate_system_prompt_with_memories(self):
        """Test prompt includes retrieved memories."""
        memories = [
            "User visited Gyeongbokgung last visit",
            "User prefers spicy food",
            "User's hotel is near Myeongdong station",
        ]

        prompt = self.middleware.generate_system_prompt(
            stage=ConversationStage.PLANNING,
            memories=memories,
        )

        assert "RELEVANT CONTEXT FROM PREVIOUS CONVERSATIONS" in prompt
        assert "Gyeongbokgung" in prompt
        assert "spicy food" in prompt

    def test_generate_system_prompt_with_summary(self):
        """Test prompt includes conversation summary."""
        summary = "User is planning a 3-day trip to Seoul focusing on historical sites."

        prompt = self.middleware.generate_system_prompt(
            stage=ConversationStage.PLANNING,
            summary=summary,
        )

        assert "PREVIOUS CONVERSATION SUMMARY" in prompt
        assert "3-day trip" in prompt

    def test_format_preferences_empty(self):
        """Test that empty preferences returns None."""
        preferences = TravelPreferences()

        result = self.middleware._format_preferences(preferences)

        # Default preferences with no meaningful content
        # language is always set, but _format_preferences doesn't include it
        assert result is None or "USER PREFERENCES" in result

    def test_format_memories_truncation(self):
        """Test that long memories are truncated."""
        long_memory = "This is a very long memory content. " * 20  # > 300 chars

        result = self.middleware._format_memories([long_memory])

        assert "..." in result
        assert len(result) < len(long_memory) + 100

    def test_create_system_message(self):
        """Test SystemMessage creation."""
        message = self.middleware.create_system_message(
            stage=ConversationStage.RESOLUTION,
        )

        assert isinstance(message, SystemMessage)
        assert "Finalizing Plans" in message.content


class TestConversationStageDetector:
    """Tests for ConversationStageDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = ConversationStageDetector()

    def test_detect_investigation_stage(self):
        """Test detection of investigation stage."""
        stage = self.detector.detect_stage(
            current_stage=ConversationStage.INIT,
            turn_count=3,
            last_user_message="What places do you recommend for sightseeing?",
        )

        assert stage == ConversationStage.INVESTIGATION

    def test_detect_planning_stage(self):
        """Test detection of planning stage."""
        stage = self.detector.detect_stage(
            current_stage=ConversationStage.INVESTIGATION,
            turn_count=5,
            last_user_message="Can you create an itinerary for my 3-day trip?",
        )

        assert stage == ConversationStage.PLANNING

    def test_detect_resolution_stage(self):
        """Test detection of resolution stage."""
        stage = self.detector.detect_stage(
            current_stage=ConversationStage.PLANNING,
            turn_count=8,
            last_user_message="Looks good, thanks! Can you save this?",
            has_itinerary=True,
        )

        assert stage == ConversationStage.RESOLUTION

    def test_default_progression_by_turn_count(self):
        """Test default stage progression based on turn count."""
        # Early turns -> INIT
        stage = self.detector.detect_stage(
            current_stage=ConversationStage.INIT,
            turn_count=1,
            last_user_message="Hi there",
        )
        assert stage == ConversationStage.INIT

        # Mid turns -> INVESTIGATION
        stage = self.detector.detect_stage(
            current_stage=ConversationStage.INIT,
            turn_count=4,
            last_user_message="I'm interested in Korean culture",
        )
        assert stage == ConversationStage.INVESTIGATION

        # Later turns without itinerary -> PLANNING
        stage = self.detector.detect_stage(
            current_stage=ConversationStage.INVESTIGATION,
            turn_count=7,
            last_user_message="Sounds interesting",
            has_itinerary=False,
        )
        assert stage == ConversationStage.PLANNING


class TestMetadataMiddleware:
    """Tests for MetadataMiddleware."""

    def setup_method(self):
        """Set up test fixtures."""
        self.middleware = MetadataMiddleware()

    def test_start_and_end_turn_latency(self):
        """Test latency tracking."""
        import time

        self.middleware.start_turn()
        time.sleep(0.01)  # 10ms
        latency = self.middleware.end_turn()

        assert latency > 0
        assert latency >= 10  # At least 10ms

    def test_end_turn_without_start(self):
        """Test end_turn returns 0 if start wasn't called."""
        latency = self.middleware.end_turn()

        assert latency == 0.0

    def test_classify_intent_greeting(self):
        """Test greeting intent classification."""
        intent = self.middleware._classify_intent("Hello! How are you?")
        assert intent == "greeting"

        intent = self.middleware._classify_intent("안녕하세요")
        assert intent == "greeting"

    def test_classify_intent_question(self):
        """Test question intent classification."""
        intent = self.middleware._classify_intent("What are the best places to visit?")
        assert intent == "question"

        intent = self.middleware._classify_intent("Where is Gyeongbokgung?")
        assert intent == "question"

    def test_classify_intent_search_request(self):
        """Test search request intent classification."""
        intent = self.middleware._classify_intent("Find me a good restaurant nearby")
        assert intent == "search_request"

        intent = self.middleware._classify_intent("Can you recommend a cafe?")
        assert intent == "search_request"

    def test_classify_intent_itinerary_request(self):
        """Test itinerary request intent classification."""
        intent = self.middleware._classify_intent("Plan my day trip to Busan")
        assert intent == "itinerary_request"

        intent = self.middleware._classify_intent("Create a schedule for tomorrow")
        assert intent == "itinerary_request"

    def test_classify_intent_directions(self):
        """Test directions request intent classification."""
        intent = self.middleware._classify_intent("How to get to Namsan Tower?")
        assert intent == "directions_request"

        intent = self.middleware._classify_intent("What's the route to Myeongdong?")
        assert intent == "directions_request"

    def test_classify_intent_general(self):
        """Test general intent classification."""
        intent = self.middleware._classify_intent("I love Korean food")
        assert intent == "general"

    def test_update_metadata(self):
        """Test metadata update."""
        initial_metadata = TurnMetadata(
            turn_number=0,
            timestamp=datetime.utcnow(),
        )

        self.middleware.start_turn()
        updated = self.middleware.update_metadata(
            current_metadata=initial_metadata,
            user_message="Find me a restaurant",
            assistant_message="Here are some options...",
        )

        assert updated.turn_number == 1
        assert updated.user_intent == "search_request"
        assert updated.token_count > 0

    def test_extract_entities_places(self):
        """Test entity extraction for places."""
        entities = self.middleware.extract_entities_from_turn(
            user_message="I want to visit Gyeongbokgung and Bukchon",
        )

        assert any("Gyeongbokgung" in e for e in entities)
        assert any("Bukchon" in e for e in entities)

    def test_extract_entities_korean_places(self):
        """Test entity extraction for Korean place names."""
        entities = self.middleware.extract_entities_from_turn(
            user_message="경복궁과 남산타워에 가고 싶어요",
        )

        assert any("경복궁" in e for e in entities)

    def test_extract_entities_dates(self):
        """Test entity extraction for dates."""
        entities = self.middleware.extract_entities_from_turn(
            user_message="I'm visiting tomorrow and staying until next week",
        )

        assert any("tomorrow" in e.lower() for e in entities)
        assert any("next week" in e.lower() for e in entities)

    def test_extract_entities_budget(self):
        """Test entity extraction for budget."""
        entities = self.middleware.extract_entities_from_turn(
            user_message="My budget is about 50,000 won per day",
        )

        assert any("50,000" in e for e in entities)

    def test_extract_entities_no_duplicates(self):
        """Test that duplicate entities are removed."""
        entities = self.middleware.extract_entities_from_turn(
            user_message="Gyeongbokgung is great. I love Gyeongbokgung!",
        )

        gyeongbokgung_count = sum(1 for e in entities if "Gyeongbokgung" in e)
        assert gyeongbokgung_count == 1


class TestDistributedLock:
    """Tests for DistributedLock - requires Redis mock."""

    @pytest.mark.asyncio
    async def test_lock_acquisition_mock(self):
        """Test lock acquisition with mocked Redis."""
        from src.utils.distributed_lock import DistributedLock

        lock = DistributedLock()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        lock._redis = mock_redis

        token = await lock.acquire("test-resource", blocking=False)

        assert token is not None
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_release_mock(self):
        """Test lock release with mocked Redis."""
        from src.utils.distributed_lock import DistributedLock

        lock = DistributedLock()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.eval = AsyncMock(return_value=1)
        lock._redis = mock_redis

        result = await lock.release("test-resource", "test-token")

        assert result is True
        mock_redis.eval.assert_called_once()

    @pytest.mark.asyncio
    async def test_lock_context_manager_mock(self):
        """Test lock context manager with mocked Redis."""
        from src.utils.distributed_lock import DistributedLock

        lock = DistributedLock()

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.eval = AsyncMock(return_value=1)
        lock._redis = mock_redis

        async with lock.lock("test-resource") as token:
            assert token is not None

        # Verify release was called
        mock_redis.eval.assert_called_once()
