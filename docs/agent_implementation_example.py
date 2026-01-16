"""
AI Agent Implementation Example
LangGraph create_react_agent + Middleware-based Context Memory Management

Production-ready implementation with:
- Long-term memory (Vector DB + PostgreSQL)
- Dynamic context management
- Custom middleware stack
"""

import os
import asyncio
from datetime import datetime
from typing import Any, TypedDict, Annotated, Sequence
from enum import Enum

# LangChain & LangGraph
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, add_messages
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import create_agent
from langchain.agents.middleware import (
    before_model,
    after_model,
    dynamic_prompt,
    SummarizationMiddleware,
    HumanInTheLoopMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain.tools import tool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store import AsyncPostgresStore

# ============================================================================
# 1. STATE DEFINITION
# ============================================================================

class ConversationStage(str, Enum):
    INITIALIZATION = "init"
    INVESTIGATION = "investigation"
    RESOLUTION = "resolution"

class ConversationMetadata(TypedDict):
    """턴별 메타데이터"""
    turn_number: int
    timestamp: str
    user_intent: str
    extracted_entities: dict
    stage: ConversationStage

class MemoryPointers(TypedDict):
    """Long-term memory 참조"""
    recent_summary_id: str | None
    recent_summary_token_count: int
    important_event_ids: list[str]

class AgentState(TypedDict):
    """Agent 상태 정의"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    metadata: Annotated[Sequence[ConversationMetadata], lambda x, y: y[-1:]]  # 최신만
    memory_pointers: MemoryPointers
    turn_count: int
    model_call_count: int
    should_summarize: bool
    next_node: str

# ============================================================================
# 2. CUSTOM TOOLS
# ============================================================================

@tool
def search_customer_info(customer_id: str) -> str:
    """고객 정보 검색"""
    # Mock implementation
    return f"Customer {customer_id}: Premium member, since 2020"

@tool
def query_orders(customer_id: str) -> str:
    """주문 이력 조회"""
    return f"Customer {customer_id} has 15 orders. Recent: Order #12345 (pending)"

@tool
def process_refund(order_id: str, amount: float) -> str:
    """환불 처리 (승인 필요)"""
    return f"Refund request for Order {order_id}: ${amount}"

tools = [
    search_customer_info,
    query_orders,
    process_refund,
]

# ============================================================================
# 3. CUSTOM MIDDLEWARE
# ============================================================================

# 3.1 Memory Retrieval Middleware
@before_model
async def retrieve_long_term_memory(
    request: ModelRequest,
    handler,
    store: AsyncPostgresStore,
) -> ModelResponse:
    """
    과거 대화에서 relevant한 정보 검색 후 context에 주입.
    """
    state = request.state
    turn = state.get("turn_count", 0)
    
    # 초기 턴에서는 스킵
    if turn < 10:
        return await handler(request)
    
    current_message = state["messages"][-1].content if state["messages"] else ""
    
    # Store에서 유사한 과거 턴 검색
    recent_summaries = await store.list(
        namespace=f"memories_turn_summaries"
    )
    
    if recent_summaries:
        # 최신 요약 가져오기
        latest = recent_summaries[0]
        memory_context = SystemMessage(
            content=f"[Previous Context Summary]\n{latest.get('value', {}).get('text', '')}"
        )
        
        updated_messages = list(state["messages"]) + [memory_context]
        return await handler(request.override(messages=updated_messages))
    
    return await handler(request)

# 3.2 Dynamic System Prompt Middleware
@dynamic_prompt
def generate_dynamic_system_prompt(request: ModelRequest) -> str:
    """
    Conversation stage에 따른 동적 프롬프트 생성.
    """
    state = request.state
    turn = state.get("turn_count", 0)
    
    base = "You are a helpful customer support AI assistant."
    
    # Stage 결정
    if turn <= 5:
        return base + " Your goal: Understand the customer's issue. Ask clarifying questions."
    elif turn <= 20:
        return base + " Your goal: Investigate the issue. Gather necessary information."
    else:
        return base + " Your goal: Provide solutions. Avoid repeating information."

# 3.3 Entity Extraction Middleware
@after_model
async def extract_entities(
    response: ModelResponse,
    handler,
    store: AsyncPostgresStore,
) -> ModelResponse:
    """
    Model 응답에서 중요 엔티티 추출 및 저장.
    """
    state = response.state
    turn = state.get("turn_count", 0)
    
    # Mock entity extraction
    entities = {
        "customer_id": extract_customer_id(response.response.content),
        "order_ids": extract_order_ids(response.response.content),
        "issues": extract_issues(response.response.content),
    }
    
    # Store에 저장
    if any(entities.values()):
        await store.put(
            namespace="entities",
            key=f"turn_{turn}",
            value=entities,
        )
    
    return response

def extract_customer_id(text: str) -> str | None:
    """Mock: 실제로는 NER 또는 regex"""
    if "customer" in text.lower():
        return "CUST_123"
    return None

def extract_order_ids(text: str) -> list[str]:
    """Mock: 실제로는 NER"""
    if "order" in text.lower():
        return ["ORD_12345"]
    return []

def extract_issues(text: str) -> list[str]:
    """Mock: 실제로는 NER"""
    issues = []
    if "billing" in text.lower():
        issues.append("billing")
    if "refund" in text.lower():
        issues.append("refund")
    return issues

# 3.4 Turn Counter & Metadata Middleware
@before_model
async def update_turn_metadata(
    request: ModelRequest,
    handler,
) -> ModelResponse:
    """
    각 턴의 메타데이터 업데이트.
    """
    state = request.state
    state["turn_count"] = state.get("turn_count", 0) + 1
    state["model_call_count"] = state.get("model_call_count", 0) + 1
    
    # Metadata 기록
    metadata = {
        "turn_number": state["turn_count"],
        "timestamp": datetime.now().isoformat(),
        "user_intent": detect_user_intent(request.state["messages"][-1].content),
        "extracted_entities": {},
        "stage": determine_stage(state["turn_count"]),
    }
    
    # State에 메타데이터 추가
    state["metadata"] = [metadata]
    
    return await handler(request)

def detect_user_intent(message: str) -> str:
    """Mock: 실제로는 intent classifier"""
    if any(word in message.lower() for word in ["refund", "return"]):
        return "refund_request"
    elif any(word in message.lower() for word in ["bill", "charge"]):
        return "billing_issue"
    return "general_inquiry"

def determine_stage(turn: int) -> ConversationStage:
    """Turn 수에 따른 stage 결정"""
    if turn <= 5:
        return ConversationStage.INITIALIZATION
    elif turn <= 20:
        return ConversationStage.INVESTIGATION
    else:
        return ConversationStage.RESOLUTION

# ============================================================================
# 4. AGENT INITIALIZATION
# ============================================================================

async def init_agent():
    """Agent 초기화"""
    
    # 1. Model
    model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=1500,
    )
    
    # 2. Checkpointer (대화 지속성)
    checkpointer = PostgresSaver(
        conn_string=os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost/agent_db"
        )
    )
    
    # 3. Store (Long-term memory)
    store = AsyncPostgresStore(
        conn_string=os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost/agent_db"
        ),
        namespace_prefix="agent_",
    )
    
    # 4. Middleware Stack
    middleware = [
        # Turn 업데이트
        update_turn_metadata,
        
        # Memory 검색
        retrieve_long_term_memory,
        
        # Context 요약 (내장)
        SummarizationMiddleware(
            model="openai:gpt-4o-mini",
            trigger=("tokens", 8000),    # 8k tokens 도달 시
            keep=("messages", 30),       # 최근 30개는 유지
        ),
        
        # 위험 도구 승인
        HumanInTheLoopMiddleware(
            interrupt_on={
                "process_refund": True,
                "search_customer_info": False,
                "query_orders": False,
            }
        ),
        
        # 동적 프롬프트
        generate_dynamic_system_prompt,
        
        # 엔티티 추출
        extract_entities,
    ]
    
    # 5. Agent 생성
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="You are a helpful customer support AI.",
        middleware=middleware,
        checkpointer=checkpointer,
        store=store,
    )
    
    return agent, store

# ============================================================================
# 5. AGENT INVOCATION
# ============================================================================

async def run_agent_conversation():
    """Agent와의 대화 예시"""
    
    agent, store = await init_agent()
    
    # 사용자 ID & 세션 ID (대화 지속성)
    user_id = "user_123"
    session_id = "session_456"
    thread_id = f"{user_id}_{session_id}"
    
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # 대화 샘플
    user_inputs = [
        "Hi, I have a billing issue with my recent order.",
        "My order #12345 was charged twice.",
        "Can you help me get a refund?",
        "The charge date was yesterday.",
    ]
    
    for i, user_input in enumerate(user_inputs):
        print(f"\n{'='*60}")
        print(f"Turn {i+1}: User Input")
        print(f"{'='*60}")
        print(f"User: {user_input}\n")
        
        # Agent 호출
        result = await agent.ainvoke(
            {"messages": [HumanMessage(user_input)]},
            config=config,
        )
        
        # 응답 출력
        if result.get("messages"):
            last_message = result["messages"][-1]
            print(f"Agent: {last_message.content}\n")
        
        # 메타데이터 출력
        if result.get("metadata"):
            meta = result["metadata"]
            print(f"[Metadata]")
            print(f"  Turn: {meta.get('turn_number')}")
            print(f"  Intent: {meta.get('user_intent')}")
            print(f"  Stage: {meta.get('stage')}\n")

# ============================================================================
# 6. STREAMING EXAMPLE
# ============================================================================

async def stream_agent_response(
    user_input: str,
    user_id: str,
    session_id: str,
):
    """Agent 응답을 스트리밍하며 반환"""
    
    agent, _ = await init_agent()
    
    thread_id = f"{user_id}_{session_id}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    # 이벤트 스트리밍
    async for event in agent.astream_events(
        {"messages": [HumanMessage(user_input)]},
        config=config,
    ):
        event_type = event.get("event", "")
        
        if event_type == "on_chain_stream":
            # Token 스트리밍
            chunk = event.get("data", {}).get("chunk", {})
            if chunk:
                yield chunk
        
        elif event_type == "on_chain_end":
            # 완료
            output = event.get("data", {}).get("output", {})
            yield output

# ============================================================================
# 7. MEMORY MANAGEMENT UTILITIES
# ============================================================================

async def save_summary_to_store(
    store: AsyncPostgresStore,
    user_id: str,
    turn_number: int,
    summary_text: str,
    token_count: int,
):
    """요약을 Store에 저장"""
    
    await store.put(
        namespace=f"summaries_{user_id}",
        key=f"summary_turn_{turn_number}",
        value={
            "text": summary_text,
            "turn": turn_number,
            "timestamp": datetime.now().isoformat(),
            "token_count": token_count,
        }
    )

async def retrieve_conversation_summary(
    store: AsyncPostgresStore,
    user_id: str,
) -> str | None:
    """최근 요약 검색"""
    
    summaries = await store.list(
        namespace=f"summaries_{user_id}"
    )
    
    if summaries:
        return summaries[0].get("value", {}).get("text")
    return None

# ============================================================================
# 8. MAIN ENTRY POINT
# ============================================================================

async def main():
    """메인 엔트리 포인트"""
    
    # 환경 변수 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        return
    
    print("Initializing AI Agent with Context Memory Management...")
    print("=" * 60)
    
    # Agent 실행
    await run_agent_conversation()

if __name__ == "__main__":
    asyncio.run(main())
