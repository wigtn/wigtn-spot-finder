"""
Business Agent (서버/Waiter) - Main travel assistant agent.
Handles user conversations and travel planning using LangGraph.
"""

import logging
from typing import Any

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from src.config.settings import settings
from src.models.state import AgentState, ConversationStage
from src.services.llm.vllm_client import get_chat_model

# Import tools
from src.tools.naver.place_search import place_search_tools
from src.tools.naver.directions import directions_tools
from src.tools.i18n.translation import translation_tools
from src.tools.travel.itinerary import itinerary_tools

logger = logging.getLogger(__name__)


def get_all_travel_tools() -> list:
    """Get all travel-related tools for the agent."""
    return (
        place_search_tools +
        directions_tools +
        translation_tools +
        itinerary_tools
    )


# System prompts for different conversation stages
SYSTEM_PROMPTS = {
    ConversationStage.INIT: """You are a friendly travel assistant helping foreigners explore Korea.

IMPORTANT CONTEXT:
- Google Maps does NOT work well in Korea. You use Naver Map data instead.
- Always be warm and welcoming to tourists visiting Korea.
- Ask about their travel dates, interests, and any dietary/mobility needs.

RESPONSE GUIDELINES:
- Respond in the user's language (detect from their message)
- Keep responses concise but helpful
- If unsure about their needs, ask clarifying questions
- Mention that you can help with: finding places, directions, building itineraries

Start by greeting them and asking how you can help with their Korea trip!""",

    ConversationStage.INVESTIGATION: """You are a travel assistant helping a foreigner plan their Korea trip.

CURRENT TASK: Understanding the user's travel needs and preferences.

GUIDELINES:
- Ask about specific interests (food, history, nature, shopping, nightlife)
- Understand budget level if not yet known
- Learn about any constraints (dietary, mobility, time)
- Suggest popular areas based on their interests

AVAILABLE TOOLS:
- Use NaverMapSearch to find places matching their interests
- Use PlaceDetails to get more information about specific places

Be proactive in making suggestions based on what you learn!""",

    ConversationStage.PLANNING: """You are a travel assistant creating an itinerary for a foreigner in Korea.

CURRENT TASK: Building an optimized travel itinerary.

USER PREFERENCES:
{preferences}

GUIDELINES:
- Create realistic schedules with travel time between locations
- Consider operating hours of attractions
- Include meal times at appropriate hours
- Suggest transportation methods (subway is usually best in Seoul)
- Provide approximate costs in KRW and USD

AVAILABLE TOOLS:
- Use NaverMapSearch to find places
- Use NaverDirections to get routes between locations
- Use ItineraryOptimizer to optimize visit order

Present the itinerary clearly with times and locations!""",

    ConversationStage.RESOLUTION: """You are a travel assistant finalizing travel plans for a foreigner in Korea.

CURRENT TASK: Confirming and saving the itinerary.

GUIDELINES:
- Summarize the final itinerary clearly
- Ask if they want any modifications
- Offer to save the itinerary for reference
- Provide practical tips for their trip:
  - T-money card for transportation
  - Pocket WiFi recommendation
  - Emergency numbers (police: 112, fire/ambulance: 119)
  - Tourist helpline: 1330

Ask if there's anything else they need help with!""",
}


def get_system_prompt(
    stage: ConversationStage,
    preferences: dict[str, Any] | None = None,
    language: str = "en",
) -> str:
    """Generate system prompt based on conversation stage and context."""
    base_prompt = SYSTEM_PROMPTS.get(stage, SYSTEM_PROMPTS[ConversationStage.INIT])

    if preferences and "{preferences}" in base_prompt:
        pref_text = "\n".join(f"- {k}: {v}" for k, v in preferences.items() if v)
        base_prompt = base_prompt.format(preferences=pref_text or "Not yet collected")

    # Add language instruction
    lang_instruction = f"\n\nIMPORTANT: Respond in {language}. Include Korean names in parentheses when mentioning places."

    return base_prompt + lang_instruction


class BusinessAgent:
    """
    Business Agent for travel assistance.
    Uses LangGraph's create_react_agent with tools.
    """

    def __init__(self, tools: list | None = None, checkpointer: Any | None = None):
        """
        Initialize the Business Agent.

        Args:
            tools: List of LangChain tools for the agent
            checkpointer: LangGraph checkpointer for state persistence
        """
        self.model = get_chat_model()
        self.tools = tools or []
        self.checkpointer = checkpointer or MemorySaver()

        # Create the react agent
        self._agent = None

    @property
    def agent(self):
        """Lazy initialization of the agent graph."""
        if self._agent is None:
            self._agent = create_react_agent(
                model=self.model,
                tools=self.tools,
                checkpointer=self.checkpointer,
            )
        return self._agent

    def get_config(self, thread_id: str) -> dict[str, Any]:
        """Get agent configuration for a specific thread."""
        return {
            "configurable": {
                "thread_id": thread_id,
            }
        }

    async def invoke(
        self,
        message: str,
        thread_id: str,
        state: AgentState | None = None,
    ) -> dict[str, Any]:
        """
        Process a user message and generate response.

        Args:
            message: User's message
            thread_id: Conversation thread ID
            state: Optional existing agent state

        Returns:
            Response dict with 'response' and updated 'state'
        """
        try:
            # Determine conversation stage and get appropriate system prompt
            stage = state.stage if state else ConversationStage.INIT
            preferences = state.travel_preferences.model_dump() if state else None
            language = state.travel_preferences.language if state else settings.default_language

            system_prompt = get_system_prompt(stage, preferences, language)

            # Build input messages
            input_messages = [
                SystemMessage(content=system_prompt),
                {"role": "user", "content": message},
            ]

            # Invoke agent
            config = self.get_config(thread_id)
            result = await self.agent.ainvoke(
                {"messages": input_messages},
                config=config,
            )

            # Extract response
            response_message = result["messages"][-1]
            response_text = response_message.content if hasattr(response_message, "content") else str(response_message)

            return {
                "response": response_text,
                "messages": result["messages"],
                "thread_id": thread_id,
            }

        except Exception as e:
            logger.error(f"Business Agent invocation failed: {e}")
            raise

    async def stream(
        self,
        message: str,
        thread_id: str,
        state: AgentState | None = None,
    ):
        """
        Stream response for SSE endpoint.

        Args:
            message: User's message
            thread_id: Conversation thread ID
            state: Optional existing agent state

        Yields:
            Response chunks
        """
        stage = state.stage if state else ConversationStage.INIT
        preferences = state.travel_preferences.model_dump() if state else None
        language = state.travel_preferences.language if state else settings.default_language

        system_prompt = get_system_prompt(stage, preferences, language)

        input_messages = [
            SystemMessage(content=system_prompt),
            {"role": "user", "content": message},
        ]

        config = self.get_config(thread_id)

        async for event in self.agent.astream_events(
            {"messages": input_messages},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content


def create_business_agent(
    tools: list | None = None,
    checkpointer: Any | None = None,
    include_default_tools: bool = True,
) -> BusinessAgent:
    """
    Factory function to create a Business Agent instance.

    Args:
        tools: Additional tools to include
        checkpointer: LangGraph checkpointer for state persistence
        include_default_tools: Include default travel tools (default: True)

    Returns:
        BusinessAgent instance
    """
    all_tools = []

    if include_default_tools:
        all_tools.extend(get_all_travel_tools())

    if tools:
        all_tools.extend(tools)

    return BusinessAgent(tools=all_tools, checkpointer=checkpointer)
