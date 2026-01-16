# Task Plan: AI Agent with Context Memory Management

> **Generated from**: docs/prd/PRD_ai-agent-context-memory.md
> **Created**: 2026-01-16
> **Updated**: 2026-01-16 (v1.2 - Dual Agent Architecture)
> **Status**: pending

## Execution Config

| Option | Value | Description |
|--------|-------|-------------|
| `auto_commit` | true | 완료 시 자동 커밋 |
| `commit_per_phase` | true | Phase별 중간 커밋 |
| `quality_gate` | true | /auto-commit 품질 검사 |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Dual Agent Architecture                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────┐           │
│  │   Business Agent    │         │   Observer Agent    │           │
│  │   (서버/Waiter)      │  ──────▶│   (주방장/Chef)       │           │
│  │                     │  Redis  │                     │           │
│  │  • 사용자 대화 처리    │  Queue  │  • 로그 수집/분석     │           │
│  │  • 비즈니스 로직      │         │  • Sentry 연동       │           │
│  │  • 동기 응답         │         │  • Better Stack     │           │
│  └─────────────────────┘         └─────────────────────┘           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phases

### Phase 1: Core Infrastructure (MVP)

**Goal**: 기본 대화 가능한 Agent API 구축

| Task | Description | Priority | Est. Files |
|------|-------------|----------|------------|
| 1.1 | 프로젝트 구조 생성 (`src/`, `tests/`, `config/`) | P0 | 5+ |
| 1.2 | 의존성 정의 (`requirements.txt`, `pyproject.toml`) | P0 | 2 |
| 1.3 | 환경 설정 파일 (`config/settings.py`, `.env.example`) | P0 | 2 |
| 1.4 | vLLM 클라이언트 래퍼 구현 (`src/llm/vllm_client.py`) | P0 | 1 |
| 1.5 | AgentState 정의 (`src/agent/state.py`) | P0 | 1 |
| 1.6 | 기본 Agent 구조 (`src/agent/core.py`) | P0 | 1 |
| 1.7 | PostgreSQL 스키마 생성 (`migrations/001_init.sql`) | P0 | 1 |
| 1.8 | Database 연결 모듈 (`src/db/connection.py`) | P0 | 1 |
| 1.9 | FastAPI 서버 기본 구조 (`src/api/main.py`) | P0 | 1 |
| 1.10 | `/chat` 엔드포인트 구현 (`src/api/routes/chat.py`) | P0 | 1 |
| 1.11 | `/health` 엔드포인트 구현 (`src/api/routes/health.py`) | P0 | 1 |
| 1.12 | Context Trimming Middleware (`src/agent/middleware/trimming.py`) | P0 | 1 |
| 1.13 | Input Validation Middleware (`src/agent/middleware/input_validation.py`) | P0 | 1 |
| 1.14 | Docker Compose 설정 (`docker-compose.yml`) | P1 | 1 |
| 1.15 | Phase 1 통합 테스트 | P0 | 2 |

**Checklist**:
- [ ] 1.1 프로젝트 구조 생성
- [ ] 1.2 의존성 정의
- [ ] 1.3 환경 설정 파일
- [ ] 1.4 vLLM 클라이언트 래퍼
- [ ] 1.5 AgentState 정의
- [ ] 1.6 기본 Agent 구조
- [ ] 1.7 PostgreSQL 스키마
- [ ] 1.8 Database 연결 모듈
- [ ] 1.9 FastAPI 서버 기본 구조
- [ ] 1.10 `/chat` 엔드포인트
- [ ] 1.11 `/health` 엔드포인트
- [ ] 1.12 Context Trimming Middleware
- [ ] 1.13 Input Validation Middleware
- [ ] 1.14 Docker Compose 설정
- [ ] 1.15 Phase 1 통합 테스트

**Deliverable**: 기본 대화 가능한 Agent API (Business Agent 기반)

---

### Phase 2: Context Engineering

**Goal**: 자동 요약 및 동적 프롬프트 지원

| Task | Description | Priority | Est. Files |
|------|-------------|----------|------------|
| 2.1 | Token counting 유틸리티 (`src/utils/tokens.py`) - transformers AutoTokenizer 사용 | P0 | 1 |
| 2.2 | Summarization Middleware with Fallback (`src/agent/middleware/summarization.py`) | P0 | 1 |
| 2.3 | Summary Store 구현 (`src/db/summary_store.py`) | P0 | 1 |
| 2.4 | Dynamic Prompt Middleware (`src/agent/middleware/dynamic_prompt.py`) | P0 | 1 |
| 2.5 | Conversation Stage 로직 (`src/agent/stages.py`) | P1 | 1 |
| 2.6 | Turn Metadata Middleware (`src/agent/middleware/metadata.py`) | P1 | 1 |
| 2.7 | Metadata Store 구현 (`src/db/metadata_store.py`) | P1 | 1 |
| 2.8 | Concurrency Control - Redis Lock (`src/utils/distributed_lock.py`) | P0 | 1 |
| 2.9 | Phase 2 단위 테스트 | P0 | 3 |

**Checklist**:
- [ ] 2.1 Token counting 유틸리티
- [ ] 2.2 Summarization Middleware with Fallback
- [ ] 2.3 Summary Store
- [ ] 2.4 Dynamic Prompt Middleware
- [ ] 2.5 Conversation Stage 로직
- [ ] 2.6 Turn Metadata Middleware
- [ ] 2.7 Metadata Store
- [ ] 2.8 Concurrency Control - Redis Lock
- [ ] 2.9 Phase 2 단위 테스트

**Deliverable**: 자동 요약 및 동적 프롬프트 지원

---

### Phase 3: Long-term Memory

**Goal**: Vector DB 기반 장기 기억 검색

| Task | Description | Priority | Est. Files |
|------|-------------|----------|------------|
| 3.1 | Qdrant 클라이언트 설정 (`src/vector/qdrant_client.py`) | P0 | 1 |
| 3.2 | Embedding 모델 래퍼 - BAAI/bge-m3 (`src/vector/embeddings.py`) | P0 | 1 |
| 3.3 | Turn Embedding 파이프라인 (`src/vector/turn_embedder.py`) | P0 | 1 |
| 3.4 | Memory Retrieval Middleware (`src/agent/middleware/memory_retrieval.py`) | P0 | 1 |
| 3.5 | Semantic Search 서비스 (`src/vector/search.py`) | P0 | 1 |
| 3.6 | Hybrid Search 구현 (keyword + semantic) | P2 | 1 |
| 3.7 | Embedding 캐싱 (Redis) | P2 | 1 |
| 3.8 | Phase 3 통합 테스트 | P0 | 2 |

**Checklist**:
- [ ] 3.1 Qdrant 클라이언트 설정
- [ ] 3.2 Embedding 모델 래퍼 (BAAI/bge-m3, 1024d)
- [ ] 3.3 Turn Embedding 파이프라인
- [ ] 3.4 Memory Retrieval Middleware
- [ ] 3.5 Semantic Search 서비스
- [ ] 3.6 Hybrid Search 구현
- [ ] 3.7 Embedding 캐싱 (Redis)
- [ ] 3.8 Phase 3 통합 테스트

**Deliverable**: Vector DB 기반 장기 기억 검색

---

### Phase 4: Observer Agent & Observability

**Goal**: 비동기 모니터링 Agent 및 Observability Stack 구축

| Task | Description | Priority | Est. Files |
|------|-------------|----------|------------|
| 4.1 | Event Schema 정의 (`src/observer/schemas.py`) | P0 | 1 |
| 4.2 | Event Emitter Middleware (`src/agent/middleware/event_emitter.py`) | P0 | 1 |
| 4.3 | Redis Event Queue 설정 (`src/observer/event_queue.py`) | P0 | 1 |
| 4.4 | Observer Agent 코어 (`src/observer/agent.py`) | P0 | 1 |
| 4.5 | Sentry Integration (`src/observer/sentry_handler.py`) | P0 | 1 |
| 4.6 | Better Stack (Logtail) Integration (`src/observer/logtail_handler.py`) | P0 | 1 |
| 4.7 | Structured Logging Setup (`src/utils/logging.py`) | P0 | 1 |
| 4.8 | Alert 전송 서비스 (`src/observer/alerting.py`) | P1 | 1 |
| 4.9 | Observer Agent 실행 스크립트 (`scripts/run_observer.py`) | P0 | 1 |
| 4.10 | Phase 4 통합 테스트 | P0 | 2 |

**Checklist**:
- [ ] 4.1 Event Schema 정의 (AgentEvent)
- [ ] 4.2 Event Emitter Middleware
- [ ] 4.3 Redis Event Queue 설정
- [ ] 4.4 Observer Agent 코어
- [ ] 4.5 Sentry Integration
- [ ] 4.6 Better Stack Integration
- [ ] 4.7 Structured Logging Setup
- [ ] 4.8 Alert 전송 서비스
- [ ] 4.9 Observer Agent 실행 스크립트
- [ ] 4.10 Phase 4 통합 테스트

**Deliverable**: Observer Agent 및 Observability Stack (Sentry + Better Stack)

---

### Phase 5: Entity Management

**Goal**: 자동 엔티티 추출 및 활용

| Task | Description | Priority | Est. Files |
|------|-------------|----------|------------|
| 5.1 | Entity Extractor 인터페이스 (`src/entity/extractor.py`) | P0 | 1 |
| 5.2 | Regex 기반 Entity Extractor (`src/entity/regex_extractor.py`) | P0 | 1 |
| 5.3 | LLM 기반 Entity Extractor (`src/entity/llm_extractor.py`) | P2 | 1 |
| 5.4 | Entity Store 구현 (`src/db/entity_store.py`) | P0 | 1 |
| 5.5 | Entity Extraction Middleware (`src/agent/middleware/entity_extraction.py`) | P0 | 1 |
| 5.6 | Entity 검색 API (`src/api/routes/entities.py`) | P1 | 1 |
| 5.7 | Entity 기반 context enrichment | P1 | 1 |
| 5.8 | Phase 5 단위 테스트 | P0 | 2 |

**Checklist**:
- [ ] 5.1 Entity Extractor 인터페이스
- [ ] 5.2 Regex 기반 Entity Extractor
- [ ] 5.3 LLM 기반 Entity Extractor
- [ ] 5.4 Entity Store
- [ ] 5.5 Entity Extraction Middleware
- [ ] 5.6 Entity 검색 API
- [ ] 5.7 Entity 기반 context enrichment
- [ ] 5.8 Phase 5 단위 테스트

**Deliverable**: 자동 엔티티 추출 및 활용

---

### Phase 6: Production Hardening

**Goal**: Production-ready API 서버

| Task | Description | Priority | Est. Files |
|------|-------------|----------|------------|
| 6.1 | Streaming API 구현 (`/chat/stream`) | P0 | 1 |
| 6.2 | 대화 조회 API (`/conversations/{thread_id}`) | P0 | 1 |
| 6.3 | 대화 삭제 API (`DELETE /conversations/{thread_id}`) | P1 | 1 |
| 6.4 | Error handling 미들웨어 | P0 | 1 |
| 6.5 | Retry 로직 (vLLM, DB) | P0 | 1 |
| 6.6 | Request validation (Pydantic) | P0 | 1 |
| 6.7 | Rate Limiting - slowapi (`src/api/middleware/rate_limit.py`) | P0 | 1 |
| 6.8 | Prometheus 메트릭 설정 | P1 | 1 |
| 6.9 | LangSmith 통합 | P1 | 1 |
| 6.10 | API documentation (OpenAPI) | P1 | 1 |
| 6.11 | Load testing (locust) | P1 | 2 |
| 6.12 | E2E 테스트 | P0 | 2 |

**Checklist**:
- [ ] 6.1 Streaming API
- [ ] 6.2 대화 조회 API
- [ ] 6.3 대화 삭제 API
- [ ] 6.4 Error handling 미들웨어
- [ ] 6.5 Retry 로직
- [ ] 6.6 Request validation
- [ ] 6.7 Rate Limiting
- [ ] 6.8 Prometheus 메트릭
- [ ] 6.9 LangSmith 통합
- [ ] 6.10 API documentation
- [ ] 6.11 Load testing
- [ ] 6.12 E2E 테스트

**Deliverable**: Production-ready API 서버

---

## Project Structure (Target)

```
wigtn-ai-agent/
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── rate_limit.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       ├── conversations.py
│   │       ├── entities.py
│   │       └── health.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── core.py                    # Business Agent
│   │   ├── state.py
│   │   ├── stages.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── trimming.py
│   │       ├── summarization.py
│   │       ├── dynamic_prompt.py
│   │       ├── metadata.py
│   │       ├── memory_retrieval.py
│   │       ├── entity_extraction.py
│   │       ├── input_validation.py    # Prompt Injection 방어
│   │       └── event_emitter.py       # Observer Agent로 이벤트 전송
│   ├── observer/                       # Observer Agent (주방장/Chef)
│   │   ├── __init__.py
│   │   ├── agent.py                   # Observer Agent 코어
│   │   ├── schemas.py                 # AgentEvent 스키마
│   │   ├── event_queue.py             # Redis Event Queue
│   │   ├── sentry_handler.py          # Sentry Integration
│   │   ├── logtail_handler.py         # Better Stack Integration
│   │   └── alerting.py                # Alert 전송 서비스
│   ├── llm/
│   │   ├── __init__.py
│   │   └── vllm_client.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── summary_store.py
│   │   ├── metadata_store.py
│   │   └── entity_store.py
│   ├── vector/
│   │   ├── __init__.py
│   │   ├── qdrant_client.py
│   │   ├── embeddings.py              # BAAI/bge-m3 (1024d)
│   │   ├── turn_embedder.py
│   │   └── search.py
│   ├── entity/
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── regex_extractor.py
│   │   └── llm_extractor.py
│   └── utils/
│       ├── __init__.py
│       ├── tokens.py                  # transformers AutoTokenizer
│       ├── distributed_lock.py        # Redis Distributed Lock
│       └── logging.py                 # Structured Logging (structlog)
├── scripts/
│   ├── run_observer.py                # Observer Agent 실행 스크립트
│   └── run_server.py                  # Business Agent 실행 스크립트
├── tests/
│   ├── __init__.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/
│   ├── __init__.py
│   └── settings.py
├── migrations/
│   └── 001_init.sql
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.observer               # Observer Agent 전용 Dockerfile
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Progress

| Metric | Value |
|--------|-------|
| Total Tasks | 0/62 |
| Current Phase | - |
| Status | pending |

---

## Execution Log

| Timestamp | Phase | Task | Status | Notes |
|-----------|-------|------|--------|-------|
| - | - | - | - | - |

---

## Dependencies

### External Services

| Service | Required | Port | Purpose |
|---------|----------|------|---------|
| vLLM | Yes | 8000 | LLM 추론 |
| PostgreSQL | Yes | 5432 | State/Store 저장 |
| Qdrant | Yes | 6333 | Vector DB (1024d) |
| Redis | Yes | 6379 | Event Queue, Distributed Lock, 캐싱 |
| Sentry | Yes | - | Error Tracking |
| Better Stack | Yes | - | Log Management |

### Python Packages (Core)

```
# LangGraph / LLM
langchain>=0.3.0
langgraph>=0.2.0
langchain-openai>=0.2.0
openai>=1.0.0

# API Framework
fastapi>=0.115.0
uvicorn>=0.32.0
slowapi>=0.1.9

# Database
asyncpg>=0.30.0
redis>=5.0.0

# Vector DB & Embeddings
qdrant-client>=1.12.0
sentence-transformers>=3.3.0

# Tokenizer
transformers>=4.40.0

# Observability
sentry-sdk[fastapi]>=2.0.0
logtail-python>=0.3.0
structlog>=24.0.0
prometheus-client>=0.20.0

# Validation & Config
pydantic>=2.10.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

---

## Notes

- Phase 1 완료 후 기본 대화 테스트 필수
- Phase 3의 Embedding 모델: `BAAI/bge-m3` (1024d, multilingual)
- Phase 4의 Observer Agent는 별도 프로세스로 실행
- Production 배포 전 Phase 6 Load testing 필수
- 각 Phase 완료 시 `git tag` 생성 권장
- Sentry, Better Stack 설정은 Phase 4에서 진행

---

## Environment Variables

```bash
# vLLM
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/agent_db

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key

# Redis
REDIS_URL=redis://localhost:6379/0

# Observability
SENTRY_DSN=https://xxx@sentry.io/xxx
SENTRY_ENVIRONMENT=development
LOGTAIL_TOKEN=your_logtail_token

# Rate Limiting
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
```

---

**Last Updated**: 2026-01-16 (v1.2)
