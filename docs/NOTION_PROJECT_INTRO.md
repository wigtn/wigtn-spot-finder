# Spotfinder - AI 성수동 팝업스토어 가이드

> 외국인 관광객(특히 일본인)을 위한 AI 기반 성수동 팝업스토어 추천 서비스

---

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | Spotfinder (스팟파인더) |
| **목표 사용자** | 한국 방문 일본인 관광객 |
| **핵심 기능** | 팝업스토어 탐색, AI 챗봇 가이드, 지도 연동 |
| **개발 기간** | 2025년 1월 |
| **Frontend URL** | https://frontend-blue-gamma-56.vercel.app |
| **Backend URL** | https://wigtn-spot-finder-production.up.railway.app |

---

## 주요 기능

### 1. 팝업스토어 갤러리
- 성수동 26개 실제 팝업스토어 정보
- 카테고리별 필터링 (패션, 뷰티, 카페, 아트 등)
- 검색 기능
- 상세 정보 페이지 (운영시간, 위치, 설명)

### 2. AI 여행 가이드 챗봇
- **Upstage Solar Pro 2** LLM 연동
- 실시간 스트리밍 응답 (SSE)
- 맞춤형 팝업스토어 추천
- 다국어 대화 지원 (일본어, 영어, 한국어)

### 3. 다국어 지원 (i18n)
- 일본어 (기본 언어)
- 영어
- 한국어
- 헤더에서 원클릭 언어 전환
- localStorage 저장으로 설정 유지

### 4. 지도 연동
- OpenStreetMap 임베드
- Naver Map / Google Maps 원클릭 연결
- 팝업스토어 위치 확인

---

## 기술 스택

### Frontend
| 기술 | 버전 | 용도 |
|------|------|------|
| Next.js | 15 | React 프레임워크 (App Router) |
| React | 19 | UI 라이브러리 |
| TypeScript | 5 | 타입 안정성 |
| Tailwind CSS | 4 | 스타일링 |
| Supabase | - | 인증 (Google, Kakao OAuth) |

### Backend
| 기술 | 용도 |
|------|------|
| FastAPI | REST API 서버 |
| Upstage Solar Pro 2 | LLM (챗봇) |
| LangGraph | Agent 워크플로우 |
| SQLite | 팝업스토어 데이터 저장 |
| Python | 3.11 |

### 배포
| 서비스 | 용도 |
|--------|------|
| Vercel | Frontend 호스팅 |
| Railway | Backend 호스팅 |
| GitHub | 소스 코드 관리 |

---

## 시스템 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Vercel         │────▶│  Railway        │────▶│  Upstage API    │
│  (Next.js 15)   │     │  (FastAPI)      │     │  (Solar Pro 2)  │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Supabase       │     │  SQLite         │
│  (OAuth)        │     │  (팝업 데이터)   │
└─────────────────┘     └─────────────────┘
```

---

## 프로젝트 구조

```
wigtn-spot-finder/
├── frontend/                 # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/             # 페이지 라우팅 (App Router)
│   │   │   ├── (main)/      # 메인 레이아웃 그룹
│   │   │   │   ├── chat/    # AI 챗봇 페이지
│   │   │   │   ├── map/     # 지도 페이지
│   │   │   │   └── popups/  # 팝업 갤러리
│   │   │   └── page.tsx     # 랜딩 페이지
│   │   ├── components/      # 공통 UI 컴포넌트
│   │   ├── contexts/        # React Context (언어)
│   │   ├── features/        # 기능별 모듈
│   │   │   ├── chat/        # 챗봇 기능
│   │   │   ├── map/         # 지도 기능
│   │   │   └── popups/      # 팝업 기능
│   │   ├── lib/             # 유틸리티, API 클라이언트
│   │   └── types/           # TypeScript 타입 정의
│   └── package.json
│
├── src/                      # Python 백엔드
│   ├── api/                 # FastAPI 라우터
│   │   ├── main.py          # 앱 진입점
│   │   └── routes/          # API 엔드포인트
│   ├── agents/              # LangGraph 에이전트
│   ├── services/            # LLM 서비스
│   │   └── llm/             # Upstage Solar 클라이언트
│   └── tools/               # 외부 API 도구
│
├── railway.toml             # Railway 배포 설정
├── Procfile                 # 프로세스 정의
└── pyproject.toml           # Python 의존성
```

---

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서버 상태 확인 |
| POST | `/api/v1/chat` | 챗봇 메시지 전송 |
| POST | `/api/v1/chat/stream` | 스트리밍 챗봇 응답 (SSE) |

### 챗봇 API 요청 예시
```json
{
  "message": "성수동에서 패션 팝업 추천해줘",
  "language": "ko",
  "thread_id": "optional-thread-id"
}
```

### 챗봇 API 응답 예시
```json
{
  "response": "성수동에서 현재 진행 중인 패션 팝업을 추천해드릴게요...",
  "thread_id": "thread_abc123",
  "turn_number": 1,
  "stage": "recommend",
  "latency_ms": 1234.5
}
```

---

## 팝업스토어 데이터

**총 26개** 실제 성수동 팝업스토어 (2025년 1월 5주차 기준)

| 카테고리 | 개수 | 예시 |
|----------|------|------|
| 뷰티/코스메틱 | 6 | 온그리디언츠, 러븀, 토리든 |
| 패션 | 6 | 나비의 여정, 시에라디자인, 아디다스 |
| F&B | 3 | 뿌까x정지선, 맥캘란, 디저트젬스 |
| 아트/전시 | 5 | 월리를찾아라, 사랑의단상 |
| 엔터테인먼트 | 4 | 펍지성수, 금쪽같은내새끼 |
| 라이프스타일 | 5 | GMC, 레노버, NEXT WAVE |

---

## 로컬 개발 환경 설정

### 1. 백엔드 실행
```bash
cd wigtn-spot-finder

# 환경변수 설정
cp .env.example .env
# .env 파일에 UPSTAGE_API_KEY 추가

# 서버 실행
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 프론트엔드 실행
```bash
cd wigtn-spot-finder/frontend

# 의존성 설치
npm install

# 환경변수 설정
cp .env.example .env.local
# .env.local 파일 수정

# 개발 서버 실행
npm run dev
```

### 3. 접속
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 환경 변수

### Backend (.env)
```env
UPSTAGE_API_KEY=your-upstage-api-key
USE_UPSTAGE=true
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=https://wigtn-spot-finder-production.up.railway.app
```

---

## 배포 가이드

### Frontend (Vercel)
1. Vercel에 GitHub 레포 연결
2. Root Directory: `frontend`
3. Environment Variables 설정
4. 자동 배포

### Backend (Railway)
1. Railway CLI 설치: `brew install railway`
2. 로그인: `railway login`
3. 프로젝트 초기화: `railway init`
4. 배포: `railway up`
5. 도메인 생성: `railway domain`
6. Environment Variables 설정 (UPSTAGE_API_KEY)

---

## 스크린샷

### 메인 페이지
일본어 기본 UI, 언어 선택 버튼 우측 상단

### 팝업 갤러리
카테고리 필터, 검색, 카드 그리드 레이아웃

### AI 챗봇
Solar Pro 2 기반 실시간 스트리밍 응답

### 상세 페이지
이미지, 운영정보, 네이버맵/구글맵 버튼

---

## 기술적 특징

### 1. Next.js 15 App Router
- Server Components와 Client Components 분리
- 파일 기반 라우팅
- 레이아웃 중첩 구조

### 2. 다국어 처리
- React Context API로 전역 언어 상태 관리
- localStorage로 사용자 설정 유지
- 모든 페이지에서 일관된 언어 적용

### 3. LLM 스트리밍
- Server-Sent Events (SSE) 프로토콜
- 실시간 타이핑 효과
- 대화 컨텍스트 유지 (thread_id)

### 4. 모노레포 구조
- 하나의 저장소에서 Frontend/Backend 관리
- 공유 타입 정의 가능
- 통합 버전 관리

---

## 향후 계획

- [ ] Instagram 크롤링 자동화
- [ ] 실시간 팝업 정보 업데이트
- [ ] 사용자 리뷰/평점 기능
- [ ] PWA 지원
- [ ] 푸시 알림 (새 팝업 오픈 시)

---

## 만든 사람

**Harrison Kim**

---

## 링크

- **Live Demo**: https://frontend-blue-gamma-56.vercel.app
- **Backend API**: https://wigtn-spot-finder-production.up.railway.app
- **GitHub**: https://github.com/wigtn/wigtn-spot-finder

---

*이 문서는 Notion에 붙여넣기만 하면 바로 사용할 수 있습니다.*
