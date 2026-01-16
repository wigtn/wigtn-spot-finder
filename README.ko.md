# Spotfinder

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://github.com/langchain-ai/langgraph)

**외국인을 위한 AI 기반 한국 여행 어시스턴트**

[English Documentation](./README.md)

Spotfinder는 외국인들이 한국의 숨겨진 명소를 발견하고, 여행 일정을 계획하며, 네이버 지도를 활용해 한국을 탐험할 수 있도록 돕는 지능형 여행 에이전트입니다. 안정적인 프로덕션 환경을 위한 듀얼 에이전트 아키텍처로 구축되었습니다.

## 주요 기능

- **다국어 지원**: 영어, 일본어, 중국어 등 다양한 언어로 대화
- **스마트 장소 검색**: 네이버 지도를 통한 맛집, 관광지, 로컬 명소 발견
- **여행 일정 계획**: 최적화된 일별 여행 스케줄 자동 생성
- **실시간 길찾기**: 대중교통, 도보, 자동차 경로 안내
- **번역 지원**: 파파고 API를 통한 자연스러운 한국어 번역
- **대화 기억**: 세션 간 사용자 선호도 기억
- **프로덕션 레디**: Rate limiting, Circuit breaker, 포괄적 에러 처리

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 요청                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI 게이트웨이                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Rate Limiter │  │ 입력 검증    │  │ 에러 핸들러           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────┐
│     Business Agent        │   │       Observer Agent          │
│        (서버/웨이터)        │   │         (주방장/셰프)          │
│                           │   │                               │
│  • 사용자 상호작용          │   │  • 품질 모니터링               │
│  • 도구 오케스트레이션      │   │  • 분석 데이터 수집            │
│  • 응답 생성               │   │  • 대화 품질 평가              │
└───────────────────────────┘   └───────────────────────────────┘
                │                               │
                ▼                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          도구 레이어                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ 네이버 지도  │  │ 파파고 번역  │  │ 여행 일정 생성기         │ │
│  │ • 장소 검색  │  │ • 번역      │  │ • 일정 계획             │ │
│  │ • 길찾기    │  │ • 표현 안내  │  │ • 비용 추정             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         데이터 레이어                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ PostgreSQL  │  │   Redis     │  │   Qdrant                │ │
│  │ • 세션      │  │ • 캐시      │  │ • 벡터 메모리            │ │
│  │ • 메타데이터 │  │ • 분산 락   │  │ • 시맨틱 검색            │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 기술 스택

| 카테고리 | 기술 |
|----------|------|
| **AI 프레임워크** | LangGraph, LangChain |
| **LLM** | vLLM (로컬) / OpenAI (폴백) |
| **API** | FastAPI, Uvicorn |
| **데이터베이스** | PostgreSQL, Redis, Qdrant |
| **외부 API** | 네이버 지도 API, 파파고 번역 |
| **관측성** | Sentry, Logtail, Prometheus |

## 빠른 시작

### 사전 요구사항

- Python 3.11+
- Docker & Docker Compose
- 네이버 클라우드 플랫폼 계정 (지도 및 파파고 API용)

### 1. 저장소 클론

```bash
git clone https://github.com/Hyeongseob91/spotfinder.git
cd spotfinder
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

필수 환경 변수:

```env
# LLM 설정
VLLM_BASE_URL=http://localhost:8000/v1
LLM_MODEL=your-model-name

# 네이버 API (필수)
NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret

# 데이터베이스
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/spotfinder
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# 선택: OpenAI 폴백
OPENAI_API_KEY=your-openai-key
```

### 3. Docker Compose로 시작

```bash
docker-compose up -d
```

### 4. 또는 로컬에서 실행

```bash
# 의존성 설치
pip install -e ".[dev]"

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 시작
uvicorn src.api.main:app --reload --port 8080
```

## API 엔드포인트

### 채팅

```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "강남에서 맛있는 한식당 추천해줘",
  "thread_id": "user-123-session-1",
  "user_id": "user-123"
}
```

### 헬스 체크

```http
GET /health
```

### 메트릭

```http
GET /metrics
```

## 사용 예시

### 장소 검색

```
사용자: "홍대 근처에 좋은 카페 찾아줘"
에이전트: 홍대역 근처의 인기 카페들을 찾았습니다:

1. **카페 어니언** - 트렌디한 인더스트리얼 스타일 카페
   📍 주소: 성동구 양제길 5
   ⭐ 평점: 4.5/5

2. **프릳츠 커피** - 훌륭한 베이커리로 유명
   📍 주소: 마포구 동교로 41길 17
   ⭐ 평점: 4.3/5
```

### 여행 일정 계획

```
사용자: "서울 3일 여행 일정 짜줘"
에이전트: 서울 3일 여행 일정입니다:

**1일차: 역사 속 서울**
- 오전: 경복궁
- 점심: 토속촌 삼계탕
- 오후: 북촌 한옥마을
- 저녁: 인사동 쇼핑

**2일차: 현대 서울**
...
```

### 길찾기

```
사용자: "명동에서 남산타워 어떻게 가?"
에이전트: 다음과 같은 경로가 있습니다:

🚇 **지하철 + 케이블카** (추천)
- 명동에서 4호선 타고 회현역 하차
- 남산 케이블카 정류장까지 도보 (10분)
- 케이블카로 N서울타워 이동
- 총 소요시간: ~30분, ₩15,000

🚶 **도보**
- 거리: 2.1 km (오르막)
- 소요시간: ~40분
```

## 개발

### 테스트 실행

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 테스트 파일
pytest tests/unit/test_context_engineering.py -v
```

### 코드 품질

```bash
# 린팅
ruff check src tests

# 타입 체크
mypy src

# 코드 포맷팅
ruff format src tests
```

### 프로젝트 구조

```
spotfinder/
├── src/
│   ├── agents/           # Business & Observer 에이전트
│   ├── api/              # FastAPI 애플리케이션
│   │   ├── routes/       # API 엔드포인트
│   │   └── middleware/   # 에러 처리
│   ├── config/           # 설정 관리
│   ├── db/               # 데이터베이스 연결
│   │   ├── postgres/     # PostgreSQL 저장소
│   │   └── qdrant/       # 벡터 DB 연결
│   ├── middleware/
│   │   └── core/         # 컨텍스트 엔지니어링
│   ├── models/           # Pydantic 모델
│   ├── services/
│   │   ├── llm/          # LLM 클라이언트
│   │   └── memory/       # 장기 기억
│   ├── tools/            # 에이전트 도구
│   │   ├── naver/        # 네이버 지도 API
│   │   ├── i18n/         # 번역
│   │   └── travel/       # 여행 일정 계획
│   └── utils/            # 유틸리티
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                 # 문서
├── scripts/              # 유틸리티 스크립트
└── docker-compose.yml    # 컨테이너 오케스트레이션
```

## 컨텍스트 엔지니어링

Spotfinder는 정교한 컨텍스트 관리를 구현합니다:

| 기능 | 설명 |
|------|------|
| **트리밍** | 토큰 제한 내에서 스마트한 메시지 자르기 |
| **요약** | 4단계 폴백 (Claude → GPT-4 → Local → 규칙 기반) |
| **동적 프롬프트** | 단계별 시스템 프롬프트 (INIT → INVESTIGATION → PLANNING → RESOLUTION) |
| **메모리 검색** | 시맨틱 검색 + 최신성 기반 랭킹 |

## 기여하기

기여를 환영합니다! PR을 제출하기 전에 기여 가이드라인을 읽어주세요.

1. 저장소 Fork
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 열기

## 라이선스

이 프로젝트는 MIT 라이선스로 배포됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 감사의 말

- [LangGraph](https://github.com/langchain-ai/langgraph) - 에이전트 프레임워크
- [네이버 클라우드 플랫폼](https://www.ncloud.com/) - 지도 및 번역 API
- Anthropic의 Claude - AI 개발 지원
