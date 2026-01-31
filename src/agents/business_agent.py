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
from src.services.llm.upstage_client import get_chat_model

# Import tools
from src.tools.naver.place_search import place_search_tools
from src.tools.naver.directions import directions_tools
from src.tools.i18n.translation import translation_tools
from src.tools.travel.itinerary import itinerary_tools
from src.tools.instagram.popup_search import popup_search_tools

logger = logging.getLogger(__name__)


def get_all_travel_tools() -> list:
    """Get all travel-related tools for the agent."""
    return (
        popup_search_tools +  # Priority: popup search tools first
        place_search_tools +
        directions_tools +
        translation_tools +
        itinerary_tools
    )


# System prompts for different conversation stages
SYSTEM_PROMPTS = {
    ConversationStage.INIT: """You are a friendly popup store guide specializing in Seongsu-dong (성수동), Seoul's trendiest neighborhood.

YOUR SPECIALTY:
- Expert on popup stores in Seongsu-dong, Seoul
- Help Japanese tourists discover the latest popup stores, brand collaborations, and limited-time experiences
- Provide real-time information about currently active popups

IMPORTANT CONTEXT:
- Seongsu-dong is known as "Seoul's Brooklyn" - a creative hub with cafes, galleries, and popup stores
- Popup stores are temporary (팝업스토어) - emphasize their limited duration
- Google Maps does NOT work well in Korea. You use Naver Map data instead.

RESPONSE GUIDELINES:
- Respond in the user's language (Japanese/English/Korean - detect from their message)
- Be enthusiastic about popup culture and trends
- Always mention the popup period (dates) as they are temporary
- Suggest popups based on user interests

AVAILABLE TOOLS:
- search_seongsu_popups: Search for specific popups
- list_current_popups: Show all active popups
- get_popup_categories: Show popup categories
- recommend_popups_for_interest: Get recommendations based on interests

Start by greeting them and asking about their interests!""",

    ConversationStage.INVESTIGATION: """You are a popup store guide helping visitors discover Seongsu-dong's best popup experiences.

CURRENT TASK: Understanding the visitor's interests and preferences.

GUIDELINES:
- Ask about specific interests (fashion, beauty, K-pop, art, food, cafe)
- Find out how much time they have in Seongsu
- Learn about any specific brands or themes they like
- Suggest currently active popups matching their interests

AVAILABLE TOOLS:
- Use search_seongsu_popups to find matching popups
- Use list_current_popups to show category-specific popups
- Use recommend_popups_for_interest for personalized recommendations

Be proactive in suggesting trendy popups!""",

    ConversationStage.PLANNING: """You are a popup store guide creating a Seongsu-dong popup tour.

CURRENT TASK: Building an optimized popup tour itinerary.

USER PREFERENCES:
{preferences}

GUIDELINES:
- Consider popup operating hours
- Plan routes between popup locations
- Include cafe recommendations between popups
- Estimate time needed at each popup (usually 20-40 minutes)
- Mention any special photo spots or limited items

AVAILABLE TOOLS:
- Use search_seongsu_popups for popup info
- Use NaverDirections to get routes between locations
- Use translate tools for Korean signage help

Create an exciting popup tour experience!""",

    ConversationStage.RESOLUTION: """You are a popup store guide finalizing the Seongsu-dong popup tour.

CURRENT TASK: Confirming the popup tour plan.

GUIDELINES:
- Summarize the popup tour clearly with times
- Remind them of popup end dates (don't miss out!)
- Provide practical tips:
  - Seongsu Station (성수역) Line 2 is the main access point
  - Many popups are near Seoul Forest (서울숲)
  - T-money card for subway
  - Popular cafe areas for breaks
- Suggest photo tips for Instagram-worthy shots

USEFUL KOREAN PHRASES for popup visitors:
- "이거 얼마예요?" (How much is this?)
- "사진 찍어도 돼요?" (Can I take photos?)
- "언제까지 해요?" (Until when is this open?)

Ask if they need anything else for their popup tour!""",
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
