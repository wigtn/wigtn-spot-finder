# 🎯 Spotfinder - AI 성수동 팝업스토어 가이드

> 외국인 관광객(특히 일본인)을 위한 AI 기반 성수동 팝업스토어 추천 서비스

---

## 📌 프로젝트 개요

| 항목 | 내용 |
|------|------|
| **프로젝트명** | Spotfinder (스팟파인더) |
| **목표 사용자** | 한국 방문 일본인 관광객 |
| **핵심 기능** | 팝업스토어 탐색, AI 챗봇 가이드, 지도 연동 |
| **개발 기간** | 2025년 1월 |
| **Live URL** | https://frontend-blue-gamma-56.vercel.app |

---

## ✨ 주요 기능

### 1️⃣ 팝업스토어 갤러리
- 성수동 26개 실제 팝업스토어 정보
- 카테고리별 필터링 (패션, 뷰티, 카페, 아트 등)
- 검색 기능
- 상세 정보 페이지 (운영시간, 위치, 설명)

### 2️⃣ AI 여행 가이드 챗봇
- **Upstage Solar Pro 2** LLM 연동
- 실시간 스트리밍 응답
- 맞춤형 팝업스토어 추천
- 다국어 대화 지원

### 3️⃣ 다국어 지원 (i18n)
- 🇯🇵 일본어 (기본)
- 🇺🇸 영어
- 🇰🇷 한국어
- 헤더에서 원클릭 언어 전환
- localStorage 저장으로 설정 유지

### 4️⃣ 지도 연동
- OpenStreetMap 임베드
- Naver Map / Google Maps 원클릭 연결
- 팝업스토어 위치 확인

---

## 🛠️ 기술 스택

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

### 배포
| 서비스 | 용도 |
|--------|------|
| Vercel | Frontend 호스팅 |
| Local | Backend (개발 환경) |

---

## 📁 프로젝트 구조

```
wigtn-spot-finder/
├── frontend/                 # Next.js 프론트엔드
│   ├── src/
│   │   ├── app/             # 페이지 라우팅
│   │   ├── components/      # 공통 컴포넌트
│   │   ├── contexts/        # 언어 컨텍스트
│   │   ├── features/        # 기능별 모듈
│   │   └── lib/             # 유틸리티, 데이터
│   └── package.json
│
├── src/                      # Python 백엔드
│   ├── api/                 # FastAPI 라우터
│   ├── agents/              # LangGraph 에이전트
│   ├── services/            # LLM 서비스
│   └── tools/               # 외부 API 도구
│
└── data/                     # SQLite 데이터베이스
```

---

## 📊 팝업스토어 데이터

**총 26개** 실제 성수동 팝업스토어 (2025년 1월 기준)

| 카테고리 | 개수 | 예시 |
|----------|------|------|
| 뷰티/코스메틱 | 6 | 온그리디언츠, 러븀, 토리든 |
| 패션 | 6 | 나비의 여정, 시에라디자인, 아디다스 |
| F&B | 3 | 뿌까x정지선, 맥캘란, 디저트젬스 |
| 아트/전시 | 5 | 월리를찾아라, 사랑의단상 |
| 엔터테인먼트 | 4 | 펍지성수, 금쪽같은내새끼 |
| 라이프스타일 | 5 | GMC, 레노버, NEXT WAVE |

---

## 🚀 실행 방법

### 1. 백엔드 실행
```bash
cd wigtn-spot-finder
uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 프론트엔드 실행
```bash
cd wigtn-spot-finder/frontend
npm install
npm run dev
```

### 3. 접속
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- 배포 버전: https://frontend-blue-gamma-56.vercel.app

---

## 🎨 스크린샷

### 메인 페이지
일본어 기본 UI, 언어 선택 버튼 우측 상단

### 팝업 갤러리
카테고리 필터, 검색, 카드 그리드 레이아웃

### AI 챗봇
Solar Pro 2 기반 실시간 스트리밍 응답

### 상세 페이지
이미지, 운영정보, 네이버맵/구글맵 버튼

---

## 💡 배운 점

1. **Next.js 15 App Router** - Server/Client Component 구분
2. **다국어 처리** - Context API + localStorage 활용
3. **LLM 연동** - Upstage Solar Pro 스트리밍 응답
4. **Vercel 배포** - 환경변수 관리, 빌드 최적화

---

## 🔮 향후 계획

- [ ] 백엔드 클라우드 배포 (Railway/Render)
- [ ] Instagram 크롤링 자동화
- [ ] 실시간 팝업 정보 업데이트
- [ ] 사용자 리뷰/평점 기능
- [ ] PWA 지원

---

## 🙋 만든 사람

**Harrison Kim**

---

*이 문서는 Notion에 붙여넣기만 하면 바로 사용할 수 있습니다.*
