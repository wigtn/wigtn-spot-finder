# WIGTN Spot Finder 모바일 앱 구현 현황

> 생성일: 2026-01-31 | 업데이트: 2026-01-31 (C-3, C-5 해결)
> PRD 문서: `docs/prd/PRD_mobile-app-deployment_ANALYSIS.md`

---

## 1. 최근 백엔드 변경사항 (코드 리뷰 결과)

### 1.1 AI 에이전트 강화 (`src/agents/business_agent.py`)
- [x] 팝업 스토어 검색 도구 통합 (최우선 순위)
- [x] 성수동 특화 시스템 프롬프트 전면 개편
  - INIT: 성수동 팝업 가이드 (서울의 "브루클린")
  - INVESTIGATION: 사용자 관심사 파악 (패션, 뷰티, K-POP, 아트, 푸드)
  - PLANNING: 최적화된 팝업 투어 일정 구성
  - RESOLUTION: 실용 팁, 한국어 표현, 성수역 정보
- [x] 다국어 응답 지원 (일본어/영어/한국어)

### 1.2 벡터 데이터베이스 확장 (`src/db/qdrant/`)
- [x] `POPUP_COLLECTION = "seongsu_popups"` 추가
- [x] 팝업 컬렉션 인덱스 설정
  - `popup_id` (KEYWORD)
  - `category` (KEYWORD)
  - `is_active` (BOOL)
  - `period_start` / `period_end` (DATETIME)
- [x] 건강 체크에 팝업 컬렉션 통계 포함

### 1.3 보안 및 안정성 미들웨어 (`src/middleware/core/`)

#### 입력 검증 (`input_validation.py`)
- [x] 프롬프트 인젝션 탐지 패턴 23개
- [x] 최대 입력 길이 제한 (4000자)
- [x] 특수 문자 이스케이프 (script 태그, javascript: 프로토콜)
- [x] `InputValidationError` 커스텀 예외

#### 컨텍스트 요약 (`summarization.py`)
- [x] 4단계 폴백 전략:
  1. 전체 LLM 요약
  2. 축소 LLM 요약 (50%)
  3. 추출 기반 요약 (키워드)
  4. 단순 트렁케이션
- [x] 소프트/하드 토큰 한도 설정
- [x] 30초 타임아웃 처리

### 1.4 임베딩 서비스 (`src/services/memory/embeddings.py`)
- [x] 멀티 프로바이더 지원 (자동 폴백)
  1. Upstage (solar-embedding-1-large, 4096차원) - 기본
  2. VLLM (self-hosted)
  3. OpenAI (text-embedding-3-small/large)
  4. HuggingFace (sentence-transformers, 384차원) - 로컬 폴백
- [x] 코사인 유사도 계산
- [x] 동적 차원 감지

### 1.5 도구 확장 (`src/tools/`)

#### 번역 도구 (`i18n/translation.py`)
- [x] 언어 감지 기능 추가 (Papago)
- [x] 13개 언어 지원 확장
- [x] 팝업 스토어 전용 어휘 (한국어 발음 포함)
- [x] 일본어 → 한국어 관광 표현 매핑
- [x] 주요 도구: `translate()`, `get_korean_phrase()`, `get_popup_phrases()`

#### Naver 지도 도구 (`naver/`)
- [x] `directions.py` 개선
  - 성수동 랜드마크 추가 (성수역, 서울숲, 어니언 성수, 대림창고 등)
  - 비용 계산 (통행료, 유류비, 택시비 + USD 환산)
  - 단계별 내비게이션 안내
- [x] `geocoding.py` 신규 생성
  - 주소 → 좌표 변환 (Naver Cloud Platform API)
  - 도로명/지번 주소 모두 처리
  - URL 생성: 지도, 장소 검색, 길찾기

### 1.6 Instagram 스크래퍼 시스템 (신규: `src/scraper/`)

#### 전체 파이프라인
```
Instagram (@seongsu_bible)
    ↓ instaloader_client.py
포스트 수집 (이미지, 캡션, 해시태그)
    ↓ upstage_document_parser.py
이미지 텍스트 추출 (Upstage Document API)
    ↓ parser.py
LLM 파싱 (Solar Pro 2) → PopupStore 구조화
    ↓ naver/geocoding.py
주소 지오코딩
    ↓ embeddings.py
벡터 임베딩 생성
    ↓ sqlite/popup_store.py
SQLite 저장
```

#### 주요 컴포넌트
| 파일 | 역할 |
|------|------|
| `instaloader_client.py` | Instagram 포스트 수집 (Instaloader) |
| `parser.py` | LLM 기반 팝업 정보 추출 |
| `scheduler.py` | APScheduler 기반 주기적 스크래핑 |
| `run_scraper.py` | CLI 진입점 (`--once`, `--schedule`) |

#### Upstage Document Parser (`src/services/llm/upstage_document_parser.py`)
- [x] 이미지 텍스트 추출 API 클라이언트
- [x] 지수 백오프 재시도 (최대 3회)
- [x] 다중 이미지 동시 처리

---

## 2. 모바일 앱 구현 대기 항목

> **참고**: 이전에 생성한 `mobile/`, `shared/` 디렉토리는 롤백됨

### 2.1 프로젝트 설정 (Phase 1)

| 항목 | 파일 | 상태 |
|------|------|------|
| Monorepo 설정 | `/package.json` | 미구현 |
| Shared 패키지 | `/shared/*` | 미구현 |
| Expo 프로젝트 | `/mobile/app.json` | 미구현 |
| EAS Build | `/mobile/eas.json` | 미구현 |

### 2.2 Mobile 화면 구현 (Phase 2)

| 화면 | 파일 | 우선순위 |
|------|------|----------|
| 탭 레이아웃 | `app/(tabs)/_layout.tsx` | 높음 |
| 팝업 갤러리 | `app/(tabs)/index.tsx` | 높음 |
| 팝업 상세 | `app/popup/[id].tsx` | 높음 |
| 지도 뷰 | `app/(tabs)/map.tsx` | 높음 |
| OAuth 로그인 | `app/auth/login.tsx` | 높음 |
| AI 채팅 | `app/(tabs)/chat.tsx` | Phase 2 |

### 2.3 Backend 추가 작업

| 항목 | 상태 | 설명 |
|------|------|------|
| 푸시 알림 API | 미구현 | `POST /api/v1/push/register`, `/send` |
| 푸시 토큰 테이블 | 미구현 | PostgreSQL/Supabase 스키마 |
| 팝업 API 확장 | 부분 완료 | 카테고리 필터, 검색 API 필요 |

### 2.4 외부 설정 작업

- [ ] Supabase OAuth 리다이렉트 URI 등록 (`spotfinder://auth/callback`)
- [ ] Google/Kakao OAuth 모바일 리다이렉트 설정
- [ ] Google Maps API 키 발급
- [ ] Apple Developer 계정 ($99/년)
- [ ] Google Play Developer 계정 ($25 일회성)
- [ ] EAS 프로젝트 ID 생성

---

## 3. 현재 디렉토리 구조

```
wigtn-spot-finder/
├── frontend/                       # Next.js 웹 앱 (Vercel 배포)
├── src/                            # Python 백엔드 (Railway 배포)
│   ├── agents/
│   │   └── business_agent.py      # [수정됨] 팝업 특화 에이전트
│   ├── api/routes/                # FastAPI 라우트
│   ├── db/
│   │   ├── qdrant/               # [수정됨] 팝업 벡터 컬렉션
│   │   └── sqlite/               # SQLite 팝업 저장소
│   ├── middleware/core/
│   │   ├── input_validation.py   # [수정됨] 프롬프트 인젝션 방어
│   │   └── summarization.py      # [수정됨] 컨텍스트 요약
│   ├── scraper/                   # [신규] Instagram 스크래퍼
│   │   ├── instaloader_client.py
│   │   ├── parser.py
│   │   └── scheduler.py
│   ├── services/
│   │   ├── llm/
│   │   │   └── upstage_document_parser.py  # [신규]
│   │   └── memory/
│   │       └── embeddings.py      # [수정됨] 멀티 프로바이더
│   └── tools/
│       ├── i18n/translation.py    # [수정됨] 번역 확장
│       └── naver/
│           ├── directions.py      # [수정됨] 성수동 랜드마크
│           └── geocoding.py       # [신규] 지오코딩
├── scripts/
│   └── run_scraper.py             # [신규] 스크래퍼 CLI
├── app/                            # [신규] Monorepo 구조 준비
├── docs/
│   ├── MOBILE_APP_IMPLEMENTATION_STATUS.md  # 본 문서
│   └── prd/PRD_mobile-app-deployment_ANALYSIS.md
└── data/                           # SQLite DB (팝업 26개)
```

---

## 4. PRD Critical Issues 현황

| ID | 이슈 | 상태 | 해결 방안 |
|----|------|------|----------|
| C-1 | 푸시 알림 백엔드 미존재 | 🔴 미해결 | `src/api/routes/notifications.py` 생성 |
| C-2 | 푸시 토큰 저장소 미정의 | 🔴 미해결 | PostgreSQL 테이블 스키마 추가 |
| C-3 | Naver Maps SDK 미지원 | ✅ 해결됨 | 아래 참조 |
| C-4 | OAuth 리다이렉트 URI 미등록 | 🔴 미해결 | Supabase/Google/Kakao 설정 |
| C-5 | 개인정보처리방침 URL 미정의 | ✅ 해결됨 | `/privacy`, `/privacy/en`, `/privacy/ja`, `/terms` |

### C-3 해결: Naver Maps 라이브러리 선정

| 플랫폼 | 라이브러리 | 비고 |
|--------|-----------|------|
| **Web (Next.js)** | `react-naver-maps` | Naver Maps JS SDK 래핑 |
| **Mobile (Expo)** | `@mj-studio/react-native-naver-map` | 네이티브 SDK 래핑, Expo 지원 |

**API 키 발급**: Naver Cloud Platform → AI·NAVER API → Application 등록
- Web: `Web 서비스 URL` 등록
- Mobile: `Mobile Dynamic Map` 체크 + 패키지명 (`com.wigtn.spotfinder`)

---

## 5. 구현 우선순위 (권장)

### Phase 1: 백엔드 준비 (1주)
1. 푸시 알림 API 엔드포인트 구현
2. 푸시 토큰 DB 스키마 생성
3. 팝업 API CRUD 정리 (목록/상세/검색)

### Phase 2: 모바일 기반 (1주)
1. Monorepo 구조 설정 (`package.json` workspaces)
2. Shared 패키지 생성 (타입, 상수, API 클라이언트)
3. Expo 프로젝트 초기화

### Phase 3: 핵심 화면 (2주)
1. 탭 네비게이션 + 팝업 갤러리
2. 팝업 상세 화면
3. 지도 뷰 (`@mj-studio/react-native-naver-map`)

### Phase 4: 인증 & 알림 (1주)
1. OAuth 딥링크 설정 (Google/Kakao)
2. 푸시 알림 통합
3. 로그인/로그아웃 플로우

### Phase 5: 앱스토어 준비 (1주)
1. 개인정보처리방침/이용약관 페이지
2. 앱 아이콘, 스플래시 화면
3. EAS Build 및 TestFlight/내부 테스트

---

## 6. 환경 변수 설정 필요

### Backend 추가 (.env)
```env
# Expo Push Notifications
EXPO_ACCESS_TOKEN=your-expo-access-token
```

### Mobile (.env)
```env
EXPO_PUBLIC_API_URL=https://wigtn-spot-finder-production.up.railway.app
EXPO_PUBLIC_SUPABASE_URL=your-supabase-url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

---

## 7. 참고 링크

- **Frontend (Live)**: https://frontend-blue-gamma-56.vercel.app
- **Backend (Live)**: https://wigtn-spot-finder-production.up.railway.app
- **PRD 분석**: `docs/prd/PRD_mobile-app-deployment_ANALYSIS.md`
