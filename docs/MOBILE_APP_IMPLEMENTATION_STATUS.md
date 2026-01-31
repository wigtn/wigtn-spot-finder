# WIGTN Spot Finder 모바일 앱 구현 현황

> 생성일: 2026-01-31
> PRD 문서: `docs/prd/PRD_mobile-app-deployment_ANALYSIS.md`

---

## 1. 완료된 작업

### 1.1 Monorepo 설정
- [x] `/package.json` - npm workspaces 설정 (frontend, mobile, shared)

### 1.2 Shared 패키지 (`/shared/`)
- [x] `package.json` - 패키지 설정
- [x] `tsconfig.json` - TypeScript 설정
- [x] `types/index.ts` - 공유 타입 정의
  - PopupStore, PopupSummary, PopupCategory
  - ChatMessage, ChatRequest, ChatResponse
  - User, Language, PushToken, PushNotification
  - ApiResponse, PaginatedResponse
- [x] `constants/index.ts` - 공유 상수
  - LANGUAGES, DEFAULT_LANGUAGE, STORAGE_KEYS
  - NAV_LABELS, CATEGORY_LABELS, CATEGORY_COLORS
  - UI_STRINGS, ERROR_MESSAGES (다국어)
- [x] `api/index.ts` - 공유 API 클라이언트
  - API 설정, 엔드포인트, fetch 래퍼
  - Popup/Chat/Push API 함수
- [x] `index.ts` - 모듈 re-export

### 1.3 Mobile 프로젝트 설정 (`/mobile/`)
- [x] `package.json` - Expo SDK 52 기반 의존성
- [x] `app.json` - Expo 설정
  - Bundle ID: `com.wigtn.spotfinder`
  - Scheme: `spotfinder`
  - iOS/Android 권한 설정
  - Universal Links / App Links 설정
- [x] `eas.json` - EAS Build 설정 (development, preview, production)
- [x] `tsconfig.json` - TypeScript 설정
- [x] `babel.config.js` - Babel 설정
- [x] `metro.config.js` - Metro bundler 설정 (monorepo 지원)
- [x] `.eslintrc.js` - ESLint 설정
- [x] `.gitignore` - Git ignore 설정

### 1.4 Mobile 라이브러리 (`/mobile/lib/`)
- [x] `storage.ts` - AsyncStorage/SecureStore 래퍼
- [x] `supabase.ts` - 모바일용 Supabase 클라이언트
- [x] `notifications.ts` - Expo 푸시 알림 설정
- [x] `api.ts` - API 클라이언트 (SSE 스트리밍 포함)

### 1.5 Mobile Context (`/mobile/contexts/`)
- [x] `language-context.tsx` - 언어 컨텍스트
- [x] `auth-context.tsx` - 인증 컨텍스트
- [x] `index.ts` - 모듈 re-export

### 1.6 Mobile App Layout
- [x] `app/_layout.tsx` - 루트 레이아웃 (일부)

---

## 2. 남은 작업

### 2.1 Mobile 화면 구현 (`/mobile/app/`)

#### Tab 화면
| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `(tabs)/_layout.tsx` | 탭 네비게이션 레이아웃 | 높음 |
| `(tabs)/index.tsx` | 팝업 갤러리 (메인) | 높음 |
| `(tabs)/map.tsx` | 지도 뷰 | 높음 |
| `(tabs)/chat.tsx` | AI 채팅 (Phase 2) | 낮음 |

#### 상세 화면
| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `popup/[id].tsx` | 팝업 상세 | 높음 |

#### 인증 화면
| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `auth/login.tsx` | 로그인 (Google/Kakao OAuth) | 높음 |
| `auth/callback.tsx` | OAuth 콜백 처리 | 높음 |

### 2.2 Mobile 컴포넌트 (`/mobile/components/`)

| 컴포넌트 | 설명 | 우선순위 |
|----------|------|----------|
| `PopupCard.tsx` | 팝업 카드 | 높음 |
| `PopupGrid.tsx` | 팝업 그리드 | 높음 |
| `CategoryFilter.tsx` | 카테고리 필터 | 높음 |
| `MapMarker.tsx` | 지도 마커 | 높음 |
| `LanguageSelector.tsx` | 언어 선택 | 중간 |
| `UserMenu.tsx` | 사용자 메뉴 | 중간 |
| `LoadingSkeleton.tsx` | 로딩 스켈레톤 | 중간 |

### 2.3 Mobile Hooks (`/mobile/hooks/`)

| 훅 | 설명 | 우선순위 |
|----|------|----------|
| `usePopups.ts` | 팝업 데이터 fetching | 높음 |
| `usePopupDetail.ts` | 팝업 상세 fetching | 높음 |
| `useChat.ts` | 채팅 훅 (Phase 2) | 낮음 |

### 2.4 Backend 엔드포인트 (`/src/api/routes/`)

| 파일 | 엔드포인트 | 설명 |
|------|-----------|------|
| `notifications.py` | `POST /api/v1/push/register` | 푸시 토큰 등록 |
| `notifications.py` | `POST /api/v1/push/send` | 푸시 알림 전송 |

### 2.5 Database 스키마

```sql
-- 푸시 토큰 테이블 (Supabase)
CREATE TABLE push_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  token TEXT NOT NULL UNIQUE,
  platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
  device_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 2.6 Frontend 추가 페이지

| 파일 | 설명 | 우선순위 |
|------|------|----------|
| `frontend/src/app/privacy/page.tsx` | 개인정보처리방침 | 높음 (앱스토어 필수) |
| `frontend/src/app/terms/page.tsx` | 이용약관 | 높음 (앱스토어 필수) |

### 2.7 설정 및 등록 작업

- [ ] Supabase OAuth 리다이렉트 URI 등록 (`spotfinder://auth/callback`)
- [ ] Google OAuth 리다이렉트 URI 등록
- [ ] Kakao OAuth 리다이렉트 URI 등록
- [ ] Google Maps API 키 발급 및 설정
- [ ] EAS 프로젝트 생성 및 projectId 설정
- [ ] Apple Developer 계정 설정
- [ ] Google Play Developer 계정 설정

---

## 3. 디렉토리 구조 (현재)

```
wigtn-spot-finder/
├── package.json                    # [완료] Monorepo 설정
├── frontend/                       # 기존 Next.js 웹 앱
├── mobile/                         # [진행중] Expo React Native 앱
│   ├── app.json                   # [완료]
│   ├── eas.json                   # [완료]
│   ├── package.json               # [완료]
│   ├── tsconfig.json              # [완료]
│   ├── babel.config.js            # [완료]
│   ├── metro.config.js            # [완료]
│   ├── app/
│   │   ├── _layout.tsx            # [완료]
│   │   ├── (tabs)/
│   │   │   ├── _layout.tsx        # [미완료]
│   │   │   ├── index.tsx          # [미완료]
│   │   │   ├── map.tsx            # [미완료]
│   │   │   └── chat.tsx           # [미완료] Phase 2
│   │   ├── popup/[id].tsx         # [미완료]
│   │   └── auth/
│   │       ├── login.tsx          # [미완료]
│   │       └── callback.tsx       # [미완료]
│   ├── components/                 # [미완료]
│   ├── hooks/                      # [미완료]
│   ├── contexts/
│   │   ├── index.ts               # [완료]
│   │   ├── language-context.tsx   # [완료]
│   │   └── auth-context.tsx       # [완료]
│   ├── lib/
│   │   ├── api.ts                 # [완료]
│   │   ├── storage.ts             # [완료]
│   │   ├── supabase.ts            # [완료]
│   │   └── notifications.ts       # [완료]
│   └── assets/                     # [미완료] 아이콘, 스플래시
├── shared/                         # [완료] 웹/모바일 공유 코드
│   ├── package.json               # [완료]
│   ├── tsconfig.json              # [완료]
│   ├── index.ts                   # [완료]
│   ├── types/index.ts             # [완료]
│   ├── constants/index.ts         # [완료]
│   └── api/index.ts               # [완료]
└── src/                            # 기존 Python 백엔드
    └── api/routes/
        └── notifications.py       # [미완료]
```

---

## 4. 다음 단계 권장 순서

1. **Mobile 화면 구현** - 탭 레이아웃, 갤러리, 상세 화면
2. **OAuth 인증** - 로그인/콜백 화면 및 딥링크 설정
3. **지도 뷰** - react-native-maps + Google Maps
4. **Backend 푸시 API** - 토큰 등록/전송 엔드포인트
5. **개인정보처리방침** - 앱스토어 제출 필수
6. **앱 에셋** - 아이콘, 스플래시 화면
7. **빌드 및 테스트** - EAS Build 프리뷰

---

## 5. 환경 변수 설정 필요

### Mobile (`mobile/.env`)
```env
EXPO_PUBLIC_API_URL=https://your-railway-app.railway.app
EXPO_PUBLIC_SUPABASE_URL=your-supabase-url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

### app.json 수정 필요 항목
- `ios.config.googleMapsApiKey`
- `android.config.googleMaps.apiKey`
- `extra.eas.projectId`
