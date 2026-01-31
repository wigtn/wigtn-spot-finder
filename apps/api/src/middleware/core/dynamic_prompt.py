"""
Dynamic Prompt Middleware.
Generates context-aware system prompts based on conversation stage and user preferences.
"""

import logging
from typing import Any

from langchain_core.messages import SystemMessage

from src.config.settings import settings
from src.models.state import ConversationStage, TravelPreferences

logger = logging.getLogger(__name__)


# Base system prompt for the travel assistant
BASE_SYSTEM_PROMPT = """You are a friendly and knowledgeable travel assistant helping foreigners explore Korea.

IMPORTANT CONTEXT:
- Google Maps does NOT work well in Korea. You use Naver Map data instead.
- You help tourists find attractions, restaurants, and plan itineraries.
- You can search for places, get directions, and optimize travel routes.

RESPONSE GUIDELINES:
- Be warm, helpful, and culturally sensitive
- Provide practical tips that tourists need (T-money cards, WiFi, subway tips)
- Include Korean names in parentheses when mentioning places: "Gyeongbokgung Palace (경복궁)"
- Mention approximate costs in both KRW and USD when relevant
- Consider operating hours and travel time between locations"""


# Stage-specific prompt additions
STAGE_PROMPTS = {
    ConversationStage.INIT: """
CURRENT STAGE: Initial Greeting
- Welcome the user warmly
- Ask about their travel dates and interests
- Learn where they're staying (hotel area)
- Discover any dietary restrictions or mobility needs
- Keep the conversation light and friendly""",

    ConversationStage.INVESTIGATION: """
CURRENT STAGE: Understanding Needs
- Ask clarifying questions about their interests
- Suggest popular attractions based on their preferences
- Learn about their daily schedule preferences
- Understand their transportation comfort (walking vs subway vs taxi)
- Search for places that match their criteria""",

    ConversationStage.PLANNING: """
CURRENT STAGE: Building Itinerary
- Create detailed day-by-day schedules
- Include realistic travel times between locations
- Schedule meals at appropriate times (lunch 12-2pm, dinner 6-8pm)
- Consider attraction operating hours
- Optimize the route to minimize travel time
- Provide alternative options for each time slot""",

    ConversationStage.RESOLUTION: """
CURRENT STAGE: Finalizing Plans
- Summarize the complete itinerary clearly
- Ask if any modifications are needed
- Provide emergency contact information:
  * Police: 112
  * Fire/Ambulance: 119
  * Tourist Helpline: 1330 (24/7, English available)
- Remind about T-money card for transportation
- Offer to save the itinerary for reference
- Wish them a wonderful trip!""",
}


# Language-specific greetings and phrases
LANGUAGE_HINTS = {
    "en": {
        "greeting": "Hello! Welcome to Korea!",
        "instruction": "Respond in English.",
    },
    "zh": {
        "greeting": "你好！欢迎来到韩国！",
        "instruction": "Respond in Chinese (Simplified). Include Korean names in parentheses.",
    },
    "ja": {
        "greeting": "こんにちは！韓国へようこそ！",
        "instruction": "Respond in Japanese. Include Korean names in parentheses.",
    },
    "ko": {
        "greeting": "안녕하세요! 한국에 오신 것을 환영합니다!",
        "instruction": "Respond in Korean.",
    },
}


class DynamicPromptMiddleware:
    """
    Middleware to generate dynamic system prompts based on context.

    Considers:
    - Conversation stage (init, investigation, planning, resolution)
    - User's language preference
    - User's travel preferences (budget, dietary, mobility, interests)
    - Retrieved memories from previous conversations
    """

    def __init__(self):
        """Initialize the dynamic prompt middleware."""
        pass

    def generate_system_prompt(
        self,
        stage: ConversationStage,
        preferences: TravelPreferences | None = None,
        memories: list[str] | None = None,
        summary: str | None = None,
    ) -> str:
        """
        Generate a complete system prompt based on context.

        Args:
            stage: Current conversation stage
            preferences: User's travel preferences
            memories: Retrieved memories from vector DB
            summary: Summary of previous conversation

        Returns:
            Complete system prompt string
        """
        parts = [BASE_SYSTEM_PROMPT]

        # Add stage-specific instructions
        if stage in STAGE_PROMPTS:
            parts.append(STAGE_PROMPTS[stage])

        # Add user preferences if available
        if preferences:
            pref_section = self._format_preferences(preferences)
            if pref_section:
                parts.append(pref_section)

        # Add language instruction
        language = preferences.language if preferences else settings.default_language
        lang_hint = LANGUAGE_HINTS.get(language, LANGUAGE_HINTS["en"])
        parts.append(f"\nLANGUAGE: {lang_hint['instruction']}")

        # Add memories if available
        if memories:
            memory_section = self._format_memories(memories)
            parts.append(memory_section)

        # Add summary if available
        if summary:
            parts.append(f"\nPREVIOUS CONVERSATION SUMMARY:\n{summary}")

        return "\n".join(parts)

    def _format_preferences(self, preferences: TravelPreferences) -> str | None:
        """Format user preferences into prompt section."""
        lines = ["\nUSER PREFERENCES:"]
        has_content = False

        if preferences.budget_level:
            lines.append(f"- Budget: {preferences.budget_level}")
            has_content = True

        if preferences.dietary_restrictions:
            restrictions = ", ".join(preferences.dietary_restrictions)
            lines.append(f"- Dietary restrictions: {restrictions}")
            has_content = True

        if preferences.mobility_level and preferences.mobility_level != "full":
            lines.append(f"- Mobility: {preferences.mobility_level}")
            has_content = True

        if preferences.interests:
            interests = ", ".join(preferences.interests)
            lines.append(f"- Interests: {interests}")
            has_content = True

        if preferences.accommodation_area:
            lines.append(f"- Staying at: {preferences.accommodation_area}")
            has_content = True

        if preferences.travel_dates:
            dates = preferences.travel_dates
            if dates.get("start_date") and dates.get("end_date"):
                lines.append(f"- Travel dates: {dates['start_date']} to {dates['end_date']}")
                has_content = True

        return "\n".join(lines) if has_content else None

    def _format_memories(self, memories: list[str]) -> str:
        """Format retrieved memories into prompt section."""
        if not memories:
            return ""

        lines = ["\nRELEVANT CONTEXT FROM PREVIOUS CONVERSATIONS:"]
        for i, memory in enumerate(memories[:5], 1):  # Limit to 5 memories
            # Truncate long memories
            if len(memory) > 300:
                memory = memory[:300] + "..."
            lines.append(f"{i}. {memory}")

        lines.append("(Use this context to provide personalized recommendations)")

        return "\n".join(lines)

    def create_system_message(
        self,
        stage: ConversationStage,
        preferences: TravelPreferences | None = None,
        memories: list[str] | None = None,
        summary: str | None = None,
    ) -> SystemMessage:
        """
        Create a SystemMessage with the generated prompt.

        Args:
            stage: Current conversation stage
            preferences: User's travel preferences
            memories: Retrieved memories
            summary: Conversation summary

        Returns:
            SystemMessage object
        """
        prompt = self.generate_system_prompt(stage, preferences, memories, summary)
        return SystemMessage(content=prompt)


class ConversationStageDetector:
    """
    Detects the appropriate conversation stage based on context.
    """

    def __init__(self):
        """Initialize the stage detector."""
        # Keywords that suggest different stages
        self.investigation_keywords = [
            "recommend", "suggest", "what", "where", "which", "best",
            "good", "popular", "famous", "must-see", "must-visit",
            "interested in", "looking for", "want to",
        ]

        self.planning_keywords = [
            "itinerary", "schedule", "plan", "day", "morning", "afternoon",
            "evening", "route", "order", "optimize", "how long", "how much time",
            "between", "from", "to", "next",
        ]

        self.resolution_keywords = [
            "looks good", "perfect", "thanks", "thank you", "great",
            "save", "done", "finished", "complete", "final",
            "that's all", "nothing else", "goodbye", "bye",
        ]

    def detect_stage(
        self,
        current_stage: ConversationStage,
        turn_count: int,
        last_user_message: str,
        has_itinerary: bool = False,
    ) -> ConversationStage:
        """
        Detect the appropriate conversation stage.

        Args:
            current_stage: Current stage
            turn_count: Number of turns in conversation
            last_user_message: The latest user message
            has_itinerary: Whether an itinerary has been created

        Returns:
            Detected conversation stage
        """
        message_lower = last_user_message.lower()

        # Check for resolution indicators
        if any(kw in message_lower for kw in self.resolution_keywords):
            if has_itinerary or current_stage == ConversationStage.PLANNING:
                return ConversationStage.RESOLUTION

        # Check for planning indicators
        if any(kw in message_lower for kw in self.planning_keywords):
            return ConversationStage.PLANNING

        # Check for investigation indicators
        if any(kw in message_lower for kw in self.investigation_keywords):
            return ConversationStage.INVESTIGATION

        # Default progression based on turn count
        if turn_count <= 2:
            return ConversationStage.INIT
        elif turn_count <= 6:
            return ConversationStage.INVESTIGATION
        elif not has_itinerary:
            return ConversationStage.PLANNING
        else:
            return ConversationStage.RESOLUTION


def create_dynamic_prompt_middleware() -> DynamicPromptMiddleware:
    """Factory function for creating dynamic prompt middleware."""
    return DynamicPromptMiddleware()


def create_stage_detector() -> ConversationStageDetector:
    """Factory function for creating stage detector."""
    return ConversationStageDetector()
