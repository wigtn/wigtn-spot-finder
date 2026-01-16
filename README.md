# Spotfinder

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://github.com/langchain-ai/langgraph)

**AI-powered travel assistant for foreigners exploring Korea**

[한국어 문서](./README.ko.md)

Spotfinder is an intelligent travel agent that helps foreigners discover hidden gems, plan itineraries, and navigate Korea using Naver Map integration. Built with a dual-agent architecture for robust, production-ready performance.

## Features

- **Multilingual Support**: Communicate in English, Japanese, Chinese, and more
- **Smart Place Discovery**: Find restaurants, attractions, and local spots via Naver Map
- **Itinerary Planning**: Generate optimized day-by-day travel schedules
- **Real-time Directions**: Get transit, walking, and driving routes
- **Translation Assistance**: Seamless Korean translation with Papago API
- **Conversation Memory**: Remember user preferences across sessions
- **Production Ready**: Rate limiting, circuit breakers, and comprehensive error handling

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Gateway                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Rate Limiter │  │ Input Valid. │  │ Error Handler        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│      Business Agent       │   │       Observer Agent          │
│         (Waiter)          │   │          (Chef)               │
│                           │   │                               │
│  • User interaction       │   │  • Quality monitoring         │
│  • Tool orchestration     │   │  • Analytics collection       │
│  • Response generation    │   │  • Conversation scoring       │
└───────────────────────────┘   └───────────────────────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Tool Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Naver Map   │  │ Papago i18n │  │ Itinerary Generator     │ │
│  │ • Search    │  │ • Translate │  │ • Day planning          │ │
│  │ • Directions│  │ • Phrases   │  │ • Cost estimation       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ PostgreSQL  │  │   Redis     │  │   Qdrant                │ │
│  │ • Sessions  │  │ • Cache     │  │ • Vector memory         │ │
│  │ • Metadata  │  │ • Locks     │  │ • Semantic search       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Category | Technology |
|----------|------------|
| **AI Framework** | LangGraph, LangChain |
| **LLM** | vLLM (local) / OpenAI (fallback) |
| **API** | FastAPI, Uvicorn |
| **Database** | PostgreSQL, Redis, Qdrant |
| **External APIs** | Naver Map API, Papago Translation |
| **Observability** | Sentry, Logtail, Prometheus |

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Naver Cloud Platform account (for Map & Papago APIs)

### 1. Clone the repository

```bash
git clone https://github.com/Hyeongseob91/spotfinder.git
cd spotfinder
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:

```env
# LLM Configuration
VLLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=your-model-name

# Naver API (Required)
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/spotfinder
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Optional: OpenAI fallback
OPENAI_API_KEY=your-openai-key
```

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

### 4. Or run locally

```bash
# Install dependencies
pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.api.main:app --reload --port 8080
```

## API Endpoints

### Chat

```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "Find me the best Korean BBQ restaurants in Gangnam",
  "thread_id": "user-123-session-1",
  "user_id": "user-123"
}
```

### Health Check

```http
GET /health
```

### Metrics

```http
GET /metrics
```

## Usage Examples

### Finding Places

```
User: "I want to find good cafes near Hongdae"
Agent: I found several popular cafes near Hongdae station:

1. **Cafe Onion** - Trendy industrial-style cafe
   📍 Address: 5 Yangje-gil, Seongdong-gu
   ⭐ Rating: 4.5/5

2. **Fritz Coffee** - Known for excellent pastries
   📍 Address: 17 Donggyo-ro 41-gil, Mapo-gu
   ⭐ Rating: 4.3/5
```

### Planning Itinerary

```
User: "Plan a 3-day trip to Seoul for me"
Agent: Here's your 3-day Seoul itinerary:

**Day 1: Historic Seoul**
- Morning: Gyeongbokgung Palace
- Lunch: Tosokchon Samgyetang
- Afternoon: Bukchon Hanok Village
- Evening: Insadong shopping

**Day 2: Modern Seoul**
...
```

### Getting Directions

```
User: "How do I get from Myeongdong to N Seoul Tower?"
Agent: Here are your options:

🚇 **By Subway + Cable Car** (Recommended)
- Take Line 4 from Myeongdong to Hoehyeon
- Walk to Namsan Cable Car station (10 min)
- Take cable car to N Seoul Tower
- Total: ~30 minutes, ₩15,000

🚶 **Walking**
- Distance: 2.1 km uphill
- Time: ~40 minutes
```

## Development

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_context_engineering.py -v
```

### Code Quality

```bash
# Linting
ruff check src tests

# Type checking
mypy src

# Format code
ruff format src tests
```

### Project Structure

```
spotfinder/
├── src/
│   ├── agents/           # Business & Observer agents
│   ├── api/              # FastAPI application
│   │   ├── routes/       # API endpoints
│   │   └── middleware/   # Error handling
│   ├── config/           # Settings management
│   ├── db/               # Database connections
│   │   ├── postgres/     # PostgreSQL repositories
│   │   └── qdrant/       # Vector DB connection
│   ├── middleware/
│   │   └── core/         # Context engineering
│   ├── models/           # Pydantic models
│   ├── services/
│   │   ├── llm/          # LLM client
│   │   └── memory/       # Long-term memory
│   ├── tools/            # Agent tools
│   │   ├── naver/        # Naver Map APIs
│   │   ├── i18n/         # Translation
│   │   └── travel/       # Itinerary planning
│   └── utils/            # Utilities
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                 # Documentation
├── scripts/              # Utility scripts
└── docker-compose.yml    # Container orchestration
```

## Context Engineering

Spotfinder implements sophisticated context management:

| Feature | Description |
|---------|-------------|
| **Trimming** | Smart message truncation within token limits |
| **Summarization** | 4-level fallback (Claude → GPT-4 → Local → Rule-based) |
| **Dynamic Prompts** | Stage-aware system prompts (INIT → INVESTIGATION → PLANNING → RESOLUTION) |
| **Memory Retrieval** | Semantic search with recency-based ranking |

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [Naver Cloud Platform](https://www.ncloud.com/) for Map and Translation APIs
- Anthropic's Claude for AI assistance in development
