# AI Agent with Context Memory Management PRD

> **Version**: 1.2
> **Created**: 2026-01-16
> **Updated**: 2026-01-16
> **Status**: Ready for Implementation

## 1. Overview

### 1.1 Problem Statement

장기 대화(수백~수천 턴)를 처리하는 AI Agent에서 다음 문제가 발생한다:

1. **Context Window 한계**: LLM의 토큰 제한으로 인해 전체 대화 이력을 유지할 수 없음
2. **비용 및 Latency**: Cloud API 의존 시 비용 증가 및 네트워크 지연
3. **정보 손실**: 단순 truncation 시 중요한 과거 맥락 유실
4. **Privacy**: 민감한 대화 내용이 외부 API로 전송되는 보안 이슈
5. **Observability 부재**: 운영 중 발생하는 이슈를 실시간으로 파악하기 어려움

### 1.2 Goals

- vLLM으로 서빙되는 로컬 LLM 기반 AI Agent 구축
- 효율적인 Context Engineering을 통한 장기 대화 지원 (1000+ 턴)
- Long-term Memory 시스템으로 중요 정보 영구 보존
- **Dual Agent 아키텍처로 비즈니스 로직과 관찰/분석 분리**
- **Sentry + Better Stack 기반 통합 Observability**
- Production-ready 아키텍처 설계

### 1.3 Non-Goals (Out of Scope)

- ~~Multi-agent orchestration (단일 Agent 집중)~~ → **Dual Agent로 확장**
- Fine-tuning 파이프라인 구축
- 실시간 음성/영상 처리
- Mobile SDK 개발

### 1.4 Scope

| 포함 | 제외 |
|------|------|
| vLLM 서버 통합 | 모델 학습/Fine-tuning |
| Context Engineering Middleware | Multi-modal 입력 처리 |
| Long-term Memory (Vector DB) | 3개 이상의 Agent 시스템 |
| Conversation Summarization | 실시간 스트리밍 최적화 |
| Entity Extraction & Storage | UI/Frontend 개발 |
| **Dual Agent (Business + Observer)** | |
| **Sentry Error Tracking** | |
| **Better Stack Log Management** | |

---

## 2. Dual Agent Architecture (Restaurant Model)

### 2.1 Concept: 음식점 모델

```
┌─────────────────────────────────────────────────────────────────┐
│                        🍽️ Restaurant Model                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   👨‍🍳 주방장 (Observer Agent)          🧑‍🍳 서버 (Business Agent)  │
│   ─────────────────────────          ─────────────────────────  │
│   - 로그 수집 & 분석                  - 고객(사용자) 대화         │
│   - 에러 감지 & 알림                  - 주문(요청) 처리           │
│   - 품질 모니터링                     - 서빙(응답) 제공           │
│   - 재료(리소스) 관리                 - 피드백 수집               │
│   - 레시피(패턴) 개선                 - 불만(에러) 전달           │
│                                                                 │
│   [Background / Async]                [Foreground / Sync]       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Agent 역할 정의

| Agent | 역할 | 실행 방식 | 주요 책임 |
|-------|------|----------|----------|
| **Business Agent** | 서버 (Waiter) | Foreground, Sync | 사용자 대화, 비즈니스 로직 |
| **Observer Agent** | 주방장 (Chef) | Background, Async | 로그 수집, 분석, 모니터링 |

### 2.3 Business Agent (서버)

**역할**: 사용자와 직접 소통하며 비즈니스 로직을 수행

```
┌─────────────────────────────────────────────────────────────────┐
│                      Business Agent (서버)                       │
├─────────────────────────────────────────────────────────────────┤
│  Responsibilities:                                              │
│  - 사용자 메시지 수신 및 응답 생성                               │
│  - Context Engineering (요약, 메모리 검색)                       │
│  - 엔티티 추출 및 저장                                          │
│  - 대화 상태 관리 (Checkpointing)                               │
│  - 에러/이벤트를 Observer Agent에 전달                          │
│                                                                 │
│  Middleware Stack:                                              │
│  [0] InputValidation → [1] TurnMetadata → [2] MemoryRetrieval  │
│  → [3] ContextTrimming → [4] Summarization → [5] DynamicPrompt │
│  → [MODEL] → [6] EntityExtraction → [7] EventEmitter           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 Observer Agent (주방장)

**역할**: 백그라운드에서 시스템을 관찰하고 분석

```
┌─────────────────────────────────────────────────────────────────┐
│                      Observer Agent (주방장)                     │
├─────────────────────────────────────────────────────────────────┤
│  Responsibilities:                                              │
│  - 로그 스트림 수집 (Application, vLLM, DB)                     │
│  - 에러 패턴 분석 및 자동 분류                                   │
│  - 성능 메트릭 집계 (Latency, Token Usage)                      │
│  - 이상 탐지 (Anomaly Detection)                                │
│  - 알림 발송 (Sentry, Better Stack, Slack)                      │
│  - 자동 리포트 생성                                             │
│                                                                 │
│  Input Sources:                                                 │
│  [Event Queue] ← Business Agent                                 │
│  [Log Stream] ← Application Logs                                │
│  [Metrics] ← Prometheus/StatsD                                  │
│                                                                 │
│  Output Destinations:                                           │
│  → Sentry (Errors)                                              │
│  → Better Stack (Logs)                                          │
│  → PostgreSQL (Analysis Results)                                │
│  → Slack/Webhook (Alerts)                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.5 Agent 간 통신

```
┌──────────────────┐          Event Queue          ┌──────────────────┐
│  Business Agent  │ ─────────────────────────────→│  Observer Agent  │
│     (서버)        │           (Redis)             │     (주방장)      │
└────────┬─────────┘                               └────────┬─────────┘
         │                                                  │
         │ [Emits Events]                                   │ [Processes]
         │ - request_started                                │ - aggregate
         │ - request_completed                              │ - analyze
         │ - error_occurred                                 │ - alert
         │ - summarization_triggered                        │ - report
         │ - entity_extracted                               │
         │                                                  │
         ▼                                                  ▼
┌──────────────────┐                               ┌──────────────────┐
│   User Response  │                               │ Sentry/BetterStack│
└──────────────────┘                               └──────────────────┘
```

### 2.6 Event Schema

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    REQUEST_STARTED = "request_started"
    REQUEST_COMPLETED = "request_completed"
    ERROR_OCCURRED = "error_occurred"
    SUMMARIZATION_TRIGGERED = "summarization_triggered"
    MEMORY_RETRIEVED = "memory_retrieved"
    ENTITY_EXTRACTED = "entity_extracted"
    RATE_LIMITED = "rate_limited"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"

class AgentEvent(BaseModel):
    event_id: str
    event_type: EventType
    timestamp: datetime
    thread_id: str
    user_id: str | None

    # Event-specific data
    payload: dict

    # Performance metrics
    latency_ms: float | None
    token_count: int | None

    # Error info (if applicable)
    error_code: str | None
    error_message: str | None
    stack_trace: str | None
```

---

## 3. Observability Stack

### 3.1 Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Observability Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Sentry    │     │ Better Stack│     │  LangSmith  │       │
│  │   (Errors)  │     │   (Logs)    │     │  (Traces)   │       │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘       │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                     ┌───────┴───────┐                           │
│                     │ Observer Agent│                           │
│                     │   (주방장)     │                           │
│                     └───────┬───────┘                           │
│                             │                                   │
│         ┌───────────────────┼───────────────────┐               │
│         │                   │                   │               │
│  ┌──────┴──────┐     ┌──────┴──────┐     ┌──────┴──────┐       │
│  │ Application │     │   vLLM      │     │  Database   │       │
│  │    Logs     │     │   Logs      │     │   Logs      │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Sentry Integration

**목적**: Error Tracking, Performance Monitoring, Issue Management

#### 3.2.1 설정

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
    release=os.getenv("APP_VERSION", "1.0.0"),

    # Performance monitoring
    traces_sample_rate=0.2,  # 20% of transactions
    profiles_sample_rate=0.1,  # 10% of profiled transactions

    # Integrations
    integrations=[
        FastApiIntegration(transaction_style="endpoint"),
        SqlalchemyIntegration(),
        RedisIntegration(),
        LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
    ],

    # Data scrubbing
    send_default_pii=False,
    before_send=scrub_sensitive_data,
)
```

#### 3.2.2 Custom Context

```python
def set_agent_context(thread_id: str, user_id: str, turn_number: int):
    """Agent 실행 시 Sentry context 설정"""
    sentry_sdk.set_context("agent", {
        "thread_id": thread_id,
        "user_id": user_id,
        "turn_number": turn_number,
        "agent_type": "business",
    })

    sentry_sdk.set_tag("thread_id", thread_id)
    sentry_sdk.set_user({"id": user_id})
```

#### 3.2.3 Error Capture

```python
from sentry_sdk import capture_exception, capture_message

class SentryMiddleware:
    """Business Agent의 에러를 Sentry로 전송"""

    async def capture_error(self, error: Exception, context: dict):
        with sentry_sdk.push_scope() as scope:
            scope.set_extra("context", context)
            scope.set_tag("error_type", type(error).__name__)

            if isinstance(error, LLMError):
                scope.set_tag("category", "llm")
                scope.set_level("error")
            elif isinstance(error, MemoryError):
                scope.set_tag("category", "memory")
                scope.set_level("warning")

            capture_exception(error)
```

#### 3.2.4 Performance Tracing

```python
from sentry_sdk import start_transaction, start_span

async def process_chat_request(request: ChatRequest):
    with start_transaction(op="chat", name="process_chat") as transaction:
        transaction.set_tag("thread_id", request.thread_id)

        with start_span(op="middleware", description="input_validation"):
            validate_input(request)

        with start_span(op="middleware", description="memory_retrieval"):
            memories = await retrieve_memories(request)

        with start_span(op="llm", description="vllm_inference"):
            response = await call_vllm(request)

        return response
```

### 3.3 Better Stack Integration

**목적**: Centralized Log Management, Log Search, Alerting

#### 3.3.1 설정

```python
import logtail
from logtail import LogtailHandler

# Better Stack (Logtail) handler 설정
handler = LogtailHandler(source_token=os.getenv("BETTERSTACK_SOURCE_TOKEN"))

# Structured logging 설정
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
```

#### 3.3.2 Log Structure

```python
# 표준 로그 구조
log_entry = {
    "timestamp": "2026-01-16T10:30:00Z",
    "level": "info",
    "service": "ai-agent",
    "agent_type": "business",  # business | observer

    # Request context
    "thread_id": "user_123_session_456",
    "user_id": "user_123",
    "request_id": "req_abc123",

    # Event details
    "event": "request_completed",
    "message": "Chat request processed successfully",

    # Metrics
    "latency_ms": 1523,
    "token_count": 256,
    "context_tokens": 4500,

    # Additional context
    "metadata": {
        "stage": "investigation",
        "summarization_triggered": false,
        "entities_extracted": ["order_id:12345"]
    }
}
```

#### 3.3.3 Log Levels & Events

| Level | Event | Description | Example |
|-------|-------|-------------|---------|
| DEBUG | memory_retrieved | 메모리 검색 완료 | `{"top_k": 3, "similarity": 0.85}` |
| INFO | request_started | 요청 시작 | `{"thread_id": "...", "message_preview": "..."}` |
| INFO | request_completed | 요청 완료 | `{"latency_ms": 1500, "tokens": 256}` |
| WARNING | summarization_fallback | 요약 실패, fallback | `{"reason": "timeout"}` |
| WARNING | rate_limited | Rate limit 적용 | `{"limit": 20, "retry_after": 32}` |
| ERROR | llm_error | vLLM 호출 실패 | `{"error": "connection_refused"}` |
| ERROR | prompt_injection | Prompt injection 탐지 | `{"pattern": "ignore previous"}` |
| CRITICAL | service_down | 서비스 중단 | `{"component": "vllm"}` |

#### 3.3.4 Better Stack Alerts

```yaml
# Better Stack Alert Rules
alerts:
  - name: "High Error Rate"
    condition: "count(level:error) > 10 in 5m"
    channels: [slack, email]
    severity: critical

  - name: "LLM Latency Spike"
    condition: "avg(latency_ms) > 5000 in 5m"
    channels: [slack]
    severity: warning

  - name: "Summarization Failures"
    condition: "count(event:summarization_fallback) > 5 in 10m"
    channels: [slack]
    severity: warning

  - name: "Prompt Injection Attempts"
    condition: "count(event:prompt_injection) > 3 in 1h"
    channels: [slack, email]
    severity: critical
```

### 3.4 Observer Agent Implementation

```python
import asyncio
from redis import asyncio as aioredis

class ObserverAgent:
    """
    주방장 Agent: 로그 수집, 분석, 알림
    Background에서 비동기로 실행
    """

    def __init__(
        self,
        redis_url: str,
        sentry_dsn: str,
        betterstack_token: str,
    ):
        self.redis = aioredis.from_url(redis_url)
        self.event_queue = "agent:events"
        self.logger = structlog.get_logger()

        # Initialize Sentry
        sentry_sdk.init(dsn=sentry_dsn)

        # Initialize Better Stack
        self.logtail = LogtailHandler(source_token=betterstack_token)

        # Analysis state
        self.error_counts: dict[str, int] = {}
        self.latency_buffer: list[float] = []

    async def run(self):
        """메인 이벤트 루프"""
        self.logger.info("Observer Agent started", agent_type="observer")

        while True:
            try:
                # Event Queue에서 이벤트 수신
                event_data = await self.redis.blpop(self.event_queue, timeout=1)

                if event_data:
                    event = AgentEvent.model_validate_json(event_data[1])
                    await self.process_event(event)

            except Exception as e:
                self.logger.error("Event processing failed", error=str(e))
                sentry_sdk.capture_exception(e)

    async def process_event(self, event: AgentEvent):
        """이벤트 처리 및 분석"""

        # 1. Log to Better Stack
        self.log_event(event)

        # 2. Error handling
        if event.event_type == EventType.ERROR_OCCURRED:
            await self.handle_error(event)

        # 3. Metrics collection
        if event.latency_ms:
            self.latency_buffer.append(event.latency_ms)

        # 4. Anomaly detection
        await self.detect_anomalies(event)

        # 5. Periodic analysis (매 100개 이벤트)
        if len(self.latency_buffer) >= 100:
            await self.analyze_and_report()

    def log_event(self, event: AgentEvent):
        """Better Stack으로 로그 전송"""
        log_data = {
            "event": event.event_type.value,
            "thread_id": event.thread_id,
            "user_id": event.user_id,
            "latency_ms": event.latency_ms,
            "token_count": event.token_count,
            **event.payload,
        }

        if event.error_code:
            self.logger.error(event.error_message, **log_data)
        else:
            self.logger.info(f"Event: {event.event_type.value}", **log_data)

    async def handle_error(self, event: AgentEvent):
        """에러 처리 및 Sentry 전송"""
        error_type = event.error_code or "unknown"
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Sentry로 에러 전송
        with sentry_sdk.push_scope() as scope:
            scope.set_context("event", event.model_dump())
            scope.set_tag("error_type", error_type)
            sentry_sdk.capture_message(
                event.error_message,
                level="error"
            )

        # 연속 에러 감지
        if self.error_counts[error_type] >= 5:
            await self.send_alert(
                severity="critical",
                message=f"Repeated errors: {error_type} ({self.error_counts[error_type]} times)"
            )

    async def detect_anomalies(self, event: AgentEvent):
        """이상 탐지"""
        # Latency anomaly
        if event.latency_ms and event.latency_ms > 5000:
            await self.send_alert(
                severity="warning",
                message=f"High latency detected: {event.latency_ms}ms",
                context={"thread_id": event.thread_id}
            )

        # Prompt injection
        if event.event_type == EventType.PROMPT_INJECTION_DETECTED:
            await self.send_alert(
                severity="critical",
                message="Prompt injection attempt detected",
                context=event.payload
            )

    async def analyze_and_report(self):
        """주기적 분석 및 리포트"""
        if not self.latency_buffer:
            return

        avg_latency = sum(self.latency_buffer) / len(self.latency_buffer)
        p95_latency = sorted(self.latency_buffer)[int(len(self.latency_buffer) * 0.95)]

        report = {
            "period": "last_100_events",
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "error_counts": dict(self.error_counts),
            "total_events": len(self.latency_buffer),
        }

        self.logger.info("Performance report", **report)

        # Reset buffers
        self.latency_buffer = []
        self.error_counts = {}

    async def send_alert(self, severity: str, message: str, context: dict = None):
        """알림 발송"""
        alert_data = {
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
        }

        self.logger.warning("Alert triggered", **alert_data)

        # Slack webhook (optional)
        if os.getenv("SLACK_WEBHOOK_URL"):
            await self.send_slack_alert(alert_data)
```

### 3.5 Event Emitter (Business Agent용)

```python
class EventEmitterMiddleware:
    """
    Business Agent에서 Observer Agent로 이벤트 전송
    Middleware Stack의 마지막에 위치
    """

    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.queue_name = "agent:events"

    async def emit(self, event: AgentEvent):
        """이벤트를 Redis Queue에 전송"""
        await self.redis.rpush(
            self.queue_name,
            event.model_dump_json()
        )

    async def emit_request_started(self, thread_id: str, user_id: str):
        await self.emit(AgentEvent(
            event_id=str(uuid4()),
            event_type=EventType.REQUEST_STARTED,
            timestamp=datetime.now(),
            thread_id=thread_id,
            user_id=user_id,
            payload={"status": "started"},
            latency_ms=None,
            token_count=None,
            error_code=None,
            error_message=None,
            stack_trace=None,
        ))

    async def emit_request_completed(
        self,
        thread_id: str,
        user_id: str,
        latency_ms: float,
        token_count: int,
        metadata: dict,
    ):
        await self.emit(AgentEvent(
            event_id=str(uuid4()),
            event_type=EventType.REQUEST_COMPLETED,
            timestamp=datetime.now(),
            thread_id=thread_id,
            user_id=user_id,
            payload=metadata,
            latency_ms=latency_ms,
            token_count=token_count,
            error_code=None,
            error_message=None,
            stack_trace=None,
        ))

    async def emit_error(
        self,
        thread_id: str,
        user_id: str,
        error: Exception,
    ):
        await self.emit(AgentEvent(
            event_id=str(uuid4()),
            event_type=EventType.ERROR_OCCURRED,
            timestamp=datetime.now(),
            thread_id=thread_id,
            user_id=user_id,
            payload={"error_class": type(error).__name__},
            latency_ms=None,
            token_count=None,
            error_code=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
        ))
```

---

## 4. User Stories

### 4.1 Primary Users

1. **개발자/운영자**: 장기 대화를 효율적으로 처리하는 AI Agent 구축
2. **SRE/DevOps**: 시스템 모니터링 및 문제 대응

### 4.2 Acceptance Criteria (Gherkin)

```gherkin
Scenario: 장기 대화에서 과거 맥락 유지
  Given Agent가 500턴 이상의 대화를 진행했을 때
  When 사용자가 100턴 전에 언급한 주제를 다시 질문하면
  Then Agent는 Long-term Memory에서 관련 정보를 검색하여 응답한다

Scenario: Context Window 초과 방지
  Given 대화 토큰이 설정된 임계값(6000 tokens)을 초과했을 때
  When 새로운 사용자 입력이 들어오면
  Then 오래된 메시지를 요약하고 최근 20개 메시지만 유지한다

Scenario: 에러 발생 시 자동 추적
  Given Business Agent에서 에러가 발생했을 때
  When 에러가 Observer Agent로 전달되면
  Then Sentry에 에러가 기록되고 Better Stack에 로그가 저장된다

Scenario: 성능 이상 감지
  Given 응답 시간이 5초를 초과하면
  When Observer Agent가 이를 감지하면
  Then Slack 알림이 발송되고 Better Stack에 경고 로그가 기록된다

Scenario: Prompt Injection 탐지 및 알림
  Given 사용자가 악의적인 프롬프트를 입력하면
  When InputValidationMiddleware가 이를 탐지하면
  Then 요청이 차단되고 Observer Agent가 보안 알림을 발송한다
```

---

## 5. Functional Requirements

| ID | Requirement | Priority | Dependencies |
|----|-------------|----------|--------------|
| FR-001 | vLLM OpenAI-compatible API 연동 | P0 (Must) | vLLM 서버 |
| FR-002 | LangGraph create_react_agent 기반 Agent 구조 | P0 (Must) | FR-001 |
| FR-003 | Context Trimming Middleware (토큰 기반) | P0 (Must) | FR-002 |
| FR-004 | Summarization Middleware (자동 요약) | P0 (Must) | FR-002 |
| FR-005 | Long-term Memory Store (PostgreSQL) | P0 (Must) | - |
| FR-006 | Vector DB 기반 Semantic Search | P0 (Must) | FR-005 |
| FR-007 | Memory Retrieval Middleware | P0 (Must) | FR-005, FR-006 |
| FR-008 | Dynamic System Prompt Middleware | P1 (Should) | FR-002 |
| FR-009 | Entity Extraction Middleware | P1 (Should) | FR-002 |
| FR-010 | Turn Metadata 관리 | P1 (Should) | FR-002 |
| FR-011 | Conversation State Checkpointing | P1 (Should) | FR-005 |
| FR-012 | Human-in-the-Loop (위험 도구 승인) | P2 (Could) | FR-002 |
| FR-013 | Embedding 캐싱 (Redis) | P2 (Could) | FR-006 |
| FR-014 | Rate Limiting | P0 (Must) | - |
| FR-015 | Input Validation & Sanitization | P0 (Must) | FR-002 |
| FR-016 | Concurrency Control (thread_id별) | P0 (Must) | FR-005 |
| FR-017 | Token Counting (정확한 토크나이저) | P0 (Must) | FR-003 |
| FR-018 | Summarization Fallback | P0 (Must) | FR-004 |
| **FR-019** | **Observer Agent (Background)** | **P0 (Must)** | FR-020, FR-021 |
| **FR-020** | **Sentry Error Tracking** | **P0 (Must)** | - |
| **FR-021** | **Better Stack Log Management** | **P0 (Must)** | - |
| **FR-022** | **Event Queue (Redis)** | **P0 (Must)** | FR-019 |
| **FR-023** | **Event Emitter Middleware** | **P0 (Must)** | FR-019, FR-022 |
| **FR-024** | **Anomaly Detection** | **P1 (Should)** | FR-019 |
| **FR-025** | **Slack Alert Integration** | **P1 (Should)** | FR-019 |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| LLM Response Time (p95) | < 3000ms | vLLM 로컬 추론 |
| Memory Retrieval Time | < 200ms | Vector DB 쿼리 |
| Context Summarization | < 2000ms | 별도 모델 또는 동일 모델 |
| Concurrent Sessions | 100+ | Thread 기반 isolation |
| Max Conversation Turns | 1000+ | Summarization + Memory |
| **Event Processing Latency** | **< 100ms** | **Observer Agent** |
| **Log Ingestion Rate** | **1000+ events/sec** | **Better Stack** |

### 6.2 Scalability

- 수평 확장: 다중 vLLM 인스턴스 + Load Balancer
- 수직 확장: GPU 메모리 기반 배치 처리
- **Observer Agent**: 다중 인스턴스 가능 (Consumer Group)

### 6.3 Security

| Area | Requirement |
|------|-------------|
| 데이터 저장 | PostgreSQL 암호화 (at rest) |
| API 통신 | 내부 네트워크 (localhost/VPC) |
| 인증 | API Key 기반 (환경별 정책) |
| 로깅 | 민감 정보 마스킹 |
| 입력 검증 | Prompt Injection 방어 |
| SQL 보안 | ORM 사용, Raw SQL 금지 |
| **Sentry** | **PII scrubbing 활성화** |
| **Better Stack** | **민감 필드 자동 마스킹** |

### 6.4 Reliability

- Checkpointer로 대화 상태 영구 저장
- vLLM 서버 장애 시 재시도 로직 (3회, exponential backoff)
- Graceful degradation (Memory 검색 실패 시 최근 컨텍스트만 사용)
- Summarization 실패 시 Fallback
- **Observer Agent 장애 시 Event Queue 보존 (Redis persistence)**
- **Sentry/Better Stack 장애 시 로컬 로그 fallback**

### 6.5 Rate Limiting

| Endpoint | Limit | Window | Burst |
|----------|-------|--------|-------|
| POST /chat | 20 req | 1 min | 5 |
| POST /chat/stream | 10 req | 1 min | 3 |
| GET /conversations | 60 req | 1 min | 10 |
| DELETE /conversations | 10 req | 1 min | 2 |

### 6.6 Input Validation & Prompt Injection 방어

(기존 섹션 유지)

### 6.7 Concurrency Control

(기존 섹션 유지)

### 6.8 Summarization Fallback Strategy

(기존 섹션 유지)

---

## 7. Technical Design

### 7.1 System Architecture (Dual Agent)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Client Application                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Server (API Layer)                           │
│   - Rate Limiting (Redis + slowapi)                                         │
│   - Input Validation                                                         │
│   - Sentry Performance Tracing                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
┌───────────────────────────────────┐   ┌───────────────────────────────────┐
│      Business Agent (서버)         │   │      Observer Agent (주방장)       │
│  ┌─────────────────────────────┐  │   │  ┌─────────────────────────────┐  │
│  │     Middleware Stack        │  │   │  │     Event Processor         │  │
│  │  [0] InputValidation        │  │   │  │  - Log aggregation          │  │
│  │  [1] TurnMetadata           │  │   │  │  - Error analysis           │  │
│  │  [2] MemoryRetrieval        │  │   │  │  - Anomaly detection        │  │
│  │  [3] ContextTrimming        │  │   │  │  - Alert dispatch           │  │
│  │  [4] Summarization          │  │   │  └─────────────────────────────┘  │
│  │  [5] DynamicPrompt          │  │   │                │                  │
│  │  [MODEL CALL]               │  │   │                ▼                  │
│  │  [6] EntityExtraction       │  │   │  ┌─────────────────────────────┐  │
│  │  [7] EventEmitter ─────────────────→  │     External Services       │  │
│  └─────────────────────────────┘  │   │  │  - Sentry (Errors)          │  │
│                                   │   │  │  - Better Stack (Logs)      │  │
│  [Foreground / Synchronous]       │   │  │  - Slack (Alerts)           │  │
└───────────────────────────────────┘   │  └─────────────────────────────┘  │
        │                               │                                   │
        │                               │  [Background / Asynchronous]      │
        │                               └───────────────────────────────────┘
        │                                               │
        ▼                                               │
┌───────────────────────────────────────────────────────┴───────────────────┐
│                              Redis                                         │
│   - Rate Limit Counter                                                     │
│   - Distributed Lock                                                       │
│   - Event Queue (agent:events)                                            │
│   - Embedding Cache                                                        │
└───────────────────────────────────────────────────────────────────────────┘
        │                               │                       │
        ▼                               ▼                       ▼
┌───────────────┐            ┌───────────────┐       ┌───────────────────────┐
│  vLLM Server  │            │  PostgreSQL   │       │  Vector DB (Qdrant)   │
│  (LLM 추론)    │            │  (State/Store)│       │  (Semantic Search)    │
└───────────────┘            └───────────────┘       └───────────────────────┘
```

### 7.2 vLLM Integration

(기존 섹션 유지)

### 7.3 Context Engineering Strategy

(기존 섹션 유지)

### 7.4 Middleware Execution Flow (Updated)

```
User Input
    │
    ▼
[0] InputValidationMiddleware (before_model)
    - Prompt Injection 패턴 탐지
    - 입력 길이 검증 (max 4000자)
    - 특수 문자 이스케이프
    │
    ▼
[1] TurnMetadataMiddleware (before_model)
    - turn_count 증가
    - timestamp 기록
    - user_intent 분류
    │
    ▼
[2] MemoryRetrievalMiddleware (before_model)
    - 현재 쿼리로 Vector DB 검색
    - 유사한 과거 턴/요약 검색 (top-k=3, threshold=0.7)
    - SystemMessage로 context 주입
    │
    ▼
[3] ContextTrimmingMiddleware (before_model)
    - 토크나이저로 정확한 토큰 수 계산
    - 6000 tokens 초과 시 오래된 메시지 제거
    - 최근 20개 메시지 유지
    │
    ▼
[4] SummarizationMiddleware (before_model)
    - 제거된 메시지 요약 (with Fallback)
    - 요약 결과 Store에 저장
    - 요약 텍스트를 context에 추가
    │
    ▼
[5] DynamicPromptMiddleware (dynamic_prompt)
    - conversation stage 판단 (init/investigation/resolution)
    - stage에 맞는 system prompt 생성
    │
    ▼
[MODEL CALL - vLLM]
    │
    ▼
[6] EntityExtractionMiddleware (after_model)
    - 응답에서 엔티티 추출 (NER/regex)
    - Store에 저장
    - Vector DB에 embedding 저장
    │
    ▼
[7] EventEmitterMiddleware (after_model) [NEW]
    - request_completed 이벤트 발행
    - latency, token_count 포함
    - Observer Agent로 전송
    │
    ▼
Agent Response
```

### 7.5 Token Counting Strategy

(기존 섹션 유지)

### 7.6 Database Schema

(기존 섹션 유지 + 아래 추가)

```sql
-- Observer Agent Analysis Results
CREATE TABLE observer_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL,  -- 'performance', 'error_summary', 'anomaly'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    report_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert History
CREATE TABLE alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'critical'
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    context JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 7.7 API Specification

(기존 섹션 유지)

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (MVP)

- [ ] vLLM 서버 설정 및 연동
- [ ] LangGraph Agent 기본 구조 구현 (Business Agent)
- [ ] PostgreSQL 스키마 생성
- [ ] 기본 API 엔드포인트 구현 (`/chat`, `/health`)
- [ ] Context Trimming Middleware 구현
- [ ] Token Counting 유틸리티 구현
- [ ] Rate Limiting 구현 (Redis + slowapi)
- [ ] Input Validation Middleware 구현
- [ ] Concurrency Control 구현 (Redis Lock)
- [ ] **Sentry 기본 통합**
- [ ] **Better Stack 기본 통합**

**Deliverable**: 기본 대화 가능한 Business Agent API (Observability 포함)

### Phase 2: Context Engineering

- [ ] Summarization Middleware 구현
- [ ] Summarization Fallback 전략 구현
- [ ] Dynamic Prompt Middleware 구현
- [ ] Turn Metadata 관리 구현

**Deliverable**: 자동 요약 및 동적 프롬프트 지원

### Phase 3: Long-term Memory

- [ ] Qdrant 설정 및 연동
- [ ] Embedding 생성 파이프라인 구현 (bge-m3)
- [ ] Memory Retrieval Middleware 구현
- [ ] Semantic Search 최적화 (top-k=3, threshold=0.7)

**Deliverable**: Vector DB 기반 장기 기억 검색

### Phase 4: Observer Agent

- [ ] **Event Queue 구현 (Redis)**
- [ ] **Event Emitter Middleware 구현**
- [ ] **Observer Agent 기본 구조 구현**
- [ ] **Log Aggregation 파이프라인**
- [ ] **Error Analysis 로직**
- [ ] **Anomaly Detection 구현**
- [ ] **Alert Dispatch (Slack)**

**Deliverable**: 완전한 Observer Agent (주방장)

### Phase 5: Entity Management

- [ ] Entity Extraction Middleware 구현
- [ ] Entity Store 및 검색 API
- [ ] Entity 기반 context enrichment

**Deliverable**: 자동 엔티티 추출 및 활용

### Phase 6: Production Hardening

- [ ] Streaming API 구현 (`/chat/stream`)
- [ ] Error handling 및 retry 로직
- [ ] Monitoring & Logging 강화
- [ ] Load testing 및 성능 최적화
- [ ] **Sentry Performance Monitoring 최적화**
- [ ] **Better Stack Dashboard 구성**
- [ ] **Alert Rules 튜닝**

**Deliverable**: Production-ready Dual Agent 시스템

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Long conversation support | 1000+ turns | 정보 손실 없이 대화 지속 |
| Memory retrieval accuracy | > 80% | 관련 과거 정보 검색 정확도 |
| Context utilization | < 80% of limit | 토큰 효율성 |
| Response latency (p95) | < 3000ms | vLLM 추론 시간 |
| Summarization quality | > 4.0/5.0 | Human evaluation |
| System uptime | > 99.5% | Availability |
| Rate limit effectiveness | < 0.1% abuse | 악용 시도 차단률 |
| Prompt injection blocked | 100% | 탐지된 공격 차단률 |
| **Error detection rate** | **> 99%** | **Sentry 캡처율** |
| **Log ingestion success** | **> 99.9%** | **Better Stack** |
| **Alert response time** | **< 5 min** | **MTTR** |
| **Observer Agent latency** | **< 100ms** | **Event 처리 시간** |

---

## 10. Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| LLM Serving | vLLM | 로컬 추론, OpenAI-compatible API |
| LLM Model | Qwen2.5-7B-Instruct | 한국어/영어 성능, 적절한 크기 |
| Agent Framework | LangGraph | Middleware 지원, Checkpointer |
| Vector DB | Qdrant | 경량, Self-hosted, 고성능 |
| Database | PostgreSQL | State 저장, pgvector 확장 가능 |
| Embedding | BAAI/bge-m3 | 다국어(한국어), 1024 차원, 고성능 |
| API Server | FastAPI | 비동기, OpenAPI 자동 생성 |
| Rate Limiting | Redis + slowapi | 분산 환경 지원 |
| Concurrency | Redis Lock | thread_id별 제어 |
| Caching | Redis | Embedding 캐싱 |
| Token Counter | transformers | 정확한 토큰 계산 |
| **Error Tracking** | **Sentry** | **에러 추적, 성능 모니터링** |
| **Log Management** | **Better Stack** | **중앙 집중 로그, 검색, 알림** |
| **Event Queue** | **Redis Streams** | **Agent 간 이벤트 통신** |
| **Alerting** | **Slack Webhook** | **실시간 알림** |
| **Structured Logging** | **structlog** | **JSON 로그, Better Stack 호환** |

---

## 11. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| vLLM 서버 장애 | High | Medium | Health check, 자동 재시작, fallback |
| 요약 품질 저하 | Medium | Medium | Fallback 전략, prompt 최적화 |
| Vector 검색 부정확 | Medium | Medium | Hybrid search, reranking |
| 메모리 누수 | Medium | Low | Async cleanup, connection pooling |
| 동시성 이슈 | High | Medium | Redis Lock 구현 |
| DoS 공격 | High | Medium | Rate Limiting 구현 |
| Prompt Injection | High | High | Input Validation, 패턴 탐지 |
| 토큰 계산 오류 | Medium | Medium | 정확한 토크나이저 사용 |
| **Observer Agent 장애** | **Medium** | **Low** | **Event Queue 보존, 재시작** |
| **Sentry 할당량 초과** | **Low** | **Medium** | **샘플링 비율 조정** |
| **Better Stack 비용** | **Low** | **Low** | **로그 보존 기간 조정** |
| **Event Queue 백프레셔** | **Medium** | **Low** | **Consumer 스케일링** |

---

## 12. Resolved Questions

| 질문 | 결정 | 근거 |
|-----|------|------|
| Embedding 모델 선택 | BAAI/bge-m3 | 다국어(한국어) 지원, 1024 차원 |
| Summarization 모델 | 동일 vLLM | 리소스 효율 |
| 요약 트리거 조건 | 토큰 기반 (6000 tokens) | 일관된 context budget |
| 최근 메시지 유지 수 | 20개 | 3000 tokens 내 적절한 컨텍스트 |
| Rate Limiting 방식 | Redis + slowapi | 분산 환경 지원 |
| 동시성 제어 방식 | Redis Distributed Lock | 분산 환경 지원 |
| **Error Tracking** | **Sentry** | **업계 표준, 풍부한 기능** |
| **Log Management** | **Better Stack** | **모던 UI, 저렴한 비용** |
| **Agent 간 통신** | **Redis Streams** | **신뢰성, 간편함** |
| **Alert 채널** | **Slack** | **팀 협업 도구 통합** |

---

## 13. Environment Variables

```bash
# Core
VLLM_BASE_URL=http://localhost:8000/v1
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_db
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Observability
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.2

BETTERSTACK_SOURCE_TOKEN=xxx

# Alerting
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx

# Feature Flags
OBSERVER_AGENT_ENABLED=true
ANOMALY_DETECTION_ENABLED=true
```

---

## 14. References

- [LangGraph Middleware Documentation](https://docs.langchain.com)
- [vLLM Documentation](https://docs.vllm.ai)
- [Qdrant Documentation](https://qdrant.tech/documentation)
- [BAAI/bge-m3 Model](https://huggingface.co/BAAI/bge-m3)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Better Stack (Logtail)](https://betterstack.com/docs/logs/)
- [기존 아키텍처 설계서](./ai_agent_architecture_design.md)
- [PRD Analysis Report](./PRD_ai-agent-context-memory_ANALYSIS.md)

---

**Document Owner**: AI Team
**Last Updated**: 2026-01-16
**Version**: 1.2 (Dual Agent + Observability)
