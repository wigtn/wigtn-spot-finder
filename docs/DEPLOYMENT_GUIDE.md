# AI Agent 배포 & 운영 가이드

## 1. 사전 준비 (Pre-Deployment Checklist)

### 1.1 인프라 준비
- [ ] AWS / GCP / Azure 계정 및 권한 확인
- [ ] PostgreSQL 버전 확인 (최소 12.0+, pgvector 설치)
- [ ] Vector DB 선택 및 설정 (Qdrant / Pinecone)
- [ ] Redis 클러스터 (선택사항, 캐싱용)
- [ ] Docker & Docker Compose 설치 확인

### 1.2 API 키 & 서비스
- [ ] OpenAI API key 발급 및 테스트
  ```bash
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY"
  ```
- [ ] LangSmith API key 발급 (모니터링용)
- [ ] Sentry API key (에러 추적용, 선택사항)

### 1.3 네트워크
- [ ] VPC/네트워크 설정 (보안 그룹)
- [ ] 로드 밸런서 설정 (Nginx / AWS ALB)
- [ ] SSL 인증서 설정
- [ ] CDN (CloudFront) 설정 (선택사항)

---

## 2. 로컬 개발 환경 설정

### 2.1 환경 변수 파일 생성

```bash
# .env 파일 생성
cat > .env << EOF
# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://agent_user:secure_password_change_me@localhost:5432/agent_db

# Vector DB
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=qdrant_api_key_change_me

# Redis (선택)
REDIS_URL=redis://localhost:6379/0

# LangSmith
LANGSMITH_API_KEY=ls-...
LANGSMITH_PROJECT=agent_chatbase

# App
LOG_LEVEL=DEBUG
ENVIRONMENT=development
EOF

chmod 600 .env
```

### 2.2 Docker Compose로 스택 시작

```bash
# 1. 이미지 빌드
docker-compose build

# 2. 컨테이너 시작
docker-compose up -d

# 3. 헬스 체크
docker-compose ps
# 모든 서비스가 "healthy"여야 함

# 4. 로그 확인
docker-compose logs -f agent

# 5. DB 초기화 확인
docker-compose exec postgres psql -U agent_user -d agent_db -c "\dt"
```

### 2.3 로컬 테스트

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. Agent 테스트
python agent_implementation_example.py

# 3. API 서버 시작 (src/main.py 필요)
uvicorn src.main:app --reload

# 4. API 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "session_id": "test_session",
    "message": "Hello, I need help with my order"
  }'
```

---

## 3. 프로덕션 배포

### 3.1 클라우드 배포 (AWS 예시)

```bash
# 1. ECR 이미지 빌드 & 푸시
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <your-ecr-uri>

docker build -t agent:latest .
docker tag agent:latest <ecr-uri>/agent:latest
docker push <ecr-uri>/agent:latest

# 2. RDS 생성 (PostgreSQL with pgvector)
aws rds create-db-instance \
  --db-instance-identifier agent-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --master-username agent_user \
  --master-user-password "$(openssl rand -base64 32)" \
  --allocated-storage 100 \
  --enable-cloudwatch-logs-exports postgresql

# 3. Qdrant 클러스터 (또는 Pinecone 사용)
# Qdrant Cloud 또는 self-hosted EKS cluster

# 4. ECS 작업 정의 생성
aws ecs register-task-definition \
  --family agent-task \
  --network-mode awsvpc \
  --container-definitions '[{
    "name": "agent",
    "image": "<ecr-uri>/agent:latest",
    "portMappings": [{"containerPort": 8000}],
    "environment": [
      {"name": "DATABASE_URL", "value": "postgresql://..."},
      {"name": "OPENAI_API_KEY", "value": "..."}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/agent",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]'

# 5. ECS 서비스 생성
aws ecs create-service \
  --cluster agent-cluster \
  --service-name agent-service \
  --task-definition agent-task:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-...],securityGroups=[sg-...]}"
```

### 3.2 Kubernetes 배포 (K8s 예시)

```bash
# 1. Namespace 생성
kubectl create namespace ai-agents

# 2. Secrets 생성
kubectl create secret generic agent-secrets \
  --from-literal=OPENAI_API_KEY=sk-... \
  --from-literal=DATABASE_URL=postgresql://... \
  -n ai-agents

# 3. Deployment
cat > deployment.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent
  namespace: ai-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent
  template:
    metadata:
      labels:
        app: agent
    spec:
      containers:
      - name: agent
        image: <registry>/agent:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: agent-secrets
        env:
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
EOF

kubectl apply -f deployment.yaml

# 4. Service 생성
kubectl expose deployment agent \
  --type=LoadBalancer \
  --port=80 \
  --target-port=8000 \
  -n ai-agents

# 5. HPA (Auto Scaling)
kubectl autoscale deployment agent \
  --min=3 --max=10 \
  --cpu-percent=80 \
  -n ai-agents
```

---

## 4. 성능 튜닝

### 4.1 Database 최적화

```sql
-- Connection pooling 확인
SHOW max_connections;  -- 기본값 100, 필요 시 증가

-- Shared buffers (메모리의 25%)
-- max_wal_size (메모리의 25%)
-- checkpoint_completion_target = 0.9

-- 인덱스 확인
EXPLAIN ANALYZE SELECT * FROM conversation_metadata 
WHERE user_id = 'user_123' AND timestamp > NOW() - INTERVAL '7 days';

-- 통계 업데이트
ANALYZE;

-- Vacuum (자동으로 실행되지만, 큰 데이터셋에는 수동 실행)
VACUUM ANALYZE conversation_metadata;
```

### 4.2 Agent 성능 최적화

```python
# 1. Summarization trigger 조정
# 너무 자주: 오버헤드, 정보 손실
# 너무 드물게: Context explosion
# 권장: 70-80% context window

summarization = SummarizationMiddleware(
    model="openai:gpt-4o-mini",  # 빠름, 저비용
    trigger=("fraction", 0.75),  # 75% 도달 시
    keep=("messages", 50),
)

# 2. Memory retrieval 성능
# - Top-K 조정: 3~5가 일반적
# - Similarity threshold: 0.6~0.8
# - Batch retrieval (여러 쿼리 한 번에)

# 3. Tool 실행 병렬화
# create_react_agent는 native하게 병렬 tool 실행 지원
# (동시에 여러 tool을 호출할 수 있음)

# 4. Caching 활용
# - Prompt caching (Claude/GPT-4 지원)
# - Response caching (Redis)
# - Embedding caching
```

### 4.3 비용 최적화

```python
# 1. Model 선택
# Cheap: gpt-3.5-turbo
# Balanced: gpt-4o-mini (권장)
# Expensive: gpt-4o, gpt-4-turbo

# 2. Summarization model
# 별도 비용 모델 선택
model="openai:gpt-4o-mini"  # summarization 전용

# 3. Embedding model
# text-embedding-3-small: $0.02 / 1M tokens (권장)
# text-embedding-3-large: $0.13 / 1M tokens

# 4. Token 최소화
# - Context trimming
# - 불필요한 tool 제거
# - 시스템 프롬프트 최적화

# 5. Batch 처리
# - 여러 사용자 요청을 한 번에 처리
# - 비동기 처리로 parallelism 극대화
```

---

## 5. 모니터링 & 로깅

### 5.1 Prometheus 메트릭

```python
# src/monitoring.py 예시

from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
agent_calls = Counter('agent_calls_total', 'Total agent calls')
token_usage = Counter('token_usage_total', 'Total tokens used')
context_window_usage = Histogram('context_window_percent', 'Context usage %')
summarization_latency = Histogram('summarization_latency_seconds', 'Summarization time')
model_latency = Histogram('model_latency_seconds', 'Model call latency')
memory_retrieval_latency = Histogram('memory_retrieval_latency_seconds', 'Memory search time')

# Custom metric recording
@before_model
async def record_metrics(request: ModelRequest, handler):
    start = time.time()
    
    agent_calls.inc()
    msg_count = len(request.state["messages"])
    token_count = estimate_tokens(request.state["messages"])
    token_usage.inc(token_count)
    context_window_usage.observe((token_count / 128000) * 100)  # GPT-4 window
    
    response = await handler(request)
    
    duration = time.time() - start
    model_latency.observe(duration)
    
    return response
```

### 5.2 LangSmith 통합

```python
# 자동으로 모든 agent 호출이 trace됨
# LangSmith Dashboard에서 확인 가능

# Custom feedback (선택)
from langsmith import Client

client = Client()

# Agent 실행 후
result = agent.invoke(...)

# Feedback 기록
client.create_feedback(
    run_id=result.get("run_id"),
    key="quality",
    score=4.5,  # 1-5
    comment="Good response",
)
```

### 5.3 Grafana 대시보드 설정

```yaml
# grafana/dashboards/agent-metrics.json
{
  "dashboard": {
    "title": "Agent Metrics",
    "panels": [
      {
        "title": "Agent Calls",
        "targets": [
          {
            "expr": "rate(agent_calls_total[5m])"
          }
        ]
      },
      {
        "title": "Average Context Window Usage",
        "targets": [
          {
            "expr": "avg(context_window_percent)"
          }
        ]
      },
      {
        "title": "Model Latency P99",
        "targets": [
          {
            "expr": "histogram_quantile(0.99, model_latency_seconds_bucket)"
          }
        ]
      },
      {
        "title": "Token Usage (Hourly)",
        "targets": [
          {
            "expr": "increase(token_usage_total[1h])"
          }
        ]
      }
    ]
  }
}
```

---

## 6. 트러블슈팅

### 문제 1: Context Window Explosion
**증상**: 대화가 길어질수록 응답이 느려짐

**해결책**:
```python
# 1. Summarization trigger 낮추기
trigger=("fraction", 0.6)  # 60%로 낮춤

# 2. Keep message count 줄이기
keep=("messages", 20)  # 30에서 20으로

# 3. Memory retrieval 검증
# → semantic search가 제대로 작동하는지 확인
```

### 문제 2: 높은 비용
**증상**: API 비용이 예상보다 높음

**해결책**:
```python
# 1. Cheap model로 변경
model="openai:gpt-4o-mini"  # gpt-4-turbo에서 변경

# 2. Summarization 최적화
model="openai:gpt-3.5-turbo"  # summarization용

# 3. Token 사용 추적
from langchain.callbacks import OpenAICallbackHandler

with OpenAICallbackHandler() as cb:
    result = agent.invoke(...)
    print(f"Tokens: {cb.total_tokens}")
    print(f"Cost: ${cb.total_cost}")
```

### 문제 3: 요약 품질 저하
**증상**: 요약 후 중요 정보 손실

**해결책**:
```python
# 1. 더 나은 summarization model
model="openai:gpt-4-turbo"

# 2. Custom extraction 추가
@after_model
async def extract_critical_info(...):
    # 요약 전에 중요 정보 추출
    entities = extract_entities(...)
    await store.put(..., value=entities)

# 3. 더 자주 요약 (정보 손실 최소화)
trigger=("tokens", 5000)  # 10000에서 5000으로
```

### 문제 4: Memory Retrieval 느림
**증상**: Semantic search가 병목

**해결책**:
```python
# 1. Vector DB 최적화
# - Index 재구성: REINDEX
# - Connection pooling 확인

# 2. Embedding model 변경
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"  # 빠르고 저렴
)

# 3. Cache 추가
from langchain.cache import RedisCache
from redis import Redis

langchain.llm_cache = RedisCache(redis_client=Redis())
```

---

## 7. 보안 체크리스트

- [ ] API key는 환경 변수로만 관리 (hardcoded 금지)
- [ ] Database 암호화 (SSL/TLS)
- [ ] VPC 내 database 접근만 허용
- [ ] Rate limiting 설정 (DDoS 방지)
- [ ] Input validation & sanitization
- [ ] SQL Injection 방지 (ORM 사용)
- [ ] CORS 설정 (필요한 도메인만)
- [ ] 정기적인 보안 감사 (OWASP)

---

## 8. 운영 SOP

### 일일 (Daily)
- [ ] Agent 성능 모니터링 (Grafana)
- [ ] 에러율 확인 (LangSmith / Sentry)
- [ ] API 비용 추적

### 주간 (Weekly)
- [ ] Database 통계 업데이트 (`ANALYZE`)
- [ ] Slow query log 검토
- [ ] 사용자 피드백 분석

### 월간 (Monthly)
- [ ] Full backup 검증
- [ ] Cost analysis & optimization
- [ ] Model 벤치마크 (새 모델 비교)
- [ ] 의존성 업데이트 검토 (`pip outdated`)

---

## 9. 참고 명령어

```bash
# Docker 상태 확인
docker-compose ps
docker-compose logs agent

# Database 접근
docker-compose exec postgres psql -U agent_user -d agent_db

# Vector DB 상태
curl http://localhost:6333/health

# Agent API 테스트
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Performance 프로파일링
python -m cProfile -s cumtime agent_implementation_example.py

# Memory 사용량 추적
python -m memory_profiler agent_implementation_example.py
```

---

**Last Updated**: 2025-01-16  
**Version**: 1.0
