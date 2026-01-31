# Spotfinder - 성수동 팝업스토어 파인더

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![React Native](https://img.shields.io/badge/React%20Native-Expo-blue.svg)](https://expo.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**성수동 팝업스토어를 찾아주는 AI 기반 플랫폼**

[English Documentation](./README.md)

Spotfinder는 관광객(특히 일본인 방문객)이 AI 채팅 어시스턴트를 통해 성수동의 트렌디한 팝업스토어를 발견할 수 있도록 도와줍니다. 웹, 모바일, API 서비스를 지원하는 모던 Monorepo 아키텍처로 구축되었습니다.

## 주요 기능

- **AI 채팅 어시스턴트**: 대화형 팝업스토어 추천
- **다국어 지원**: 일본어, 영어, 한국어
- **실시간 팝업 데이터**: AI 기반 인스타그램 스크래핑
- **인터랙티브 지도**: 네이버 지도 연동 길찾기
- **크로스 플랫폼**: 웹 (Next.js) + 모바일 (React Native)

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              클라이언트 애플리케이션                           │
├─────────────────────────────┬─────────────────────────┬─────────────────────┤
│         apps/web            │       apps/mobile       │     외부 사용자      │
│     (Next.js 15 + RSC)      │   (React Native/Expo)   │                     │
│       Vercel 배포           │    App Store / Play     │                     │
└─────────────────────────────┴─────────────────────────┴─────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              apps/api (FastAPI)                              │
│                               Railway 배포                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  API 게이트웨이  │  │  Business Agent │  │   Instagram 스크래퍼        │  │
│  │  • /api/chat    │  │  • LangGraph    │  │   • Instaloader            │  │
│  │  • /api/popups  │  │  • Tool Calling │  │   • Upstage Document AI    │  │
│  │  • /health      │  │  • Streaming    │  │   • APScheduler            │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              데이터 레이어                                    │
├──────────────────────┬──────────────────────┬───────────────────────────────┤
│       SQLite         │       Qdrant         │         Naver API             │
│   • 팝업스토어 DB     │   • 벡터 메모리       │   • 지도 / 길찾기              │
│   • 로컬 캐시         │   • 임베딩           │   • 지오코딩                   │
└──────────────────────┴──────────────────────┴───────────────────────────────┘
```

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| **웹 프론트엔드** | Next.js 15, React 19, Tailwind CSS, Supabase Auth |
| **모바일 앱** | React Native, Expo Router, Supabase |
| **백엔드 API** | FastAPI, LangGraph, LangChain |
| **LLM** | Upstage Solar / OpenAI (폴백) |
| **데이터베이스** | SQLite (팝업), Qdrant (벡터) |
| **외부 API** | 네이버 지도, 네이버 지오코딩, Instagram |
| **배포** | Vercel (웹), Railway (API), EAS (모바일) |

## 프로젝트 구조

```
spotfinder/
├── apps/
│   ├── api/                    # FastAPI 백엔드
│   │   ├── src/
│   │   │   ├── agents/         # LangGraph AI 에이전트
│   │   │   ├── api/            # FastAPI 라우트 & 미들웨어
│   │   │   ├── config/         # 설정 (Pydantic)
│   │   │   ├── db/             # 데이터베이스 (SQLite, Qdrant)
│   │   │   ├── models/         # 도메인 모델
│   │   │   ├── scraper/        # Instagram 스크래퍼
│   │   │   ├── services/       # LLM, 메모리, 임베딩
│   │   │   └── tools/          # 네이버 API, 번역
│   │   ├── scripts/            # CLI 유틸리티
│   │   ├── tests/              # pytest 테스트
│   │   ├── Dockerfile
│   │   └── pyproject.toml      # uv 의존성
│   │
│   ├── web/                    # Next.js 웹 앱
│   │   ├── src/
│   │   │   ├── app/            # App Router 페이지
│   │   │   ├── components/     # UI 컴포넌트
│   │   │   ├── features/       # 기능 모듈
│   │   │   └── lib/            # 유틸리티
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   └── mobile/                 # React Native 앱
│       ├── app/                # Expo Router
│       ├── components/
│       └── package.json
│
├── docs/                       # 문서
├── docker-compose.yml          # 로컬 개발
├── railway.toml                # Railway 배포
└── README.md
```

## 빠른 시작

### 사전 요구사항

- Python 3.11+ & [uv](https://github.com/astral-sh/uv)
- Node.js 20+
- Docker (선택사항, 로컬 서비스용)

### 백엔드 (API)

```bash
cd apps/api

# uv로 의존성 설치
uv sync

# 환경 변수 설정
cp ../../.env.example .env

# 개발 서버 실행
uv run uvicorn src.api.main:app --reload --port 8080
```

### 프론트엔드 (웹)

```bash
cd apps/web

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env.local

# 개발 서버 실행
npm run dev
```

### 모바일

```bash
cd apps/mobile

# 의존성 설치
npm install

# Expo 시작
npm start
```

### Docker Compose (풀스택)

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

## 배포

| 서비스 | 플랫폼 | 설정 파일 |
|--------|--------|-----------|
| **API** | Railway | `railway.toml` |
| **Web** | Vercel | `apps/web/vercel.json` |
| **Mobile** | EAS Build | `apps/mobile/app.json` |

### Railway (API)

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 배포
railway up
```

### Vercel (Web)

```bash
# Vercel CLI 설치
npm install -g vercel

# apps/web에서 배포
cd apps/web && vercel
```

## API 엔드포인트

### 채팅

```http
POST /api/v1/chat
Content-Type: application/json

{
  "message": "성수동 패션 팝업 추천해줘",
  "thread_id": "session-123"
}
```

### 팝업 목록

```http
GET /api/v1/popups?category=fashion&active_only=true
```

### 헬스 체크

```http
GET /health
```

## 환경 변수

```env
# LLM
UPSTAGE_API_KEY=your-upstage-key
OPENAI_API_KEY=your-openai-key  # 폴백

# 네이버 API
NAVER_CLIENT_ID=your-client-id
NAVER_CLIENT_SECRET=your-client-secret
NAVER_MAP_CLIENT_ID=your-map-client-id
NAVER_MAP_CLIENT_SECRET=your-map-secret

# 데이터베이스
QDRANT_URL=http://localhost:6333

# 프론트엔드
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-key
```

## 개발

### 테스트

```bash
cd apps/api

# 전체 테스트 실행
uv run pytest

# 커버리지 포함
uv run pytest --cov=src
```

### 코드 품질

```bash
# 린트 & 포맷
uv run ruff check src --fix
uv run ruff format src

# 타입 체크
uv run mypy src
```

## 기여하기

1. 저장소 Fork
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 열기

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 참조.

## 감사의 말

- [LangGraph](https://github.com/langchain-ai/langgraph) - AI 에이전트 프레임워크
- [Upstage](https://www.upstage.ai/) - Solar LLM & Document AI
- [네이버 클라우드 플랫폼](https://www.ncloud.com/) - 지도 API
