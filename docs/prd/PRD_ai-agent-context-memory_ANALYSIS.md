# PRD Analysis Report

## 분석 대상
- **문서**: `docs/prd/PRD_ai-agent-context-memory.md`
- **버전**: 1.0
- **분석일**: 2026-01-16

---

## 요약

| 카테고리 | 발견 | Critical | Major | Minor |
|----------|------|----------|-------|-------|
| 완전성 | 8 | 2 | 4 | 2 |
| 실현가능성 | 5 | 1 | 3 | 1 |
| 보안 | 6 | 2 | 3 | 1 |
| 일관성 | 4 | 1 | 2 | 1 |
| **총계** | **23** | **6** | **12** | **5** |

---

## 상세 분석

### 🔴 Critical (즉시 수정 필요)

#### C-1. Rate Limiting 미정의
- **위치**: Section 4.3 Security, Section 5.6 API Specification
- **문제**: API에 Rate Limiting이 전혀 정의되지 않음
- **영향**:
  - DoS 공격에 취약
  - vLLM 서버 과부하로 전체 서비스 장애 유발 가능
  - 악의적 사용자가 GPU 리소스 독점 가능
- **개선안**:
  ```markdown
  ### 4.5 Rate Limiting

  | Endpoint | Limit | Window | Burst |
  |----------|-------|--------|-------|
  | POST /chat | 20 req | 1 min | 5 |
  | POST /chat/stream | 10 req | 1 min | 3 |
  | GET /conversations | 60 req | 1 min | 10 |

  **초과 시 응답**:
  - Status: 429 Too Many Requests
  - Header: `Retry-After: <seconds>`
  ```

#### C-2. Embedding 차원 불일치
- **위치**: Section 5.5 (Qdrant), Section 8 (Technology Stack)
- **문제**:
  - Qdrant 설정: `size=1024`
  - sentence-transformers `all-MiniLM-L6-v2`: 실제 차원 `384`
- **영향**: 런타임 에러 발생, Vector DB 삽입 실패
- **개선안**:
  ```python
  # 옵션 1: 모델에 맞게 Qdrant 수정
  vectors_config=VectorParams(
      size=384,  # all-MiniLM-L6-v2 dimension
      distance=Distance.COSINE
  )

  # 옵션 2: 더 큰 차원 모델 사용
  # BAAI/bge-large-en-v1.5 (1024) 또는
  # intfloat/multilingual-e5-large (1024)
  ```

#### C-3. Prompt Injection 방어 없음
- **위치**: Section 4.3 Security
- **문제**: 사용자 입력에 대한 Prompt Injection 방어 전략 없음
- **영향**:
  - System Prompt 우회 가능
  - 민감한 정보 유출 가능
  - Agent가 의도치 않은 동작 수행
- **개선안**:
  ```markdown
  ### 4.6 Input Sanitization

  1. **Prompt Injection 방어**:
     - 사용자 입력에서 시스템 프롬프트 패턴 탐지
     - XML/마크다운 태그 이스케이프
     - 입력 길이 제한 (4000자)

  2. **검증 Middleware**:
     - InputValidationMiddleware (before TurnMetadata)
     - 의심스러운 패턴 로깅 및 차단
  ```

#### C-4. 동시성 제어 미정의
- **위치**: Section 4.1 Performance
- **문제**: 동일 thread_id로 동시 요청 시 처리 방법 없음
- **영향**:
  - Race condition으로 인한 상태 불일치
  - 메시지 순서 보장 불가
  - 요약/메모리 저장 충돌
- **개선안**:
  ```markdown
  ### 4.7 Concurrency Control

  | 전략 | 설명 |
  |------|------|
  | Optimistic Locking | checkpoint_id 기반 충돌 감지 |
  | Request Queue | thread_id별 직렬화 처리 |
  | 429 Response | 동시 요청 시 거부 |

  **권장**: thread_id별 Redis Lock (TTL: 30초)
  ```

#### C-5. 요약 실패 시 Fallback 미정의
- **위치**: Section 5.4 Middleware Execution Flow
- **문제**: SummarizationMiddleware 실패 시 동작 정의 없음
- **영향**:
  - Context Window 초과로 LLM 호출 실패
  - 대화 중단
- **개선안**:
  ```markdown
  ### Summarization Fallback Strategy

  1. **1차 시도**: 동일 vLLM으로 요약
  2. **실패 시**: 단순 truncation (최근 N개만 유지)
  3. **로깅**: 요약 실패 이벤트 기록
  4. **알림**: 3회 연속 실패 시 운영자 알림
  ```

#### C-6. 토큰 카운팅 방법 미정의
- **위치**: Section 5.3, 5.4
- **문제**: "8000 tokens 초과 시" 언급하지만 카운팅 방법 없음
- **영향**:
  - 모델별 토크나이저 차이로 부정확한 계산
  - Context 초과 또는 비효율적 사용
- **개선안**:
  ```markdown
  ### 5.7 Token Counting Strategy

  | 모델 | 토크나이저 | 라이브러리 |
  |------|-----------|-----------|
  | Qwen2.5 | Qwen tokenizer | transformers |
  | Llama 3 | Llama tokenizer | transformers |

  **구현**:
  ```python
  from transformers import AutoTokenizer

  tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
  token_count = len(tokenizer.encode(text))
  ```

  **대안**: tiktoken 근사 (빠르지만 부정확할 수 있음)
  ```

---

### 🟡 Major (구현 전 수정 권장)

#### M-1. "최근 N개 메시지" N 값 미정의
- **위치**: Section 5.3, 5.4
- **문제**: "최근 N턴", "최근 N개 메시지" 언급하지만 구체적 값 없음
- **개선안**:
  ```markdown
  ### Context Window 구성 (구체화)

  | 구성 요소 | 토큰 | 메시지 수 |
  |----------|------|----------|
  | System Prompt | ~500 | 1 |
  | Retrieved Memory | ~1000 | 1-3 |
  | Previous Summary | ~1500 | 1 |
  | Recent Messages | ~3000 | **20개** |
  | Buffer | ~2000 | - |
  | **Total** | 8000 | - |
  ```

#### M-2. 메모리 정리 정책 미정의
- **위치**: 전체 (누락)
- **문제**: 오래된 대화, 요약, 엔티티 삭제 정책 없음
- **영향**:
  - DB 무한 증가
  - 검색 성능 저하
- **개선안**:
  ```markdown
  ### 6.1 Data Retention Policy

  | 데이터 | 보존 기간 | 삭제 방식 |
  |--------|----------|----------|
  | Checkpoints | 30일 | Batch delete |
  | Summaries | 90일 | Soft delete |
  | Entities | 90일 | Cascade |
  | Embeddings | 30일 | Qdrant TTL |

  **구현**: Daily cron job
  ```

#### M-3. vLLM Cold Start 미고려
- **위치**: Section 5.2
- **문제**: vLLM 서버 시작 시 모델 로딩 시간 고려 안됨
- **영향**:
  - 첫 요청 매우 느림 (수십 초)
  - Health check 실패
- **개선안**:
  ```markdown
  ### vLLM Warmup Strategy

  1. **Startup probe**: 모델 로딩 완료 대기 (timeout: 300s)
  2. **Warmup 요청**: 서버 시작 시 더미 추론 1회
  3. **Health check 분리**:
     - `/health/live`: 프로세스 생존
     - `/health/ready`: 추론 가능 상태
  ```

#### M-4. 요약 트리거 조건 불명확
- **위치**: Section 5.4, Section 10
- **문제**: "8000 tokens 초과 시" vs "토큰 기반 vs 턴 기반?" 충돌
- **개선안**:
  ```markdown
  ### Summarization Trigger (명확화)

  **Primary Trigger**: 토큰 기반
  - 임계값: 6000 tokens (8000의 75%)
  - 측정 시점: ContextTrimmingMiddleware

  **Secondary Trigger**: 턴 기반 (백업)
  - 임계값: 50턴 경과 시 강제 요약
  ```

#### M-5. Embedding 모델 다국어 지원 검증 필요
- **위치**: Section 8 Technology Stack
- **문제**: `all-MiniLM-L6-v2`는 영어 중심, 한국어 성능 미검증
- **개선안**:
  ```markdown
  ### Embedding 모델 선택 (재검토)

  | 모델 | 차원 | 한국어 | 추천 |
  |------|-----|-------|------|
  | all-MiniLM-L6-v2 | 384 | 낮음 | X |
  | paraphrase-multilingual-MiniLM-L12-v2 | 384 | 양호 | O |
  | intfloat/multilingual-e5-base | 768 | 우수 | O |
  | BAAI/bge-m3 | 1024 | 우수 | O (권장) |
  ```

#### M-6. API 인증 정책 불명확
- **위치**: Section 4.3 Security, Section 5.6
- **문제**: "API Key 기반 (optional)" - 구체적 정책 없음
- **개선안**:
  ```markdown
  ### 4.3.1 API 인증 정책

  | 환경 | 인증 | 방식 |
  |------|-----|------|
  | Development | 없음 | - |
  | Staging | 필수 | X-API-Key header |
  | Production | 필수 | X-API-Key + IP whitelist |

  **API Key 관리**:
  - 발급: 관리자 콘솔
  - 만료: 90일
  - 로테이션: 자동 알림
  ```

#### M-7. 토큰 임계값 불일치
- **위치**: Section 5.3 vs Section 5.4
- **문제**:
  - 5.3: "Total: ~6000 tokens"
  - 5.4: "8000 tokens 도달 시"
- **개선안**: 일관되게 수정
  ```markdown
  - Context Budget: 6000 tokens (기본값)
  - Summarization Trigger: 6000 tokens 도달 시
  - Hard Limit: 8000 tokens (안전 마진)
  ```

#### M-8. SQL Injection 방어 미언급
- **위치**: Section 4.3 Security
- **문제**: SQL Injection 방어 전략 없음
- **개선안**:
  ```markdown
  ### 4.3.2 SQL Injection 방어

  - **ORM 사용**: SQLAlchemy (parameterized queries)
  - **Raw SQL 금지**: 직접 SQL 문자열 조합 금지
  - **입력 검증**: thread_id 등 ID 필드 형식 검증
  ```

#### M-9. Middleware 순서 근거 미설명
- **위치**: Section 5.4
- **문제**: Middleware 실행 순서의 이유가 설명되지 않음
- **개선안**:
  ```markdown
  ### Middleware 순서 근거

  1. **TurnMetadata**: 모든 처리 전 메타데이터 필요
  2. **MemoryRetrieval**: 관련 과거 정보를 먼저 가져옴
  3. **ContextTrimming**: 검색된 메모리 포함하여 토큰 계산
  4. **Summarization**: Trimming 후 필요시 요약
  5. **DynamicPrompt**: 최종 context 기반 프롬프트 생성
  6. **EntityExtraction**: 응답 완료 후 처리 (after_model)
  ```

---

### 🟢 Minor (개선 제안)

#### m-1. User Story 추가 필요
- **위치**: Section 2
- **문제**: 개발자/운영자 외 실제 최종 사용자 시나리오 없음
- **개선안**: End-user 관점 User Story 추가

#### m-2. Error Code 불완전
- **위치**: Section 5.6
- **문제**: 모든 에러 케이스가 정의되지 않음
- **개선안**:
  ```markdown
  | Status | Code | Message |
  |--------|------|---------|
  | 401 | UNAUTHORIZED | API key invalid |
  | 404 | NOT_FOUND | Conversation not found |
  | 408 | TIMEOUT | Request timeout |
  | 429 | RATE_LIMITED | Too many requests |
  ```

#### m-3. 로깅 레벨 미정의
- **위치**: Section 4.3 Security
- **문제**: "민감 정보 마스킹" 언급하지만 구체적 정책 없음
- **개선안**:
  ```markdown
  ### 로깅 정책

  | 레벨 | 내용 | 마스킹 대상 |
  |------|-----|-----------|
  | INFO | 요청/응답 메타데이터 | 메시지 내용 |
  | DEBUG | 전체 내용 | 개인정보 패턴 |
  | ERROR | 에러 상세 | API keys |
  ```

#### m-4. 모니터링 메트릭 상세화 필요
- **위치**: Section 7 Success Metrics
- **문제**: 메트릭은 정의되었으나 수집 방법이 없음
- **개선안**: Prometheus 메트릭 상세 정의 추가

#### m-5. CORS 정책 미정의
- **위치**: Section 4.3 Security
- **문제**: Cross-Origin 정책 없음
- **개선안**:
  ```markdown
  ### CORS 설정

  | 환경 | Allowed Origins |
  |------|-----------------|
  | Dev | * |
  | Staging | *.staging.example.com |
  | Prod | app.example.com |
  ```

---

## 누락된 요구사항

| ID | 요구사항 | 권장 우선순위 | 영향도 |
|----|---------|--------------|-------|
| NEW-1 | Rate Limiting 정책 | P0 | 보안 |
| NEW-2 | 동시성 제어 (thread_id별) | P0 | 안정성 |
| NEW-3 | Prompt Injection 방어 | P0 | 보안 |
| NEW-4 | Data Retention 정책 | P1 | 운영 |
| NEW-5 | API Key 관리 정책 | P1 | 보안 |
| NEW-6 | vLLM Warmup/Readiness | P1 | 성능 |
| NEW-7 | 입력 길이 제한 명시 | P1 | 안정성 |
| NEW-8 | Graceful Shutdown 처리 | P2 | 운영 |

---

## 리스크 매트릭스 (확장)

| 리스크 | 발생 확률 | 영향도 | 현재 대응 | 추가 필요 |
|--------|----------|--------|----------|----------|
| DoS 공격 | 높음 | 높음 | 없음 | Rate Limiting |
| Prompt Injection | 높음 | 높음 | 없음 | Input Sanitization |
| 요약 품질 저하 | 중간 | 중간 | Prompt 최적화 | Quality metrics |
| Race Condition | 중간 | 높음 | 없음 | Locking 구현 |
| 토큰 카운트 오차 | 중간 | 중간 | 없음 | 정확한 토크나이저 |
| Embedding 불일치 | 높음 | 높음 | 없음 | 차원 통일 |
| Cold Start 지연 | 낮음 | 중간 | 없음 | Warmup 전략 |

---

## 권장 조치

### 즉시 조치 (Critical) - 구현 시작 전 필수

1. ❗ **Rate Limiting 정의** (C-1)
   - API 엔드포인트별 제한 설정
   - 429 응답 형식 정의

2. ❗ **Embedding 차원 통일** (C-2)
   - 모델과 Qdrant 설정 일치시키기
   - 다국어 모델로 변경 검토 (bge-m3)

3. ❗ **Prompt Injection 방어** (C-3)
   - InputValidationMiddleware 추가
   - 위험 패턴 정의

4. ❗ **동시성 제어 정의** (C-4)
   - thread_id별 Lock 전략
   - 동시 요청 처리 방법

5. ❗ **Fallback 전략 정의** (C-5, C-6)
   - 요약 실패 시 동작
   - 토큰 카운팅 방법 명시

### 구현 전 조치 (Major)

1. ⚠️ Context 파라미터 구체화 (M-1)
2. ⚠️ Data Retention 정책 추가 (M-2)
3. ⚠️ vLLM Readiness 전략 추가 (M-3)
4. ⚠️ Embedding 모델 재선정 (M-5)
5. ⚠️ Middleware 순서 근거 문서화 (M-9)

### 가능하면 조치 (Minor)

1. 💡 End-user Story 추가 (m-1)
2. 💡 Error Code 완성 (m-2)
3. 💡 로깅 정책 상세화 (m-3)
4. 💡 CORS 정책 추가 (m-5)

---

## 수정된 Technology Stack 제안

| Component | 현재 | 권장 | 이유 |
|-----------|------|------|------|
| Embedding | all-MiniLM-L6-v2 (384) | **BAAI/bge-m3** (1024) | 다국어, 고성능 |
| Qdrant Dimension | 1024 | **1024** (유지) | bge-m3와 일치 |
| Token Counter | 미정의 | **transformers** | 정확한 카운팅 |
| Rate Limiter | 없음 | **Redis + slowapi** | 분산 환경 지원 |
| Concurrency | 없음 | **Redis Lock** | thread_id별 제어 |

---

## 다음 단계

### PRD 수정 완료 후

Critical 이슈 6개 모두 해결되면 구현을 시작해도 됩니다.

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Critical 이슈 해결 후                                    │
│                                                             │
│  → `/implement ai-agent-context-memory`                     │
│  → Task Plan 기반 Phase별 자동 실행                          │
│                                                             │
│  💡 Major 이슈는 구현 중 병행 수정 가능                       │
└─────────────────────────────────────────────────────────────┘
```

---

**Analysis by**: AI Assistant
**Analysis Date**: 2026-01-16
