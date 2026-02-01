# Popga AI Agent 고도화 계획

## 프로젝트 개요

**서비스명**: Popga (팝가)
**목적**: 일본인 관광객을 위한 성수동 팝업스토어 가이드 & AI 여행 플래너
**핵심 기술**: Upstage Solar Pro 3 기반 AI Agent

---

## 1. 현재 시스템 구조

### 1.1 기존 아키텍처
```
사용자 입력 → LangGraph ReAct Agent → Solar Pro → 도구 호출 → 응답
                                         ↓
                              ┌──────────┴──────────┐
                              ↓                     ↓
                        Naver Maps API       SQLite (팝업 DB)
```

### 1.2 현재 기능
- 성수동 팝업스토어 검색 (SQLite)
- 장소 검색 (Naver Maps API)
- 경로 안내 (Naver Directions API)
- 번역 (Papago API)
- 일정 생성 (로컬 로직)

### 1.3 현재 한계
| 구분 | 현재 상태 | 문제점 |
|------|----------|--------|
| Agent 패턴 | 기본 ReAct | 단순 도구 호출, 추론 없음 |
| 도구 선택 | LLM 임의 결정 | 상황 분석 없이 호출 |
| 사용자 이해 | 명시적 입력만 | 선호도 추론 불가 |
| 재계획 | 없음 | 상황 변화 대응 불가 |
| 개인화 | 없음 | 일회성 대화 |

---

## 2. Solar Pro 3 Agent 고도화 방향

### 2.1 목표 아키텍처
```
사용자 입력
    ↓
┌─────────────────────────────────────┐
│  Planning Agent (Solar Pro 3)       │
│  - 의도 분석                         │
│  - 정보 격차 파악                    │
│  - 실행 계획 수립                    │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Agentic Loop                       │
│  ┌─────────────────────────────────┐│
│  │ Execute → Evaluate → Re-plan   ││
│  │     ↑_______________________↓  ││
│  └─────────────────────────────────┘│
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Tool Orchestrator                  │
│  - 동적 도구 선택                    │
│  - 병렬/순차 실행 결정               │
└─────────────────┬───────────────────┘
                  ↓
    ┌─────────────┼─────────────┐
    ↓             ↓             ↓
 Popup DB    Naver APIs    Weather API
    ↓             ↓             ↓
    └─────────────┼─────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Response Synthesizer               │
│  - 결과 통합                         │
│  - 일본어 최적화                     │
│  - 개인화 반영                       │
└─────────────────────────────────────┘
```

### 2.2 핵심 개선 사항

#### A. Planning Agent 도입
Solar Pro 3의 Multi-step Reasoning 활용

**기존 방식**:
```
사용자: "성수동 카페 추천해줘"
Agent: [Naver Maps 호출] → 결과 5개 나열
```

**개선 방식**:
```
사용자: "성수동 카페 추천해줘"

Planning Agent:
  Step 1: 성수동 카페는 수백 개 → 선호도 파악 필요
  Step 2: 역질문 생성: "어떤 분위기를 선호하시나요?"

사용자: "조용하고 작업하기 좋은 곳"

Planning Agent:
  Step 3: "작업하기 좋은" = 콘센트, 와이파이, 넓은 테이블
  Step 4: Naver Maps 기본 정보 부족 → 팝업 DB 크로스체크
  Step 5: 현재 시간 고려 → 혼잡도 예측
  Step 6: 결과 합성 + 각 카페 장단점 설명
```

#### B. Context-Aware Tool Selection
상황에 따른 동적 도구 선택

| 사용자 요청 | 기존 | 개선 |
|------------|------|------|
| "비 오는 날 갈만한 곳" | place_search만 호출 | weather → 실내 장소 필터링 |
| "오늘 저녁 데이트" | place_search만 호출 | 현재시간 확인 → 영업시간 필터 → 분위기 추론 |
| "팝업 보고 카페도" | popup_search만 호출 | popup_search → 근처 카페 검색 → 동선 최적화 |

#### C. Preference Learning
대화에서 사용자 선호도 자동 추출

```
추출 대상:
- 분위기: 조용한 / 활기찬 / 로맨틱한
- 예산: 저렴 / 중간 / 고급
- 음식: 비건, 할랄, 알러지 등
- 활동: 쇼핑 / 전시 / 카페 / 맛집
- 이동: 도보 선호 / 대중교통 / 택시

저장 위치: Qdrant Vector DB (기존 인프라 활용)
```

#### D. Re-planning 기능
실시간 상황 대응

```
시나리오:
14:00 - 사용자에게 2시간 코스 추천
       카페(1시간) → 팝업(30분) → 산책(30분)

14:45 - 사용자가 아직 카페에 있음 (계획보다 15분 초과)

Re-planning Agent:
  - 팝업스토어 마감 시간 확인 (18:00)
  - 남은 시간으로 동선 재계산
  - Option A: 팝업 먼저 → 산책 축소
  - Option B: 팝업 스킵 → 산책 연장
  - 사용자에게 선택지 제시
```

---

## 3. 기술 구현 계획

### 3.1 새로운 모듈 구조

```
apps/api/src/agents/
├── business_agent.py        # 기존 (엔트리포인트)
├── observer_agent.py        # 기존 (모니터링)
│
├── planning/                # 🆕 Planning 모듈
│   ├── planning_agent.py    # 계획 수립
│   ├── intent_analyzer.py   # 의도 분석
│   └── plan_executor.py     # 계획 실행
│
├── reasoning/               # 🆕 Reasoning 모듈
│   ├── agentic_loop.py      # 실행-평가-재계획 루프
│   ├── evaluator.py         # 결과 평가
│   └── replanner.py         # 재계획
│
├── personalization/         # 🆕 개인화 모듈
│   ├── preference_extractor.py  # 선호도 추출
│   ├── user_profile.py          # 프로필 관리
│   └── recommendation.py        # 개인화 추천
│
└── orchestration/           # 🆕 도구 관리
    ├── tool_selector.py     # 동적 도구 선택
    └── response_synth.py    # 응답 합성
```

### 3.2 Solar Pro 3 활용 포인트

| 기능 | Solar Pro 3 활용 방식 |
|------|---------------------|
| 의도 분석 | Instruction Following (복잡한 요청 이해) |
| 계획 수립 | Multi-step Reasoning (단계별 추론) |
| 선호도 추출 | Structured Text Understanding |
| 결과 평가 | Complex Reasoning (충족도 판단) |
| 응답 생성 | 일본어 자연스러운 문장 생성 |

### 3.3 API 확장

```python
# 기존
POST /api/v1/chat
POST /api/v1/chat/stream

# 추가
POST /api/v1/agent/plan      # 계획 수립 (디버깅용)
GET  /api/v1/user/profile    # 사용자 프로필 조회
PUT  /api/v1/user/preference # 선호도 수동 설정
```

---

## 4. 일본인 관광객 특화 기능

### 4.1 언어 최적화
- 모든 응답 일본어 기본
- 장소명: 한국어 + 일본어 병기
- 주소: 로마자 표기 추가
- 메뉴/가격: 엔화 환산 표시

### 4.2 문화적 고려사항
- 현금/카드 결제 정보
- 영어 소통 가능 여부
- 일본인 친화적 장소 우선
- 할랄/비건 옵션 표시

### 4.3 관광객 시나리오
```
시나리오 1: 첫 방문
  - 성수동 개요 설명
  - 인기 팝업 Top 5
  - 추천 동선 (3시간 코스)

시나리오 2: 리피터
  - 이전 방문 기록 참조
  - 새로 오픈한 팝업 추천
  - 선호도 기반 맞춤 추천

시나리오 3: 시간 제한
  - "2시간밖에 없어요"
  - 효율적 동선 계산
  - 필수 방문지 우선순위
```

---

## 5. 예상 개선 효과

### 5.1 사용자 경험
| 지표 | 현재 | 목표 |
|------|------|------|
| 평균 대화 턴 수 | 5-7턴 | 3-4턴 |
| 추천 만족도 | - | 80%+ |
| 재방문율 | - | 40%+ |

### 5.2 기술 지표
| 지표 | 현재 | 목표 |
|------|------|------|
| 도구 호출 정확도 | 70% | 90%+ |
| 선호도 추론 정확도 | 없음 | 75%+ |
| 응답 생성 시간 | 3-5초 | 2-3초 |

---

## 6. 개발 우선순위

### Phase 1: 핵심 Agent 고도화 (1주)
- [ ] Planning Agent 구현
- [ ] Intent Analyzer 구현
- [ ] 기존 business_agent와 통합

### Phase 2: Agentic Loop (1주)
- [ ] Execute-Evaluate-Replan 루프
- [ ] 동적 도구 선택 로직
- [ ] 결과 평가 로직

### Phase 3: 개인화 (1주)
- [ ] Preference Extractor
- [ ] User Profile 저장 (Qdrant)
- [ ] 개인화 추천 로직

### Phase 4: 일본어 최적화 (1주)
- [ ] 프롬프트 일본어화
- [ ] 응답 템플릿
- [ ] 문화적 컨텍스트 추가

---

## 7. Upstage 앰버서더 제출 포인트

### 차별화 요소
1. **Solar Pro 3 Multi-step Reasoning 활용**
   - 단순 LLM 호출이 아닌 추론 기반 계획 수립

2. **Agentic Loop 패턴**
   - Execute → Evaluate → Re-plan 반복 구조

3. **Context-Aware Tool Selection**
   - 상황에 따른 동적 도구 선택

4. **실시간 Re-planning**
   - 상황 변화에 따른 계획 수정

5. **개인화 학습**
   - 대화에서 선호도 자동 추출 및 반영

### 데모 시나리오
```
[데모 시작]

User: "今日の午後、聖水洞に行きたいんですが"
      (오늘 오후에 성수동 가고 싶은데요)

Agent (Planning):
  - 현재 시간: 14:00
  - 날씨: 맑음
  - 선호도: 미파악 → 질문 필요

Agent: "聖水洞にはカフェ、ポップアップストア、ギャラリーなど
        色々ありますが、どんなところに興味がありますか？"
        (성수동에는 카페, 팝업스토어, 갤러리 등 다양한데
         어떤 곳에 관심 있으세요?)

User: "最近話題のポップアップストアが見たいです"
      (요즘 화제인 팝업스토어 보고 싶어요)

Agent (Tool Selection):
  - popup_search: 현재 운영 중인 팝업
  - 마감 시간 고려 (18:00 마감 많음)
  - 근처 카페 추가 추천

Agent: "現在3つの人気ポップアップが営業中です！
        ⚠️ Gentle Monsterは18時閉店なので、先に行くのがおすすめです。
        近くのカフェも一緒にご案内しましょうか？"

[데모 종료]
```

---

## 8. 참고 자료

- Upstage Solar Pro 3 Documentation
- LangGraph ReAct Agent Pattern
- Agentic AI Design Patterns (Anthropic)
