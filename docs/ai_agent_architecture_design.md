# AI Agent 아키텍처 설계 (LangGraph create_react_agent 기반)
## 장기 대화 Context Memory 관리 전략

**작성일**: 2025.01.16  
**버전**: v1.0  
**대상**: LangChain 1.0+ / LangGraph 1.0+

---

## 1. 개요

Chatbase 같은 AI Agent에서 장기 대화(수백~수천 턴)를 처리할 때 Context Window 한계는 필연적인 문제다. 본 설계는 **LangGraph의 create_react_agent()와 Middleware 시스템을 활용하여 체계적인 Context Memory 관리 전략**을 제시한다.

### 1.1 핵심 문제
- **Transient Context**: 단일 model call에서만 유효한 메시지 (token 제약)
- **Persistent State**: 모든 턴에 저장되는 전체 대화 이력 (무제한 증가)
- **Context Explosion**: 수 백 턴 이후 relevance 없는 정보로 인한 모델 성능 저하

### 1.2 해결 전략 (3-Layer Architecture)
```
┌─────────────────────────────────────────────┐
│   Model Call (Token-Limited Context)        │
│ - Immediate Context (최근 N턴)              │
│ - Retrieved Memory (유의미한 과거)           │
│ - System Prompt (동적 생성)                 │
└─────────────────────────────────────────────┘
                    ↑
      ┌─────────────┴──────────────┐
      ↓                            ↓
┌──────────────────┐    ┌──────────────────┐
│ Short-term       │    │ Long-term        │
│ Memory           │    │ Memory           │
│ (State)          │    │ (Store)          │
│                  │    │                  │
│ Recent messages  │    │ Vector DB        │
│ Metadata         │    │ Summarized       │
│ Active turn      │    │ entities         │
│ Counters         │    │ Important events │
└──────────────────┘    └──────────────────┘
```

---

## 2. 기술 스택 & 선택 근거

### 2.1 Why create_react_agent()?
- ✅ Production-ready ReAct pattern 구현
- ✅ Native Middleware 지원 (before_model, after_model, modify_model_request)
- ✅ Checkpointer 통한 stateful 대화 관리
- ✅ 확장성: 복잡한 그래프 수작업 필요 없음
- ❌ Custom node 추가 시 한계 (→ 직접 StateGraph 구성 필요)

### 2.2 Middleware 활용 우위
Traditional approach (여러 parameter):
```python
# Pre-3.0 방식: parameter explosion
agent = create_react_agent(
    model=model,
    tools=tools,
    prompt=...          # 하나만 가능
    pre_model_hook=..., # 하나만 가능
    post_model_hook=... # 하나만 가능
)
```

**Modern approach (Middleware):**
```python
# v1.0+ 방식: composable, modular
agent = create_react_agent(
    model=model,
    tools=tools,
    middleware=[
        context_trimming_mw,
        summarization_mw,
        memory_retrieval_mw,
        dynamic_system_prompt_mw,
        guardrails_mw,
        logging_mw,
    ]
)
```

---

## 3. 상태(State) 설계

### 3.1 AgentState 정의

```python
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, add_messages

class ConversationMetadata(TypedDict):
    """턴별 메타데이터"""
    turn_number: int
    timestamp: str
    user_intent: str          # "query", "clarification", "feedback"
    extracted_entities: dict  # {"product": "...", "issue": "..."}
    summary_trigger: bool     # 이 턴에서 요약 발동했는지
    

class MemoryPointers(TypedDict):
    """Long-term memory 참조"""
    recent_summary_id: str | None        # 최근 요약된 기간
    recent_summary_token_count: int
    important_event_ids: list[str]       # 중요 사건 IDs
    

class AgentState(TypedDict):
    """Agent 상태"""
    # Core
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Metadata
    metadata: Annotated[Sequence[ConversationMetadata], lambda x, y: y]  # 최신만
    
    # Memory management
    memory_pointers: MemoryPointers
    
    # Counters
    turn_count: int
    model_call_count: int
    
    # Control flow
    should_summarize: bool
    next_node: str  # "agent" or "end"
```

### 3.2 Checkpointer 설정

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Production: 영구 저장
checkpointer = PostgresSaver(
    conn_string="postgresql://user:pass@localhost/agent_db"
)

# Development: 메모리 기반
from langgraph.checkpoint.memory import InMemorySaver
checkpointer = InMemorySaver()
```

---

## 4. Middleware 전략

### 4.1 Middleware 실행 순서 및 책임

```
Agent Invocation
      ↓
[1] before_agent (initialization)
      ↓
[2] before_model (context preparation)
   ├─ 2a. Memory Retrieval MW
   ├─ 2b. Context Trimming MW
   ├─ 2c. Dynamic Prompt MW
   └─ 2d. Entity Extraction MW
      ↓
[Model Call]
      ↓
[3] after_model (validation & persistence)
   ├─ 3a. Guardrails MW
   ├─ 3b. Event Logging MW
   └─ 3c. Summarization Check MW
      ↓
[Tool Execution]
      ↓
[4] after_agent (cleanup & analytics)
```

### 4.2 핵심 Middleware 구현

#### 4.2.1 Memory Retrieval Middleware
**목적**: Long-term memory에서 relevant한 과거 정보 검색 후 context에 주입

```python
from langchain.agents.middleware import before_model
from typing import Any
import asyncio

@before_model
async def retrieve_long_term_memory(
    request: ModelRequest,
    handler,
    store: BaseStore,  # InjectedStore 
) -> ModelResponse:
    """
    현재 메시지와 유사한 과거 대화 검색.
    Vector DB를 사용한 semantic search.
    """
    state = request.state
    current_message = state["messages"][-1].content
    turn = state.get("turn_count", 0)
    
    # 최근 50턴 이내면 검색 스킵 (overhead 방지)
    if turn < 50:
        return await handler(request)
    
    # Semantic search: 현재 쿼리와 유사한 과거 턴 찾기
    similar_past_turns = await semantic_search_from_store(
        query=current_message,
        store=store,
        top_k=3,
        similarity_threshold=0.7
    )
    
    # Retrieved memory를 context로 주입
    if similar_past_turns:
        context_msg = SystemMessage(
            content=f"Related past context:\n" + 
                   "\n".join([t["summary"] for t in similar_past_turns])
        )
        updated_messages = list(request.state["messages"]) + [context_msg]
        return await handler(request.override(messages=updated_messages))
    
    return await handler(request)
```

**기술 선택**:
- Embedding: OpenAI text-embedding-3-small (경량)
- Vector DB: Pinecone / Qdrant (serverless) 또는 PostgreSQL + pgvector
- Retrieval: Approximate Nearest Neighbor (ANN) search

---

#### 4.2.2 Context Trimming Middleware
**목적**: Token limit 직전에 transient context 정리 (불필요한 메시지 제거)

```python
from langchain.agents.middleware import before_model
from langchain.agents.middleware import (
    SummarizationMiddleware,
    ContextSize,
)

# 내장 Summarization MW 사용 (권장)
summarization_mw = SummarizationMiddleware(
    model="openai:gpt-4o-mini",  # 빠르고 저렴
    trigger=("tokens", 10000),    # 10k tokens 도달 시 발동
    keep=("messages", 30),        # 최근 30개 메시지는 유지
    token_counter=count_tokens_approximately,
)

# 커스텀 Trimming (선택사항: 더 세밀한 제어)
@before_model
async def trim_context_by_relevance(
    request: ModelRequest,
    handler,
) -> ModelResponse:
    """
    Token 기반이 아닌 relevance 기반 trimming.
    최근 N턴은 무조건 유지, 그 이전은 selective 제거.
    """
    messages = request.state["messages"]
    turn = request.state.get("turn_count", 0)
    
    # Keep recent messages always
    keep_n = 20
    if len(messages) <= keep_n:
        return await handler(request)
    
    recent = messages[-keep_n:]
    older = messages[:-keep_n]
    
    # Older 중에서 도메인-관련성 없는 것 제거
    # (예: casual chat, debugging logs)
    filtered_older = [
        msg for msg in older
        if msg.type in ["ai", "tool"]  # AI decision 또는 tool result만
        and not is_noise_message(msg)   # 노이즈 판정
    ]
    
    trimmed = filtered_older + recent
    return await handler(request.override(messages=trimmed))
```

---

#### 4.2.3 Dynamic System Prompt Middleware
**목적**: Conversation stage / user intent에 따라 시스템 프롬프트 동적 생성

```python
from langchain.agents.middleware import dynamic_prompt

@dynamic_prompt
def generate_system_prompt(request: ModelRequest) -> str:
    """
    현재 conversation state에 기반한 시스템 프롬프트 생성.
    """
    state = request.state
    turn = state.get("turn_count", 0)
    metadata = state.get("metadata", {})
    
    base_prompt = """You are a helpful AI assistant specializing in customer support."""
    
    # Stage 1: Initialization (턴 1-5)
    if turn <= 5:
        return base_prompt + "\n\nGather initial information about the customer's issue."
    
    # Stage 2: Investigation (턴 6-20)
    elif turn <= 20:
        intent = metadata.get("user_intent", "unknown")
        return base_prompt + f"\n\nFocus on investigating: {intent}. Ask clarifying questions if needed."
    
    # Stage 3: Resolution (턴 21+)
    else:
        return base_prompt + "\n\nProvide concrete solutions. Avoid repeating information."
    
    # Additional context from memory
    if state.get("memory_pointers", {}).get("important_event_ids"):
        return base_prompt + f"\n\nImportant context: {metadata.get('summary')}"
    
    return base_prompt
```

---

#### 4.2.4 Entity Extraction Middleware
**목적**: 각 턴에서 중요 엔티티 자동 추출 → 나중에 검색 시 활용

```python
from langchain.agents.middleware import after_model

@after_model
async def extract_and_store_entities(
    request: ModelResponse,
    handler,
    store: BaseStore,
) -> ModelResponse:
    """
    Model 응답에서 도메인 엔티티 추출.
    (예: 제품명, 고객명, issue type)
    """
    ai_message = request.response
    turn = request.state.get("turn_count", 0)
    
    # Entity extraction (LLM 또는 regex)
    entities = await extract_entities_with_llm(
        text=ai_message.content,
        schema={
            "products": ["product_name"],
            "issues": ["issue_type", "severity"],
            "users": ["user_name", "user_id"],
        }
    )
    
    # Store에 저장 (나중 검색용)
    if entities:
        await store.put(
            namespace=f"entities_turn_{turn}",
            key="extracted",
            value=entities,
        )
    
    return request
```

---

### 4.3 내장 Middleware 활용

```python
from langchain.agents.middleware import (
    SummarizationMiddleware,
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
)

# 1. Summarization (Context Window 관리)
summarization = SummarizationMiddleware(
    model="openai:gpt-4o-mini",
    trigger=("fraction", 0.7),  # 70% context 도달 시
    keep=("messages", 50),      # 최근 50개는 유지
)

# 2. Human-in-the-Loop (위험 도구)
hitl = HumanInTheLoopMiddleware(
    interrupt_on={
        "delete_customer_record": True,
        "process_refund": True,
        "query_database": False,  # 자동 승인
    }
)

# 3. Call Limits (runaway 방지)
call_limits = ModelCallLimitMiddleware(
    thread_limit=100,   # 스레드당 100 model calls
    run_limit=20,       # 단일 run 당 20 calls
    exit_behavior="end",  # limit 도달 시 종료
)
```

---

## 5. Long-term Memory (Store) 설계

### 5.1 Store 아키텍처

```python
from langgraph.store import InMemoryStore  # Dev
from langgraph.store import AsyncPostgresStore  # Prod

store = AsyncPostgresStore(
    conn_string="postgresql://...",
    namespace_prefix="agent_",  # 격리
)

# Store 구조:
# namespace: "agent_conversation_<user_id>_<session_id>"
# ├─ "summaries"     → List[{period, text, tokens, timestamp}]
# ├─ "entities"      → Dict[entity_name, List[turn_ids]]
# ├─ "events"        → List[{type, data, timestamp}]  # 중요 사건
# ├─ "embeddings"    → {turn_id: embedding_vector}
# └─ "metadata"      → {turn_count, last_summary_turn, ...}
```

### 5.2 요약 (Summary) 전략

```python
async def create_conversation_summary(
    messages: list,
    store: BaseStore,
    user_id: str,
) -> dict:
    """
    Sliding window 요약 (누적 손실 최소화).
    """
    # 이전 요약 로드
    previous = await store.get(
        namespace=f"agent_{user_id}",
        key="latest_summary"
    )
    
    # 새로운 구간만 요약
    new_messages = messages[previous["end_idx"]:]
    
    summary_text = await summarize_with_llm(
        messages=new_messages,
        previous_context=previous["text"] if previous else None,
        focus_areas=["key decisions", "unresolved issues", "next steps"]
    )
    
    # Store에 저장
    await store.put(
        namespace=f"agent_{user_id}",
        key="latest_summary",
        value={
            "text": summary_text,
            "start_idx": previous["end_idx"],
            "end_idx": len(messages),
            "timestamp": datetime.now(),
            "token_count": count_tokens(summary_text),
        }
    )
    
    return {"summary": summary_text, "updated": True}
```

**요약 전략 선택**:
- **Fixed Interval**: 매 50턴마다 (예측 가능)
- **Token-based**: Context 70% 도달 시 (동적)
- **Event-based**: 중요 사건 발생 시 (수동 트리거)

### 5.3 Embedding & Vector Search

```python
from langchain_openai import OpenAIEmbeddings
import numpy as np

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

async def embed_and_store_turn(
    turn_id: int,
    message_content: str,
    store: BaseStore,
    user_id: str,
):
    """각 턴을 embedding하고 저장."""
    embedding = embeddings.embed_query(message_content)
    
    await store.put(
        namespace=f"agent_{user_id}_embeddings",
        key=f"turn_{turn_id}",
        value={
            "embedding": embedding,  # float32 list
            "text": message_content[:500],  # 검색 결과용
            "timestamp": datetime.now(),
        }
    )

async def semantic_search_from_store(
    query: str,
    store: BaseStore,
    user_id: str,
    top_k: int = 3,
) -> list[dict]:
    """Semantic search (embedding 기반)."""
    query_embedding = embeddings.embed_query(query)
    
    # Store에서 모든 embedding 로드 (또는 Vector DB 사용)
    all_turns = await store.list(
        namespace=f"agent_{user_id}_embeddings"
    )
    
    # Cosine similarity 계산
    similarities = []
    for turn in all_turns:
        stored_emb = np.array(turn["embedding"])
        query_emb = np.array(query_embedding)
        sim = np.dot(stored_emb, query_emb) / (
            np.linalg.norm(stored_emb) * np.linalg.norm(query_emb)
        )
        similarities.append((turn, sim))
    
    # Top-K 반환
    return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
```

---

## 6. 통합 Agent 구성

### 6.1 완전한 Agent 생성 예시

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store import AsyncPostgresStore
from langchain.agents.middleware import (
    SummarizationMiddleware,
    HumanInTheLoopMiddleware,
)

# 1. Initialize
model = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.7,
    max_tokens=2000,
)

tools = [
    search_tool,
    database_query_tool,
    email_tool,
    # ...
]

# 2. Checkpointer & Store
checkpointer = PostgresSaver(
    conn_string="postgresql://user:pass@localhost/agent_db"
)

store = AsyncPostgresStore(
    conn_string="postgresql://user:pass@localhost/agent_db",
    namespace_prefix="agent_",
)

# 3. Middleware Stack
middleware = [
    # Memory retrieval (before_model)
    retrieve_long_term_memory,  # Custom
    
    # Context management
    SummarizationMiddleware(
        model="openai:gpt-4o-mini",
        trigger=("tokens", 10000),
        keep=("messages", 50),
    ),
    
    # Safety controls
    HumanInTheLoopMiddleware(
        interrupt_on={
            "delete_record": True,
            "send_email": True,
        }
    ),
    
    # Dynamic prompting
    generate_system_prompt,  # Custom
    
    # Entity extraction
    extract_and_store_entities,  # Custom
]

# 4. Create Agent
agent = create_agent(
    model=model,
    tools=tools,
    system_prompt="You are a helpful customer support AI.",
    middleware=middleware,
    checkpointer=checkpointer,
    store=store,
)

# 5. Invoke with Thread ID (대화 지속성)
result = await agent.ainvoke(
    {
        "messages": [
            HumanMessage("I have a billing issue.")
        ]
    },
    config={
        "configurable": {
            "thread_id": "user_123_session_456"  # 중요!
        }
    }
)
```

### 6.2 Stream + 점진적 결과 처리

```python
async def stream_agent_response(
    user_input: str,
    user_id: str,
    session_id: str,
):
    """Agent 응답을 스트리밍하며 실시간 처리."""
    config = {
        "configurable": {
            "thread_id": f"{user_id}_{session_id}"
        }
    }
    
    async for event in agent.astream_events(
        {"messages": [HumanMessage(user_input)]},
        config=config,
    ):
        if event["event"] == "on_chain_start":
            # Model 호출 시작
            pass
        elif event["event"] == "on_chain_stream":
            # Token 스트리밍
            token = event.get("data", {}).get("chunk", {})
            yield token  # WebSocket으로 전송
        elif event["event"] == "on_chain_end":
            # 완료
            yield event.get("data", {}).get("output", {})
```

---

## 7. 기술 검토 사항

### 7.1 Middleware vs Custom Node

| 측면 | Middleware | Custom Node |
|------|-----------|-----------|
| 작성 난이도 | 낮음 | 높음 |
| 유연성 | 중간 | 높음 |
| 재사용성 | 높음 | 낮음 |
| 성능 | 우수 | 우수 |
| 타입 안전성 | 보장 | 보장 |

**언제 Custom Node를 써야 하나?**
- Middleware로 불가능한 복잡한 로직
- 별도의 그래프 분기 필요
- Tool execution 자체를 커스터마이징
→ 이 경우: create_react_agent 대신 StateGraph 직접 구성

### 7.2 Memory 선택: Vector DB vs PostgreSQL

| 기준 | Vector DB (Pinecone) | PostgreSQL + pgvector |
|------|-----------|-----------|
| 초기 설정 | 빠름 (SaaS) | 복잡 (자체 호스팅) |
| 비용 | 높음 (pay-as-you-go) | 낮음 (고정) |
| 확장성 | 무제한 | 서버 의존 |
| Latency | 낮음 | 중간 |
| 학습곡선 | 낮음 | 중간 |

**추천**: 
- **초기**: Pinecone (빠른 구현)
- **성숙**: PostgreSQL + pgvector (비용 효율)

### 7.3 Summarization Model 선택

```python
# 속도 + 비용 우선
model="openai:gpt-4o-mini"  # 추천

# 품질 우선 (더 정확한 요약)
model="openai:gpt-4-turbo"

# 가장 경제적
model="openai:gpt-3.5-turbo"

# 자체 호스팅 (제약 없음)
model=ChatOllama(model="mistral:latest")
```

---

## 8. 모니터링 & 관찰성 (Observability)

### 8.1 LangSmith Integration

```python
import os
from langsmith import Client

os.environ["LANGSMITH_API_KEY"] = "..."
os.environ["LANGSMITH_PROJECT"] = "agent_chatbase"

client = Client()

# Agent 실행은 자동으로 trace됨
result = agent.invoke(
    {"messages": [...]},
    config={"configurable": {"thread_id": "..."}}
)
# LangSmith에서 모든 middleware 실행, token 사용, 성능 추적
```

### 8.2 커스텀 메트릭

```python
@after_model
async def log_metrics(request: ModelResponse, handler):
    """각 model call의 성능 지표 기록."""
    turn = request.state.get("turn_count", 0)
    msg_count = len(request.state["messages"])
    
    metrics = {
        "turn": turn,
        "message_count": msg_count,
        "model_call_count": request.state.get("model_call_count", 0),
        "context_tokens": estimate_tokens(request.state["messages"]),
        "timestamp": datetime.now(),
    }
    
    # DB 또는 analytics에 저장
    await log_to_database(metrics)
    
    return request
```

---

## 9. 일반적인 문제 & 해결책

### Q1: "요약이 중요한 정보를 놓치고 있어요"
**A**: 
- Summarization model을 더 능력있는 것으로 변경 (gpt-4o)
- Custom entity extractor로 요약 전에 중요 정보 미리 추출
- Multi-turn 요약 (최근 N turnf만 요약하고, 더 이전은 keep)

### Q2: "Semantic search가 엉뚱한 결과를 반환해요"
**A**:
- Embedding model 변경 (text-embedding-3-large)
- Hybrid search (keyword + semantic) 사용
- RAG retriever의 chunk size 조정
- Top-K 증가 후 reranking (cross-encoder)

### Q3: "Long-running conversation에서 메모리가 터져요"
**A**:
- Checkpointer 저장소 주기적 cleanup
- Summarization trigger를 더 자주 (예: 5000 tokens)
- Old summaries 압축 (older summaries를 1개로 병합)
- Async streaming으로 메모리 leak 방지

### Q4: "Middleware 순서가 중요한가요?"
**A**: **YES!**
```
Best practice:
1. Memory Retrieval (context 추가)
2. Summarization (trimming)
3. Entity Extraction (metadata)
4. Dynamic Prompt (모든 context 준비됨)
5. Model Call
6. Guardrails (안전성)
7. Event Logging (기록)
```

---

## 10. 배포 체크리스트

- [ ] Checkpointer 설정 (PostgreSQL)
- [ ] Store 설정 (Vector DB 또는 PostgreSQL)
- [ ] Middleware stack 순서 검증
- [ ] LangSmith project 설정
- [ ] Error handling (middleware에서 exception)
- [ ] Rate limiting (API call 제약)
- [ ] Load testing (동시 사용자 X)
- [ ] Privacy compliance (data storage)
- [ ] Backup strategy (critical conversations)
- [ ] Monitoring alerts (token usage, latency)

---

## 11. 참고 자료

- LangChain Docs: https://docs.langchain.com/oss/python/langchain/agents
- LangGraph Checkpointer: https://docs.langchain.com/oss/python/langgraph/concepts/persistence
- Context Engineering: https://blog.langchain.com/context-engineering-for-agents/
- Deep Agents: https://github.com/langchain-ai/deepagents

---

**끝**
