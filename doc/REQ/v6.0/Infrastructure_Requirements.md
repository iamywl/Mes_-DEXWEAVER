# DEXWEAVER MES v6.0 — 인프라 요구사항 정의서

> **버전**: v6.0
> **작성일**: 2026-03-03
> **작성 근거**: 아키텍처 분석 보고서 (`doc/ARCH.md`), CI/CD 검토 보고서 (`doc/CICD_REVIEW.md`), 한계점 분석 보고서 (`research/limitations/`)
> **관련 문서**: `Requirements_Specification.md`, `Functional_Specification.md`, `DatabaseSchema.md`
>
> | 대상 | 범위 |
> |------|------|
> | 개발 환경 | Docker Compose 기반 로컬 개발 환경 (PostgreSQL, Redis, MQTT, API, Frontend) |
> | Kubernetes 운영 환경 | 프로덕션 매니페스트 (Deployment, HPA, Ingress, Secret, PVC) |
> | CI/CD | GitHub Actions 기반 빌드/테스트/배포 파이프라인 |
> | 모니터링 | Prometheus + Grafana 기반 옵저버빌리티 스택 |
> | 마이그레이션 | Alembic 기반 DB 스키마 버전 관리 |

---

## 1. 인프라 요구사항 개요

### 1.1 As-Is vs To-Be 비교

| 항목 | As-Is (v4.0) | To-Be (v6.0) | 관련 NFR |
|:----:|:------------:|:------------:|:--------:|
| **배포 방식** | ConfigMap 소스 마운트 + `pip install` 매 부팅 | Docker 이미지 빌드 + Registry Push | NFR-002 |
| **컨테이너 이미지** | `python:3.9-slim` (범용) | 멀티스테이지 빌드 커스텀 이미지 (Python 3.11) | NFR-002 |
| **DB 드라이버** | psycopg2 (동기) | asyncpg (비동기) + 커넥션 풀링 | NFR-006 |
| **캐싱** | 없음 | Redis 7 (API 응답, 세션, AI 모델 메타데이터) | NFR-009 |
| **MQTT 브로커** | 없음 | Eclipse Mosquitto (센서 데이터 수집) | REQ-042 |
| **DB 마이그레이션** | `init.sql` 수동 관리 | Alembic 자동 마이그레이션 | NFR-005 |
| **스케일링** | `replicas: 1` 고정 | HPA 오토스케일링 (min:2, max:8) | NFR-002 |
| **CI/CD** | Jenkins (ConfigMap 방식, 불일치) | GitHub Actions (이미지 빌드 + 롤링 배포) | NFR-002 |
| **모니터링** | 없음 | Prometheus + Grafana + Alert Rules | 신규 |
| **보안** | JWT Secret 하드코딩, Rate Limit 없음 | K8s Secret, slowapi Rate Limit, TLS | NFR-007 |
| **Service 노출** | NodePort (30173, 30461, 30080) | ClusterIP + Ingress (TLS 지원) | 신규 |
| **네트워크 정책** | 없음 (Cilium 설치만 됨) | Cilium NetworkPolicy 적용 | NFR-007 |

### 1.2 To-Be 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Kubernetes Cluster (Production)                         │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐       │
│  │                        Ingress Controller (Cilium)                    │       │
│  │                    TLS Termination (Let's Encrypt)                    │       │
│  │         mes.example.com ──→ Frontend / API / Grafana                  │       │
│  └─────────────┬──────────────────┬──────────────────┬──────────────────┘       │
│                │ /                │ /api/*           │ /grafana                  │
│                ▼                  ▼                  ▼                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │  mes-frontend    │  │   mes-api        │  │   Grafana        │                │
│  │  nginx:alpine    │  │   Python 3.11    │  │   :3000           │                │
│  │  (React/Vite)    │  │   FastAPI+Uvicorn│  │                   │                │
│  │  HPA: 2~4        │  │   HPA: 2~8       │  │   replicas: 1     │                │
│  └─────────────────┘  └────────┬─────────┘  └────────┬──────────┘                │
│                                │                     │                           │
│           ┌────────────────────┼─────────────────────┘                           │
│           │                    │                                                  │
│           ▼                    ▼                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   PostgreSQL 15  │  │    Redis 7       │  │  Mosquitto MQTT  │                 │
│  │   :5432          │  │    :6379         │  │  :1883 / :9883   │                 │
│  │   PVC: 20Gi      │  │    PVC: 2Gi      │  │  (MQTT / WS)     │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
│           │                                                                      │
│  ┌────────┴────────┐                                                             │
│  │   Prometheus     │──── scrape ──→ mes-api /metrics                            │
│  │   :9090          │──── scrape ──→ postgres-exporter                            │
│  │   PVC: 10Gi      │──── scrape ──→ redis-exporter                              │
│  └─────────────────┘                                                             │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐     │
│  │                    Cilium eBPF CNI + NetworkPolicy                       │     │
│  └─────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
                │
    ┌───────────┴───────────┐
    │  GitHub Actions CI/CD  │
    │  Build → Test → Push   │
    │  → Deploy (Kustomize)  │
    └────────────────────────┘
```

### 1.3 Phase 별 인프라 연계

| Phase | 기간 | 인프라 변경 사항 | 관련 요구사항 |
|:-----:|:----:|:----------------|:-------------|
| **Phase 1** | 3개월 | Docker 이미지 빌드 전환, Redis 도입, Alembic 마이그레이션, HPA 구성, CI/CD 파이프라인, 모니터링 스택 | NFR-001~005, REQ-035~039 |
| **Phase 2** | 6개월 | MQTT 브로커 추가, asyncpg 전환, Redis 캐싱 고도화, 테스트 자동화 강화 | NFR-006~010, REQ-040~044 |
| **Phase 3** | 12개월 | ERP/OPC-UA 연동 인프라, 감사 추적 DB 파티셔닝, TLS 인증서 자동 갱신 | REQ-045~049 |

---

## 2. 개발 환경 (Docker Compose) — To-Be

### 2.1 docker-compose.yml

```yaml
# docker-compose.yml — DEXWEAVER MES v6.0 개발 환경
# 사용법: docker compose up -d
# 중지:   docker compose down
# 초기화: docker compose down -v (볼륨 포함 삭제)
# 모니터링 포함: docker compose --profile monitoring up -d
# 전체(tools+monitoring): docker compose --profile tools --profile monitoring up -d

version: "3.8"

x-common-env: &common-env
  TZ: Asia/Seoul

services:
  # ─────────────────────────────────────────────
  # 1. PostgreSQL 15 — 메인 데이터베이스
  # ─────────────────────────────────────────────
  mes-db:
    image: postgres:15-alpine
    container_name: mes-postgres
    restart: unless-stopped
    ports:
      - "5433:5432"
    environment:
      <<: *common-env
      POSTGRES_USER: ${POSTGRES_USER:-mes_admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-mes_secure_2026!}
      POSTGRES_DB: ${POSTGRES_DB:-mes_db}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-mes_admin} -d ${POSTGRES_DB:-mes_db}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - mes-network
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 256M

  # ─────────────────────────────────────────────
  # 2. Redis 7 — 캐싱, 세션, AI 모델 메타데이터
  # ─────────────────────────────────────────────
  mes-redis:
    image: redis:7-alpine
    container_name: mes-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD:-mes_redis_2026!}
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --appendfsync everysec
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD:-mes_redis_2026!}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mes-network
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 300M

  # ─────────────────────────────────────────────
  # 3. Eclipse Mosquitto — MQTT 브로커 (센서 데이터 수집)
  # ─────────────────────────────────────────────
  mes-mqtt:
    image: eclipse-mosquitto:2
    container_name: mes-mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"     # MQTT TCP
      - "9883:9883"     # MQTT WebSocket (프론트엔드 실시간 연동용)
    volumes:
      - ./infra/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - ./infra/mosquitto/passwd:/mosquitto/config/passwd:ro
      - mosquitto_data:/mosquitto/data
      - mosquitto_log:/mosquitto/log
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$SYS/#", "-C", "1", "-i", "healthcheck", "-W", "3"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - mes-network
    deploy:
      resources:
        limits:
          cpus: "0.25"
          memory: 128M

  # ─────────────────────────────────────────────
  # 4. MES API — FastAPI 백엔드
  # ─────────────────────────────────────────────
  mes-api:
    build:
      context: .
      dockerfile: Dockerfile.api
      target: dev
    container_name: mes-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      <<: *common-env
      DATABASE_URL: "postgresql+asyncpg://${POSTGRES_USER:-mes_admin}:${POSTGRES_PASSWORD:-mes_secure_2026!}@mes-db:5432/${POSTGRES_DB:-mes_db}"
      DATABASE_URL_SYNC: "postgresql://${POSTGRES_USER:-mes_admin}:${POSTGRES_PASSWORD:-mes_secure_2026!}@mes-db:5432/${POSTGRES_DB:-mes_db}"
      REDIS_URL: "redis://:${REDIS_PASSWORD:-mes_redis_2026!}@mes-redis:6379/0"
      MQTT_BROKER_HOST: mes-mqtt
      MQTT_BROKER_PORT: "1883"
      JWT_SECRET: ${JWT_SECRET:-dev-jwt-secret-change-in-production}
      JWT_ALGORITHM: "HS256"
      JWT_EXPIRE_MINUTES: "60"
      CORS_ORIGINS: "http://localhost:5173,http://localhost:3000"
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
      UVICORN_WORKERS: "1"
      DB_POOL_MIN: "2"
      DB_POOL_MAX: "10"
    volumes:
      - ./app.py:/app/app.py
      - ./api_modules:/app/api_modules
      - ./alembic:/app/alembic
      - ./alembic.ini:/app/alembic.ini
    depends_on:
      mes-db:
        condition: service_healthy
      mes-redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 30s
    networks:
      - mes-network
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G
        reservations:
          cpus: "0.25"
          memory: 512M

  # ─────────────────────────────────────────────
  # 5. MES Frontend — React/Vite (개발 서버)
  # ─────────────────────────────────────────────
  mes-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.web
      target: dev
    container_name: mes-frontend
    restart: unless-stopped
    ports:
      - "5173:5173"
    environment:
      <<: *common-env
      VITE_API_URL: "http://localhost:8000"
      VITE_MQTT_WS_URL: "ws://localhost:9883"
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    depends_on:
      - mes-api
    networks:
      - mes-network
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 512M

  # ─────────────────────────────────────────────
  # 6. pgAdmin 4 — DB 관리 UI (선택)
  # ─────────────────────────────────────────────
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: mes-pgadmin
    restart: unless-stopped
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@mes.local}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-pgadmin1234}
      PGADMIN_CONFIG_SERVER_MODE: "False"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      mes-db:
        condition: service_healthy
    networks:
      - mes-network
    profiles:
      - tools

  # ─────────────────────────────────────────────
  # 7. Prometheus — 메트릭 수집 (선택)
  # ─────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v2.51.0
    container_name: mes-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./infra/prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=15d"
      - "--web.enable-lifecycle"
    networks:
      - mes-network
    profiles:
      - monitoring

  # ─────────────────────────────────────────────
  # 8. Grafana — 대시보드 (선택)
  # ─────────────────────────────────────────────
  grafana:
    image: grafana/grafana:10.4.0
    container_name: mes-grafana
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-grafana1234}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infra/grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    networks:
      - mes-network
    profiles:
      - monitoring

# ─────────────────────────────────────────────
# 네트워크
# ─────────────────────────────────────────────
networks:
  mes-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

# ─────────────────────────────────────────────
# 볼륨
# ─────────────────────────────────────────────
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  mosquitto_data:
    driver: local
  mosquitto_log:
    driver: local
  pgadmin_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

### 2.2 Mosquitto 설정 파일

**파일 경로**: `infra/mosquitto/mosquitto.conf`

```conf
# Eclipse Mosquitto v2 설정 — DEXWEAVER MES v6.0
# MQTT 브로커 설정 (센서 데이터 수집, REQ-042)

# 기본 리스너 (MQTT TCP)
listener 1883
protocol mqtt

# WebSocket 리스너 (프론트엔드 실시간 연동)
listener 9883
protocol websockets

# 인증
allow_anonymous false
password_file /mosquitto/config/passwd

# 퍼시스턴스
persistence true
persistence_location /mosquitto/data/

# 로그
log_dest file /mosquitto/log/mosquitto.log
log_type all
log_timestamp true
log_timestamp_format %Y-%m-%dT%H:%M:%S

# 메시지 제한
max_inflight_messages 200
max_queued_messages 1000
message_size_limit 1048576

# Keep-alive
max_keepalive 120
```

### 2.3 환경 변수 파일

**파일 경로**: `.env` (Git에 포함하지 않음, `.env.example`로 템플릿 제공)

```bash
# ── Database ──
POSTGRES_USER=mes_admin
POSTGRES_PASSWORD=mes_secure_2026!
POSTGRES_DB=mes_db

# ── Redis ──
REDIS_PASSWORD=mes_redis_2026!

# ── JWT ──
JWT_SECRET=dev-jwt-secret-change-in-production

# ── pgAdmin (선택) ──
PGADMIN_EMAIL=admin@mes.local
PGADMIN_PASSWORD=pgadmin1234

# ── Grafana (선택) ──
GRAFANA_USER=admin
GRAFANA_PASSWORD=grafana1234
```

---

## 3. Dockerfile 설계

### 3.1 Backend — Dockerfile.api

```dockerfile
# Dockerfile.api — DEXWEAVER MES v6.0 Backend
# 멀티스테이지 빌드: builder → runtime → dev
# 대상: FastAPI + Uvicorn + asyncpg + Redis + MQTT

# ============================================================
# Stage 1: Builder — 의존성 설치
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# 시스템 의존성 (psycopg2 빌드용, prophet C 확장 빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# pip 의존성 설치 (캐시 레이어 최대 활용을 위해 requirements.txt만 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============================================================
# Stage 2: Runtime — 최소 프로덕션 이미지
# ============================================================
FROM python:3.11-slim AS runtime

# 보안: non-root 사용자 생성
RUN groupadd -r mesapp && useradd -r -g mesapp -d /app -s /sbin/nologin mesapp

# 런타임 시스템 라이브러리 (libpq for asyncpg/psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 복사 (builder stage에서)
COPY --from=builder /install /usr/local

# 애플리케이션 코드 복사
WORKDIR /app
COPY app.py .
COPY api_modules/ ./api_modules/
COPY alembic/ ./alembic/
COPY alembic.ini .

# 소유권 설정
RUN chown -R mesapp:mesapp /app

# non-root 사용자로 전환
USER mesapp

# 환경 변수
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 포트 노출
EXPOSE 8000

# 실행 (Uvicorn + 멀티 워커)
CMD ["python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log"]

# ============================================================
# Stage 3: Dev — 개발 환경 (핫 리로드)
# ============================================================
FROM runtime AS dev

USER root
RUN pip install --no-cache-dir debugpy watchfiles
USER mesapp

CMD ["python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload", \
     "--reload-dir", "/app"]
```

### 3.2 Updated requirements.txt

> As-Is(`requirements.txt`)에서 추가/변경되는 패키지를 강조 표시.

```txt
# ── Core Framework ──
fastapi==0.115.0                    # (업그레이드) 0.109.0 → 0.115.0
uvicorn[standard]==0.32.0           # (업그레이드) 0.27.0 → 0.32.0, uvloop/httptools 포함
pydantic>=2.0,<3.0
pydantic-settings>=2.0              # (신규) 환경변수 설정 관리

# ── Database (비동기 전환, NFR-006) ──
asyncpg>=0.29.0                     # (신규) 비동기 PostgreSQL 드라이버
psycopg2-binary==2.9.9              # (유지) Alembic 마이그레이션용 동기 드라이버
sqlalchemy[asyncio]>=2.0.25         # (신규) ORM + 비동기 지원
alembic>=1.13.0                     # (신규) DB 마이그레이션 (NFR-005)

# ── Cache / Session (NFR-009) ──
redis[hiredis]>=5.0.0               # (신규) Redis 클라이언트 + C 파서
fastapi-cache2>=0.2.1               # (신규) FastAPI 캐시 데코레이터

# ── MQTT (REQ-042) ──
aiomqtt>=2.0.0                      # (신규) 비동기 MQTT 클라이언트

# ── Auth / Security (NFR-007) ──
bcrypt>=4.0.0
PyJWT>=2.8.0
slowapi>=0.1.9                      # (신규) Rate Limiting
python-multipart>=0.0.6             # (신규) 파일 업로드 지원 (REQ-043)

# ── AI / ML ──
numpy>=1.24.0
scikit-learn>=1.3.0
xgboost>=2.0.0
shap>=0.43.0
ortools>=9.8
prophet>=1.1.0
joblib>=1.3.0                       # (신규) 모델 직렬화/캐싱 (NFR-003)

# ── WebSocket (REQ-038) ──
websockets>=12.0                    # (신규) 실시간 알림

# ── Monitoring ──
prometheus-fastapi-instrumentator>=6.0.0  # (신규) Prometheus 메트릭 자동 수집

# ── Utilities ──
httpx>=0.27.0                       # (신규) 비동기 HTTP 클라이언트 (ERP 연동 등)
python-json-logger>=2.0.0           # (신규) 구조화 JSON 로깅

# ── Test (개발 환경 전용, 프로덕션 이미지에서는 제외) ──
# pytest==8.0.0
# pytest-asyncio>=0.23.0
# pytest-cov>=4.1.0
# httpx                              # TestClient용
```

### 3.3 Frontend — Dockerfile.web

```dockerfile
# Dockerfile.web — DEXWEAVER MES v6.0 Frontend
# 멀티스테이지 빌드: deps → build → production / dev

# ============================================================
# Stage 1: Dependencies — Node 모듈 설치
# ============================================================
FROM node:20-alpine AS deps

WORKDIR /app

# package.json과 lock 파일만 먼저 복사 (캐시 레이어 최대 활용)
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline

# ============================================================
# Stage 2: Build — Vite 프로덕션 빌드
# ============================================================
FROM node:20-alpine AS build

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 빌드 시 환경 변수 (Vite는 빌드 시점에 VITE_ 접두사 변수를 번들에 포함)
ARG VITE_API_URL=""
ARG VITE_MQTT_WS_URL=""
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_MQTT_WS_URL=${VITE_MQTT_WS_URL}

RUN npm run build

# ============================================================
# Stage 3: Production — nginx 서빙
# ============================================================
FROM nginx:1.25-alpine AS production

# 기본 nginx 설정 제거
RUN rm -rf /etc/nginx/conf.d/*

# 커스텀 nginx 설정 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드 결과물 복사
COPY --from=build /app/dist /usr/share/nginx/html

# 보안: non-root 실행 가능하도록 권한 설정
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

# ============================================================
# Stage 4: Dev — Vite 개발 서버 (핫 리로드)
# ============================================================
FROM node:20-alpine AS dev

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY package.json .

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0"]
```

### 3.4 nginx.conf (Frontend SPA 라우팅 + 보안 헤더)

**파일 경로**: `frontend/nginx.conf`

```nginx
# nginx.conf — DEXWEAVER MES v6.0 Frontend
# SPA 라우팅 + API 리버스 프록시 + 보안 헤더 + Gzip 압축

server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # ── 보안 헤더 ──
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss: http: https:;"
        always;

    # ── Gzip 압축 ──
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        application/json
        application/javascript
        text/xml
        application/xml
        application/xml+rss
        text/javascript
        image/svg+xml;

    # ── 정적 파일 캐싱 (Vite 해시 파일명이므로 장기 캐싱 안전) ──
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # ── SPA 라우팅 (모든 경로 → index.html) ──
    location / {
        try_files $uri $uri/ /index.html;
    }

    # ── API 리버스 프록시 ──
    location /api/ {
        proxy_pass http://mes-api-service:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 지원 (실시간 알림, REQ-038)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;
        proxy_send_timeout 60s;
    }

    # ── 헬스체크 엔드포인트 ──
    location /health {
        access_log off;
        return 200 "OK";
    }
}
```

---

## 4. Kubernetes 매니페스트 — To-Be

### 4.1 네임스페이스

```yaml
# infra/k8s/00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mes-production
  labels:
    app.kubernetes.io/part-of: dexweaver-mes
    environment: production
```

### 4.2 ConfigMap (비밀이 아닌 설정)

```yaml
# infra/k8s/01-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mes-config
  namespace: mes-production
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRE_MINUTES: "60"
  CORS_ORIGINS: "https://mes.example.com"
  UVICORN_WORKERS: "4"
  DB_POOL_MIN: "5"
  DB_POOL_MAX: "20"
  MQTT_BROKER_HOST: "mes-mqtt-service"
  MQTT_BROKER_PORT: "1883"
  REDIS_DB: "0"
  REDIS_MAX_CONNECTIONS: "50"
```

### 4.3 Secret (민감 정보)

```yaml
# infra/k8s/02-secrets.yaml
# 주의: 실제 프로덕션에서는 아래 방법 중 하나를 사용하여 Git에 평문 Secret을 저장하지 않는다.
#   (1) External Secrets Operator + HashiCorp Vault
#   (2) Sealed Secrets (Bitnami)
#   (3) CI/CD에서 kubectl create secret --from-literal 명령으로 생성
# 아래는 구조 템플릿이며 실제 값은 CI/CD에서 주입한다.

apiVersion: v1
kind: Secret
metadata:
  name: mes-secrets
  namespace: mes-production
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://mes_admin:CHANGE_ME@postgres:5432/mes_db"
  DATABASE_URL_SYNC: "postgresql://mes_admin:CHANGE_ME@postgres:5432/mes_db"
  REDIS_URL: "redis://:CHANGE_ME@mes-redis-service:6379/0"
  JWT_SECRET: "CHANGE_ME_TO_RANDOM_256BIT_KEY"
  POSTGRES_USER: "mes_admin"
  POSTGRES_PASSWORD: "CHANGE_ME"
  REDIS_PASSWORD: "CHANGE_ME"
```

### 4.4 PostgreSQL (PVC + Deployment + Service)

```yaml
# infra/k8s/10-postgres.yaml

# ── PersistentVolumeClaim ──
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: mes-production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard           # 클러스터 StorageClass에 맞게 변경
  resources:
    requests:
      storage: 20Gi
---
# ── Deployment ──
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: mes-production
  labels:
    app: postgres
    tier: database
spec:
  replicas: 1
  strategy:
    type: Recreate                     # DB는 Recreate (롤링 업데이트 불가)
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
        tier: database
    spec:
      securityContext:
        runAsUser: 999                 # postgres 사용자
        fsGroup: 999
      containers:
        - name: postgres
          image: postgres:15-alpine
          ports:
            - containerPort: 5432
              name: postgresql
          env:
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: POSTGRES_USER
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: POSTGRES_PASSWORD
            - name: POSTGRES_DB
              value: "mes_db"
            - name: PGDATA
              value: "/var/lib/postgresql/data/pgdata"
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
          volumeMounts:
            - name: pgdata
              mountPath: /var/lib/postgresql/data
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "mes_admin", "-d", "mes_db"]
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 6
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "mes_admin", "-d", "mes_db"]
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
      volumes:
        - name: pgdata
          persistentVolumeClaim:
            claimName: postgres-pvc
---
# ── Service ──
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: mes-production
spec:
  type: ClusterIP
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
      name: postgresql
```

### 4.5 Redis (PVC + Deployment + Service)

```yaml
# infra/k8s/11-redis.yaml

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: mes-production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 2Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mes-redis
  namespace: mes-production
  labels:
    app: mes-redis
    tier: cache
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: mes-redis
  template:
    metadata:
      labels:
        app: mes-redis
        tier: cache
    spec:
      securityContext:
        runAsUser: 999
        fsGroup: 999
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
              name: redis
          command: ["redis-server"]
          args:
            - --requirepass
            - $(REDIS_PASSWORD)
            - --maxmemory
            - "512mb"
            - --maxmemory-policy
            - allkeys-lru
            - --appendonly
            - "yes"
            - --appendfsync
            - everysec
            - --save
            - "60"
            - "1000"
          env:
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: REDIS_PASSWORD
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          volumeMounts:
            - name: redis-data
              mountPath: /data
          livenessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            exec:
              command: ["redis-cli", "ping"]
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: redis-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: mes-redis-service
  namespace: mes-production
spec:
  type: ClusterIP
  selector:
    app: mes-redis
  ports:
    - port: 6379
      targetPort: 6379
      name: redis
```

### 4.6 MQTT Mosquitto (ConfigMap + Deployment + Service)

```yaml
# infra/k8s/12-mosquitto.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: mosquitto-config
  namespace: mes-production
data:
  mosquitto.conf: |
    listener 1883
    protocol mqtt
    listener 9883
    protocol websockets
    allow_anonymous false
    password_file /mosquitto/config/passwd
    persistence true
    persistence_location /mosquitto/data/
    log_dest stdout
    log_type all
    max_inflight_messages 200
    max_queued_messages 5000
    message_size_limit 1048576
    max_keepalive 120
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mes-mqtt
  namespace: mes-production
  labels:
    app: mes-mqtt
    tier: broker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mes-mqtt
  template:
    metadata:
      labels:
        app: mes-mqtt
        tier: broker
    spec:
      containers:
        - name: mosquitto
          image: eclipse-mosquitto:2
          ports:
            - containerPort: 1883
              name: mqtt
            - containerPort: 9883
              name: mqtt-ws
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 250m
              memory: 256Mi
          volumeMounts:
            - name: mosquitto-config
              mountPath: /mosquitto/config/mosquitto.conf
              subPath: mosquitto.conf
            - name: mosquitto-data
              mountPath: /mosquitto/data
          livenessProbe:
            tcpSocket:
              port: 1883
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            tcpSocket:
              port: 1883
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: mosquitto-config
          configMap:
            name: mosquitto-config
        - name: mosquitto-data
          emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: mes-mqtt-service
  namespace: mes-production
spec:
  type: ClusterIP
  selector:
    app: mes-mqtt
  ports:
    - port: 1883
      targetPort: 1883
      name: mqtt
    - port: 9883
      targetPort: 9883
      name: mqtt-ws
```

### 4.7 MES API (Deployment + Service + HPA)

```yaml
# infra/k8s/20-mes-api.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mes-api
  namespace: mes-production
  labels:
    app: mes-api
    tier: backend
spec:
  replicas: 2                              # 최소 2개 Pod으로 시작
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0                    # 무중단 배포 보장
  selector:
    matchLabels:
      app: mes-api
  template:
    metadata:
      labels:
        app: mes-api
        tier: backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: mes-api-sa
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: mes-api
          image: ghcr.io/your-org/dexweaver-mes-api:latest   # CI/CD에서 태그 치환
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: mes-config
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: DATABASE_URL
            - name: DATABASE_URL_SYNC
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: DATABASE_URL_SYNC
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: REDIS_URL
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: mes-secrets
                  key: JWT_SECRET
          resources:
            requests:
              cpu: 250m
              memory: 512Mi
            limits:
              cpu: "1"
              memory: 1Gi
          readinessProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 15
            timeoutSeconds: 5
            failureThreshold: 5
          startupProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 12          # 최대 60초 대기 (AI 모델 로딩 시간 고려)
      imagePullSecrets:
        - name: ghcr-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: mes-api-service
  namespace: mes-production
spec:
  type: ClusterIP
  selector:
    app: mes-api
  ports:
    - port: 8000
      targetPort: 8000
      name: http
---
# ── HPA (Horizontal Pod Autoscaler) ──
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mes-api-hpa
  namespace: mes-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mes-api
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60       # 1분 안정화 후 스케일 업
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300      # 5분 안정화 후 스케일 다운
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
```

### 4.8 MES Frontend (Deployment + Service + HPA)

```yaml
# infra/k8s/21-mes-frontend.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: mes-frontend
  namespace: mes-production
  labels:
    app: mes-frontend
    tier: frontend
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: mes-frontend
  template:
    metadata:
      labels:
        app: mes-frontend
        tier: frontend
    spec:
      containers:
        - name: nginx
          image: ghcr.io/your-org/dexweaver-mes-frontend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 80
              name: http
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 250m
              memory: 128Mi
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 15
      imagePullSecrets:
        - name: ghcr-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: mes-frontend-service
  namespace: mes-production
spec:
  type: ClusterIP
  selector:
    app: mes-frontend
  ports:
    - port: 80
      targetPort: 80
      name: http
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mes-frontend-hpa
  namespace: mes-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mes-frontend
  minReplicas: 2
  maxReplicas: 4
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 80
```

### 4.9 Ingress (TLS + WebSocket)

```yaml
# infra/k8s/30-ingress.yaml

apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mes-ingress
  namespace: mes-production
  annotations:
    # NGINX Ingress Controller
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "60"
    # WebSocket 지원 (실시간 알림, REQ-038)
    nginx.ingress.kubernetes.io/proxy-http-version: "1.1"
    nginx.ingress.kubernetes.io/configuration-snippet: |
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
    # Rate Limiting (Ingress 레벨 글로벌 제한)
    nginx.ingress.kubernetes.io/limit-rps: "50"
    nginx.ingress.kubernetes.io/limit-burst-multiplier: "5"
    # Let's Encrypt TLS 자동 발급 (cert-manager)
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - mes.example.com
      secretName: mes-tls-secret
  rules:
    - host: mes.example.com
      http:
        paths:
          # API 백엔드
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: mes-api-service
                port:
                  number: 8000
          # WebSocket 엔드포인트
          - path: /ws
            pathType: Prefix
            backend:
              service:
                name: mes-api-service
                port:
                  number: 8000
          # Grafana 대시보드
          - path: /grafana
            pathType: Prefix
            backend:
              service:
                name: grafana
                port:
                  number: 3000
          # Frontend (기본 라우트 — 반드시 마지막에 위치)
          - path: /
            pathType: Prefix
            backend:
              service:
                name: mes-frontend-service
                port:
                  number: 80
```

### 4.10 NetworkPolicy (Cilium)

```yaml
# infra/k8s/31-network-policy.yaml

# ── 기본 정책: 네임스페이스 내 모든 Ingress 기본 차단 ──
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: mes-production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
---
# ── PostgreSQL: mes-api Pod에서만 접근 허용 ──
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-postgres-from-api
  namespace: mes-production
spec:
  podSelector:
    matchLabels:
      app: postgres
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: mes-api
      ports:
        - port: 5432
          protocol: TCP
---
# ── Redis: mes-api Pod에서만 접근 허용 ──
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-redis-from-api
  namespace: mes-production
spec:
  podSelector:
    matchLabels:
      app: mes-redis
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: mes-api
      ports:
        - port: 6379
          protocol: TCP
---
# ── MQTT: mes-api Pod에서만 접근 허용 ──
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-mqtt-from-api
  namespace: mes-production
spec:
  podSelector:
    matchLabels:
      app: mes-mqtt
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: mes-api
      ports:
        - port: 1883
          protocol: TCP
        - port: 9883
          protocol: TCP
---
# ── API: Ingress Controller + Frontend에서 접근 허용 ──
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-ingress
  namespace: mes-production
spec:
  podSelector:
    matchLabels:
      app: mes-api
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: mes-frontend
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 8000
          protocol: TCP
---
# ── Frontend: Ingress Controller에서만 접근 허용 ──
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-ingress
  namespace: mes-production
spec:
  podSelector:
    matchLabels:
      app: mes-frontend
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 80
          protocol: TCP
```

---

## 5. CI/CD 파이프라인

### 5.1 GitHub Actions — 메인 워크플로우

**파일 경로**: `.github/workflows/ci-cd.yml`

```yaml
name: DEXWEAVER MES CI/CD

on:
  push:
    branches: [main, develop, "release/**"]
  pull_request:
    branches: [main, develop]

env:
  REGISTRY: ghcr.io
  API_IMAGE: ghcr.io/${{ github.repository_owner }}/dexweaver-mes-api
  FRONTEND_IMAGE: ghcr.io/${{ github.repository_owner }}/dexweaver-mes-frontend

jobs:
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Job 1: 코드 품질 검사
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install lint tools
        run: pip install black flake8 isort mypy

      - name: Run Black (format check)
        run: black --check --diff .

      - name: Run Flake8 (lint)
        run: flake8 --max-line-length=120 --exclude=alembic app.py api_modules/

      - name: Run isort (import order check)
        run: isort --check-only --diff .

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Frontend lint
        working-directory: frontend
        run: |
          npm ci
          npx eslint src/ --max-warnings=0

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Job 2: 백엔드 테스트 (PostgreSQL + Redis Service Container)
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  test-backend:
    name: Backend Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_mes_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready -U test_user -d test_mes_db"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov httpx

      - name: Run Alembic migrations (테스트 DB 스키마 적용)
        env:
          DATABASE_URL_SYNC: postgresql://test_user:test_pass@localhost:5432/test_mes_db
        run: alembic upgrade head

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_mes_db
          DATABASE_URL_SYNC: postgresql://test_user:test_pass@localhost:5432/test_mes_db
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET: test-jwt-secret
          ENVIRONMENT: test
        run: |
          pytest --cov=api_modules --cov-report=xml --cov-report=term-missing -v

      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
          fail_ci_if_error: false

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Job 3: 프론트엔드 테스트
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  test-frontend:
    name: Frontend Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run unit tests
        working-directory: frontend
        run: npm test -- --run --coverage

      - name: Verify production build
        working-directory: frontend
        run: npm run build

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Job 4: Docker 이미지 빌드 및 Push (GHCR)
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  build-and-push:
    name: Build & Push Docker Images
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: >-
      github.event_name == 'push' &&
      (github.ref == 'refs/heads/main' ||
       github.ref == 'refs/heads/develop' ||
       startsWith(github.ref, 'refs/heads/release/'))
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (커밋 SHA 단축)
        id: meta
        run: |
          SHA_SHORT=$(echo ${{ github.sha }} | cut -c1-7)
          echo "sha_short=${SHA_SHORT}" >> $GITHUB_OUTPUT
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "env_tag=latest" >> $GITHUB_OUTPUT
          elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
            echo "env_tag=develop" >> $GITHUB_OUTPUT
          else
            BRANCH=$(echo "${{ github.ref }}" | sed 's|refs/heads/||' | tr '/' '-')
            echo "env_tag=${BRANCH}" >> $GITHUB_OUTPUT
          fi

      - name: Build & Push API image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile.api
          target: runtime
          push: true
          tags: |
            ${{ env.API_IMAGE }}:${{ steps.meta.outputs.sha_short }}
            ${{ env.API_IMAGE }}:${{ steps.meta.outputs.env_tag }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build & Push Frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          file: ./frontend/Dockerfile.web
          target: production
          push: true
          tags: |
            ${{ env.FRONTEND_IMAGE }}:${{ steps.meta.outputs.sha_short }}
            ${{ env.FRONTEND_IMAGE }}:${{ steps.meta.outputs.env_tag }}
          build-args: |
            VITE_API_URL=
            VITE_MQTT_WS_URL=
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Job 5: Staging 배포 (develop 브랜치 자동)
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4

      - name: Configure kubeconfig
        run: echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > $HOME/.kube/config

      - name: Run Alembic migration (DB 스키마 업데이트)
        run: |
          SHA_SHORT=$(echo ${{ github.sha }} | cut -c1-7)
          kubectl -n mes-staging run alembic-migrate-${SHA_SHORT} \
            --image=${{ env.API_IMAGE }}:${SHA_SHORT} \
            --restart=Never \
            --env="DATABASE_URL_SYNC=${{ secrets.DATABASE_URL_SYNC }}" \
            --command -- alembic upgrade head
          kubectl -n mes-staging wait --for=condition=complete \
            job/alembic-migrate-${SHA_SHORT} --timeout=120s

      - name: Deploy images (롤링 업데이트)
        run: |
          SHA_SHORT=$(echo ${{ github.sha }} | cut -c1-7)
          kubectl -n mes-staging set image deployment/mes-api \
            mes-api=${{ env.API_IMAGE }}:${SHA_SHORT}
          kubectl -n mes-staging set image deployment/mes-frontend \
            nginx=${{ env.FRONTEND_IMAGE }}:${SHA_SHORT}
          kubectl -n mes-staging rollout status deployment/mes-api --timeout=120s
          kubectl -n mes-staging rollout status deployment/mes-frontend --timeout=60s

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Job 6: Production 배포 (main 브랜치, 수동 승인 필수)
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    environment: production              # GitHub Environment 보호 규칙 (수동 승인 필수)
    steps:
      - uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4

      - name: Configure kubeconfig
        run: echo "${{ secrets.KUBE_CONFIG_PRODUCTION }}" | base64 -d > $HOME/.kube/config

      - name: Run Alembic migration (DB 스키마 업데이트)
        run: |
          SHA_SHORT=$(echo ${{ github.sha }} | cut -c1-7)
          kubectl -n mes-production run alembic-migrate-${SHA_SHORT} \
            --image=${{ env.API_IMAGE }}:${SHA_SHORT} \
            --restart=Never \
            --env="DATABASE_URL_SYNC=${{ secrets.DATABASE_URL_SYNC }}" \
            --command -- alembic upgrade head
          kubectl -n mes-production wait --for=condition=complete \
            job/alembic-migrate-${SHA_SHORT} --timeout=120s

      - name: Deploy images (롤링 업데이트)
        run: |
          SHA_SHORT=$(echo ${{ github.sha }} | cut -c1-7)
          kubectl -n mes-production set image deployment/mes-api \
            mes-api=${{ env.API_IMAGE }}:${SHA_SHORT}
          kubectl -n mes-production set image deployment/mes-frontend \
            nginx=${{ env.FRONTEND_IMAGE }}:${SHA_SHORT}
          kubectl -n mes-production rollout status deployment/mes-api --timeout=180s
          kubectl -n mes-production rollout status deployment/mes-frontend --timeout=60s

      - name: Verify deployment (헬스체크)
        run: |
          echo "=== Pod 상태 확인 ==="
          kubectl -n mes-production get pods -l app=mes-api
          kubectl -n mes-production get pods -l app=mes-frontend
          echo "=== API Health Check ==="
          API_POD=$(kubectl -n mes-production get pods -l app=mes-api \
            -o jsonpath='{.items[0].metadata.name}')
          kubectl -n mes-production exec ${API_POD} -- \
            curl -sf http://localhost:8000/api/health
```

### 5.2 CI/CD 파이프라인 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                   GitHub Actions Pipeline                         │
│                                                                   │
│  ┌────────┐    ┌─────────────┐    ┌──────────────┐              │
│  │  Push   │───>│  Lint        │───>│  Test (BE)    │             │
│  │ (PR/Push│    │  black       │    │  pytest+cov   │             │
│  │  Event) │    │  flake8      │    │  alembic up   │             │
│  └────────┘    │  isort       │    └──────┬───────┘             │
│                │  eslint      │           │                       │
│                └──────┬──────┘    ┌──────┴───────┐              │
│                       └──────────>│  Test (FE)    │             │
│                                   │  vitest       │             │
│                                   │  build check  │             │
│                                   └──────┬───────┘             │
│                                          │                      │
│                                   ┌──────▼───────┐              │
│                                   │  Build &      │             │
│                                   │  Push Images  │             │
│                                   │  (GHCR)       │             │
│                                   └──────┬───────┘             │
│                              ┌───────────┴──────────┐          │
│                              │                      │          │
│                   ┌──────────▼────────┐  ┌──────────▼────────┐ │
│                   │  Deploy Staging    │  │  Deploy Production │ │
│                   │  (develop 브랜치)  │  │  (main, 수동승인)  │ │
│                   │  1. Alembic up     │  │  1. Alembic up     │ │
│                   │  2. Set image      │  │  2. Set image      │ │
│                   │  3. Rollout wait   │  │  3. Rollout wait   │ │
│                   │  4. Health check   │  │  4. Health check   │ │
│                   └───────────────────┘  └───────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.3 필수 GitHub Secrets

| Secret 이름 | 용도 | 설정 위치 |
|:----------:|:----:|:--------:|
| `KUBE_CONFIG_STAGING` | Staging 클러스터 kubeconfig (base64) | GitHub Settings > Secrets |
| `KUBE_CONFIG_PRODUCTION` | Production 클러스터 kubeconfig (base64) | GitHub Settings > Secrets |
| `DATABASE_URL_SYNC` | Alembic 마이그레이션용 DB URL | Environment-specific secret |
| `GITHUB_TOKEN` | GHCR 이미지 Push (자동 제공) | 자동 |

---

## 6. 모니터링 스택

### 6.1 Prometheus 설정

**파일 경로**: `infra/prometheus/prometheus.yml`

```yaml
# Prometheus 설정 — DEXWEAVER MES v6.0

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:
  # ── MES API (FastAPI + prometheus-fastapi-instrumentator) ──
  - job_name: "mes-api"
    metrics_path: /metrics
    scrape_interval: 10s
    static_configs:
      - targets: ["mes-api:8000"]
        labels:
          service: "mes-api"
          environment: "dev"

  # ── PostgreSQL Exporter ──
  - job_name: "postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]
        labels:
          service: "postgres"

  # ── Redis Exporter ──
  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]
        labels:
          service: "redis"

  # ── Mosquitto Exporter ──
  - job_name: "mqtt"
    static_configs:
      - targets: ["mqtt-exporter:9234"]
        labels:
          service: "mosquitto"

  # ── Prometheus 자체 메트릭 ──
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
```

### 6.2 Alert Rules

**파일 경로**: `infra/prometheus/alert_rules.yml`

```yaml
# Prometheus Alert Rules — DEXWEAVER MES v6.0

groups:
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # API 서버 경고
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - name: mes-api-alerts
    rules:
      - alert: APIHighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m])) /
            sum(rate(http_requests_total[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          service: mes-api
        annotations:
          summary: "MES API 5xx 에러율 5% 초과"
          description: "최근 5분간 API 에러율: {{ $value | humanizePercentage }}"

      - alert: APIHighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2.0
        for: 5m
        labels:
          severity: warning
          service: mes-api
        annotations:
          summary: "MES API P95 응답시간 2초 초과"
          description: "P95 응답시간: {{ $value }}s"

      - alert: APIDown
        expr: up{job="mes-api"} == 0
        for: 1m
        labels:
          severity: critical
          service: mes-api
        annotations:
          summary: "MES API 서버 다운"
          description: "mes-api 인스턴스가 Prometheus 스크래핑에 응답하지 않음"

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 데이터베이스 경고
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - name: postgres-alerts
    rules:
      - alert: PostgresConnectionPoolExhaustion
        expr: |
          pg_stat_activity_count / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
          service: postgres
        annotations:
          summary: "PostgreSQL 커넥션 풀 80% 이상 사용 중"
          description: "현재 커넥션 사용률: {{ $value | humanizePercentage }}"

      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
          service: postgres
        annotations:
          summary: "PostgreSQL 서버 다운"

      - alert: PostgresHighDiskUsage
        expr: |
          pg_database_size_bytes{datname="mes_db"} > 15 * 1024 * 1024 * 1024
        for: 10m
        labels:
          severity: warning
          service: postgres
        annotations:
          summary: "PostgreSQL 데이터베이스 크기 15GB 초과"
          description: "현재 크기: {{ $value | humanize1024 }}B"

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # Redis 경고
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - name: redis-alerts
    rules:
      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
          service: redis
        annotations:
          summary: "Redis 서버 다운"

      - alert: RedisHighMemoryUsage
        expr: |
          redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          service: redis
        annotations:
          summary: "Redis 메모리 사용률 90% 초과"
          description: "현재 사용률: {{ $value | humanizePercentage }}"

      - alert: RedisLowHitRate
        expr: |
          redis_keyspace_hits_total /
          (redis_keyspace_hits_total + redis_keyspace_misses_total) < 0.8
        for: 15m
        labels:
          severity: warning
          service: redis
        annotations:
          summary: "Redis 캐시 적중률 80% 미만"
          description: "현재 적중률: {{ $value | humanizePercentage }}. 캐시 키 전략 재검토 필요."

  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # MQTT 브로커 경고
  # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  - name: mqtt-alerts
    rules:
      - alert: MQTTBrokerDown
        expr: mosquitto_uptime_seconds == 0 or absent(mosquitto_uptime_seconds)
        for: 1m
        labels:
          severity: critical
          service: mosquitto
        annotations:
          summary: "MQTT 브로커 (Mosquitto) 다운"

      - alert: MQTTHighMessageBacklog
        expr: mosquitto_messages_stored > 10000
        for: 5m
        labels:
          severity: warning
          service: mosquitto
        annotations:
          summary: "MQTT 메시지 백로그 10,000건 초과"
          description: "저장된 메시지: {{ $value }}건. 구독자 처리 지연 확인 필요."
```

### 6.3 Grafana 대시보드 구성

| 대시보드 | 패널 | 데이터 소스 | 비고 |
|:--------:|:----:|:----------:|:----:|
| **MES API Overview** | 요청 수/초 (RPS), P50/P95/P99 응답시간, 에러율 (4xx/5xx), Active Connections | Prometheus (mes-api) | `prometheus-fastapi-instrumentator` 자동 수집 |
| **Database Monitoring** | 커넥션 풀 사용률, 쿼리 수/초, 캐시 적중률, 디스크 사용량, 슬로우 쿼리 | Prometheus (postgres-exporter) | `postgres-exporter` 배포 필요 |
| **Redis Monitoring** | 메모리 사용량, 캐시 적중률 (Hit/Miss), 키 수, Ops/초, 커넥션 수 | Prometheus (redis-exporter) | `redis-exporter` 배포 필요 |
| **MQTT Monitoring** | 연결된 클라이언트 수, 메시지 수/초 (Publish/Subscribe), 메시지 크기, 토픽별 트래픽 | Prometheus (mqtt-exporter) | `mosquitto-exporter` 배포 필요 |
| **Infrastructure** | CPU/메모리 사용률 (Pod별), Pod Restart 횟수, HPA 현황, 네트워크 I/O | Prometheus (kube-state-metrics) | K8s 환경 전용 |

---

## 7. Alembic 마이그레이션 전략

### 7.1 디렉토리 구조

```
MES_PROJECT/
├── alembic/
│   ├── env.py                    # Alembic 환경 설정 (DATABASE_URL_SYNC 환경변수 참조)
│   ├── script.py.mako            # 마이그레이션 스크립트 템플릿
│   └── versions/
│       ├── 001_v4_baseline.py    # v4.0 기존 21개 테이블 (초기 베이스라인)
│       ├── 002_phase1_spc.py     # Phase 1: spc_rules, spc_violations
│       ├── 003_phase1_capa.py    # Phase 1: capa, capa_actions
│       ├── 004_phase1_oee.py     # Phase 1: oee_daily
│       ├── 005_phase1_notify.py  # Phase 1: notifications, notification_settings
│       ├── 006_phase1_indexes.py # Phase 1: 인덱스 생성
│       ├── 007_phase2_maint.py   # Phase 2: maintenance_plans, maintenance_orders
│       ├── 008_phase2_recipe.py  # Phase 2: recipes, recipe_parameters
│       ├── 009_phase2_mqtt.py    # Phase 2: mqtt_config, sensor_data
│       ├── 010_phase2_docs.py    # Phase 2: documents, worker_skills
│       ├── 011_phase2_indexes.py # Phase 2: 인덱스 생성
│       ├── 012_phase3_erp.py     # Phase 3: erp_sync_config, erp_sync_log
│       ├── 013_phase3_opcua.py   # Phase 3: opcua_config
│       ├── 014_phase3_audit.py   # Phase 3: audit_trail
│       ├── 015_phase3_partitions.py  # Phase 3: 테이블 파티셔닝 (sensor_data, audit_trail)
│       └── 016_phase3_indexes.py # Phase 3: 인덱스 생성
│
├── alembic.ini                   # Alembic 메인 설정 파일
└── ...
```

### 7.2 alembic.ini

```ini
[alembic]
script_location = alembic
prepend_sys_path = .

# sqlalchemy.url은 env.py에서 DATABASE_URL_SYNC 환경변수로 오버라이드
sqlalchemy.url = postgresql://mes_admin:mes_secure_2026!@localhost:5433/mes_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 7.3 env.py

```python
"""Alembic env.py — DEXWEAVER MES v6.0
DATABASE_URL_SYNC 환경변수로 DB 연결 URL을 주입받아 마이그레이션을 수행한다.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 환경변수에서 DB URL 오버라이드 (CI/CD 및 Docker 환경용)
database_url = os.getenv("DATABASE_URL_SYNC")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """오프라인 모드: SQL 스크립트만 생성 (DBA 검토용)"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: DB에 직접 마이그레이션 적용"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=None)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 7.4 마이그레이션 CLI 명령어

```bash
# 1. 초기화 (최초 1회)
alembic init alembic

# 2. 베이스라인 생성 (v4.0 기존 테이블 스냅샷)
alembic revision -m "v4.0 baseline - 21 tables"

# 3. Phase 1 마이그레이션 생성 (3개월 내)
alembic revision -m "phase1: add spc_rules and spc_violations tables"
alembic revision -m "phase1: add capa and capa_actions tables"
alembic revision -m "phase1: add oee_daily table"
alembic revision -m "phase1: add notifications and notification_settings tables"
alembic revision -m "phase1: create indexes for phase1 tables"

# 4. 마이그레이션 적용 (업그레이드)
alembic upgrade head               # 최신 버전까지 모두 적용
alembic upgrade +1                  # 한 단계만 적용
alembic upgrade 003                 # 특정 리비전까지 적용

# 5. 마이그레이션 롤백 (다운그레이드)
alembic downgrade -1                # 한 단계 롤백
alembic downgrade 001               # 특정 리비전으로 롤백

# 6. 현재 상태 확인
alembic current                     # 현재 적용된 리비전
alembic history                     # 전체 마이그레이션 이력

# 7. SQL 스크립트만 생성 (DBA 사전 검토용)
alembic upgrade head --sql > migration_preview.sql
```

### 7.5 v4.0 → v6.0 마이그레이션 계획

| 단계 | 리비전 | 대상 테이블 | 예상 다운타임 | 비고 |
|:----:|:------:|:----------:|:----------:|:----:|
| **베이스라인** | 001 | 기존 21개 테이블 스냅샷 | 0 | 기존 데이터 유지, 스키마만 기록 |
| **Phase 1-A** | 002~005 | spc_rules, spc_violations, capa, capa_actions, oee_daily, notifications, notification_settings (7개) | 0 | 신규 테이블 추가만 (기존 데이터 무영향) |
| **Phase 1-B** | 006 | Phase 1 인덱스 (16개) | ~1분 | `CREATE INDEX CONCURRENTLY` 사용 |
| **Phase 2-A** | 007~010 | maintenance_plans, maintenance_orders, recipes, recipe_parameters, mqtt_config, sensor_data, documents, worker_skills (8개) | 0 | 신규 테이블 추가만 |
| **Phase 2-B** | 011 | Phase 2 인덱스 (19개) | ~1분 | `CREATE INDEX CONCURRENTLY` 사용 |
| **Phase 3-A** | 012~014 | erp_sync_config, erp_sync_log, opcua_config, audit_trail (4개) | 0 | 신규 테이블 추가만 |
| **Phase 3-B** | 015 | sensor_data, audit_trail 파티셔닝 | ~5분 | 데이터 마이그레이션 포함 |
| **Phase 3-C** | 016 | Phase 3 인덱스 (8개) | ~1분 | `CREATE INDEX CONCURRENTLY` 사용 |

> **안전성 보장**: 모든 마이그레이션은 `upgrade()`와 `downgrade()` 양방향을 구현하며,
> 인덱스 생성 시 `CREATE INDEX CONCURRENTLY`를 사용하여 운영 중 테이블 Lock을 최소화한다.

---

## 8. 보안 요구사항

### 8.1 TLS/SSL 구성

| 구간 | 방식 | 상세 |
|:----:|:----:|:----:|
| 클라이언트 → Ingress | TLS 1.2+ | cert-manager + Let's Encrypt 자동 발급/갱신 |
| Ingress → Backend Pod | HTTP (클러스터 내부) | NetworkPolicy로 허용된 Pod만 접근 가능 |
| API → PostgreSQL | SSL 선택적 적용 | `sslmode=require` (프로덕션 권장) |
| API → Redis | Redis AUTH | 비밀번호 인증, TLS는 선택 사항 |
| MQTT | MQTT over TLS (선택) | 프로덕션에서는 포트 8883 (MQTTS) 사용 권장 |

### 8.2 Secret 관리 전략

```
┌─────────────────────────────────────────────────────────────────┐
│                       Secret 관리 전략                            │
│                                                                  │
│  개발 환경:  .env 파일 (Git에 포함하지 않음, .gitignore 등록)    │
│  Staging:    GitHub Actions Secrets → kubectl create secret      │
│  Production: External Secrets Operator + HashiCorp Vault (권장)  │
│              또는 Sealed Secrets (Bitnami SealedSecret CRD)      │
│                                                                  │
│  ┌─────────────────────────────────────────┐                     │
│  │ 절대 Git에 저장하지 않을 항목:           │                     │
│  │  - DATABASE_URL (비밀번호 포함)          │                     │
│  │  - JWT_SECRET                            │                     │
│  │  - REDIS_PASSWORD                        │                     │
│  │  - POSTGRES_PASSWORD                     │                     │
│  │  - GHCR 인증 토큰                        │                     │
│  │  - Kubeconfig                            │                     │
│  └─────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Rate Limiting 구성 (NFR-007)

```python
# slowapi 기반 Rate Limiting — 엔드포인트별 차등 적용

RATE_LIMIT_CONFIG = {
    # 인증 API: 무차별 대입 공격(Brute Force) 방어
    "/api/auth/login":       "10/minute",
    "/api/auth/register":    "5/minute",

    # AI API: 고비용 연산 보호 (Prophet, XGBoost 등)
    "/api/ai/*":             "20/minute",

    # 일반 조회 API
    "/api/items":            "100/minute",
    "/api/plans":            "100/minute",
    "/api/work-orders":      "100/minute",

    # 대시보드 (5초 자동 갱신 고려)
    "/api/dashboard/*":      "60/minute",

    # 기본값 (위에 명시되지 않은 모든 엔드포인트)
    "default":               "200/minute",
}
```

### 8.4 CORS 정책

```python
# FastAPI CORS 설정 — 환경별 차등 적용

CORS_CONFIG = {
    "development": {
        "allow_origins": ["http://localhost:5173", "http://localhost:3000"],
        "allow_methods": ["*"],
        "allow_headers": ["*"],
        "allow_credentials": True,
    },
    "staging": {
        "allow_origins": ["https://staging.mes.example.com"],
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": ["Authorization", "Content-Type"],
        "allow_credentials": True,
    },
    "production": {
        "allow_origins": ["https://mes.example.com"],
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
        "allow_headers": ["Authorization", "Content-Type"],
        "allow_credentials": True,
        "max_age": 600,      # Preflight 캐시 10분
    },
}
```

### 8.5 NetworkPolicy 요약

> 상세 YAML은 섹션 4.10 참조.

| 정책 | 소스 → 대상 | 허용 포트 |
|:----:|:----------:|:--------:|
| 기본 차단 | 모든 Pod Ingress 차단 | - |
| API → PostgreSQL | `app=mes-api` → `app=postgres` | 5432/TCP |
| API → Redis | `app=mes-api` → `app=mes-redis` | 6379/TCP |
| API → MQTT | `app=mes-api` → `app=mes-mqtt` | 1883/TCP, 9883/TCP |
| Ingress → API | Ingress NS → `app=mes-api` | 8000/TCP |
| Ingress → Frontend | Ingress NS → `app=mes-frontend` | 80/TCP |

---

## 9. 성능/확장성 요구사항

### 9.1 커넥션 풀링 (asyncpg, NFR-006)

```python
# asyncpg 커넥션 풀 설정 — 환경별 차등 적용

POOL_CONFIG = {
    "development": {
        "min_size": 2,                          # 유휴 커넥션 최소
        "max_size": 10,                         # 동시 커넥션 최대
        "max_queries": 50000,                   # 커넥션당 최대 쿼리 수 후 재생성
        "max_inactive_connection_lifetime": 300.0,  # 유휴 커넥션 5분 후 해제
        "command_timeout": 60.0,                # 쿼리 타임아웃 60초
    },
    "staging": {
        "min_size": 5,
        "max_size": 15,
        "max_queries": 50000,
        "max_inactive_connection_lifetime": 300.0,
        "command_timeout": 30.0,
    },
    "production": {
        "min_size": 5,
        "max_size": 20,
        "max_queries": 50000,
        "max_inactive_connection_lifetime": 300.0,
        "command_timeout": 30.0,
    },
}
```

### 9.2 Redis 캐싱 전략 (NFR-009)

| 캐시 대상 | 키 패턴 | TTL | 무효화 전략 |
|:--------:|:------:|:---:|:----------:|
| 품목 마스터 목록 | `items:list:{page}:{size}` | 5분 | 품목 CUD 시 `items:*` 패턴 삭제 |
| 품목 상세 | `items:detail:{item_code}` | 10분 | 해당 품목 수정 시 개별 키 삭제 |
| BOM 전개 | `bom:explode:{item_code}` | 10분 | BOM 변경 시 관련 키 삭제 |
| 생산계획 목록 | `plans:list:{status}:{page}` | 2분 | 계획 CUD 시 `plans:*` 삭제 |
| 대시보드 집계 | `dashboard:production` | 30초 | 자동 만료 (TTL) |
| AI 예측 결과 | `ai:forecast:{model}:{key}` | 1시간 | 모델 재학습 시 삭제 |
| AI 모델 메타데이터 | `ai:model:{model_type}:meta` | 24시간 | 모델 갱신 시 삭제 (NFR-003) |
| 사용자 세션 | `session:{user_id}` | 60분 | 로그아웃 시 삭제 |
| SPC 관리도 데이터 | `spc:chart:{rule_id}` | 1분 | 검사 등록 시 삭제 |
| 설비 가동 현황 | `equip:status:all` | 30초 | 자동 만료 (TTL) |

### 9.3 데이터베이스 인덱스 전략

> 전체 인덱스 목록(50개+)은 `DatabaseSchema.md`의 "인덱스 설계" 섹션을 참조.

| 인덱스 유형 | 적용 대상 | 적용 기준 |
|:----------:|:--------:|:--------:|
| B-TREE (단일) | FK 컬럼, 자주 검색되는 조건 컬럼 | 기본 인덱스 (총 50개) |
| B-TREE (복합) | `(equip_code, collected_at)` 등 | 시계열 범위 쿼리 최적화 |
| BRIN | `sensor_data.collected_at` | 파티셔닝된 시계열 대용량 테이블 |
| GIN | `ai_forecasts.result_json`, `maintenance_orders.parts_used` | JSONB 필드 내부 검색 |
| Partial | `WHERE is_read = false` (notifications) | 미읽음 알림 빠른 필터링 |

### 9.4 테이블 파티셔닝

> 파티셔닝 대상 테이블 목록은 `DatabaseSchema.md`의 "테이블 파티셔닝 권장 사항" 섹션을 참조.

```sql
-- sensor_data 테이블 월별 RANGE 파티셔닝 예시 (Phase 3, 리비전 015)

CREATE TABLE sensor_data (
    data_id         BIGSERIAL,
    equip_code      VARCHAR(20) NOT NULL,
    sensor_type     VARCHAR(50) NOT NULL,
    value           DECIMAL(12,4) NOT NULL,
    collected_at    TIMESTAMP NOT NULL,
    source          VARCHAR(20) NOT NULL,
    PRIMARY KEY (data_id, collected_at)
) PARTITION BY RANGE (collected_at);

-- 월별 파티션 생성 (pg_partman 확장 또는 수동)
CREATE TABLE sensor_data_2026_03 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
CREATE TABLE sensor_data_2026_04 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
-- ... 이하 월별 반복

-- 파티션별 인덱스 (각 파티션에 자동 생성)
CREATE INDEX idx_sensor_equip_time ON sensor_data (equip_code, collected_at);
```

### 9.5 HPA 스케일링 정책

| 대상 | 최소 Pod | 최대 Pod | CPU 임계값 | 메모리 임계값 | Scale-Up 안정화 | Scale-Down 안정화 |
|:----:|:-------:|:-------:|:---------:|:----------:|:-------------:|:---------------:|
| mes-api | 2 | 8 | 70% | 80% | 60초 | 300초 |
| mes-frontend | 2 | 4 | 80% | - | 60초 | 300초 |

> **Scale-Up 정책**: 1분 안정화 후 최대 2개 Pod 동시 추가 가능.
> **Scale-Down 정책**: 5분 안정화 후 1개씩 순차적으로 제거 (급격한 축소 방지).

---

## 10. 환경별 구성 매트릭스

### 10.1 리소스 및 구성

| 항목 | Development (Docker Compose) | Staging (K8s) | Production (K8s) |
|:----:|:---------------------------:|:------------:|:----------------:|
| **API CPU** | 1 core (limit) | 500m req / 1 core limit | 250m req / 1 core limit |
| **API Memory** | 1Gi (limit) | 512Mi req / 1Gi limit | 512Mi req / 1Gi limit |
| **API Replicas** | 1 | 2 (고정) | 2~8 (HPA) |
| **API Workers (Uvicorn)** | 1 (reload 모드) | 2 | 4 |
| **Frontend Replicas** | 1 | 1 (고정) | 2~4 (HPA) |
| **PostgreSQL Storage** | Docker Volume (unbounded) | 10Gi PVC | 20Gi PVC (SSD) |
| **PostgreSQL CPU/Mem** | 1 core / 512M | 500m / 1Gi | 250m~1 core / 512Mi~1Gi |
| **Redis maxmemory** | 256mb | 256mb | 512mb |
| **Redis Storage** | Docker Volume | 1Gi PVC | 2Gi PVC |
| **MQTT max_queued** | 1,000 | 2,000 | 5,000 |
| **DB Pool min/max** | 2 / 10 | 5 / 15 | 5 / 20 |

### 10.2 네트워크 및 보안

| 항목 | Development | Staging | Production |
|:----:|:-----------:|:-------:|:----------:|
| **Service 노출** | Docker ports (localhost) | NodePort 또는 Ingress | Ingress + TLS |
| **TLS** | 없음 (HTTP) | Self-signed 또는 Let's Encrypt Staging | Let's Encrypt Production |
| **NetworkPolicy** | 없음 (Docker bridge) | 기본 정책 적용 | 엄격한 정책 (섹션 4.10) |
| **CORS** | `localhost:*` 허용 | 스테이징 도메인만 | 프로덕션 도메인만 |
| **Rate Limiting** | 비활성화 (개발 편의) | 활성화 (넉넉한 한도) | 활성화 (엄격한 한도) |
| **Secret 관리** | `.env` 파일 | GitHub Secrets | External Secrets Operator |
| **로그 레벨** | DEBUG | INFO | WARNING |

### 10.3 MQTT QoS 설정

| 항목 | Development | Staging | Production |
|:----:|:-----------:|:-------:|:----------:|
| **기본 QoS** | 0 (At most once) | 1 (At least once) | 1 (At least once) |
| **센서 데이터** | QoS 0 | QoS 0 | QoS 0 (빈번한 데이터, 유실 허용) |
| **설비 상태 변경** | QoS 1 | QoS 1 | QoS 1 (상태 변경은 반드시 전달 보장) |
| **알람/경보** | QoS 1 | QoS 2 | QoS 2 (Exactly once, 중복 방지) |
| **수집 주기** | 10초 | 5초 | 1~5초 (설비별 개별 설정, `mqtt_config` 테이블 참조) |
| **Retained Message** | 비활성 | 활성 | 활성 (마지막 상태 유지) |

### 10.4 접근 URL 정리

| 서비스 | Development | Staging | Production |
|:------:|:-----------:|:-------:|:----------:|
| **Frontend** | `http://localhost:5173` | `https://staging.mes.example.com` | `https://mes.example.com` |
| **API** | `http://localhost:8000` | `https://staging.mes.example.com/api` | `https://mes.example.com/api` |
| **PostgreSQL** | `localhost:5433` | 클러스터 내부 전용 | 클러스터 내부 전용 |
| **Redis** | `localhost:6379` | 클러스터 내부 전용 | 클러스터 내부 전용 |
| **MQTT (TCP)** | `localhost:1883` | 클러스터 내부 전용 | 클러스터 내부 전용 |
| **MQTT (WebSocket)** | `ws://localhost:9883` | 클러스터 내부 전용 | 클러스터 내부 전용 |
| **pgAdmin** | `http://localhost:5050` | 해당 없음 | 해당 없음 |
| **Prometheus** | `http://localhost:9090` | 클러스터 내부 전용 | 클러스터 내부 전용 |
| **Grafana** | `http://localhost:3001` | `https://staging.mes.example.com/grafana` | `https://mes.example.com/grafana` |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|:----:|:----:|:---------:|
| v4.0 | 2025-12 | docker-compose.yml (PostgreSQL only), ConfigMap 기반 K8s 배포, Jenkins CI/CD (불일치) |
| v6.0 | 2026-03-03 | 전면 재설계: Docker 이미지 빌드 전환 (멀티스테이지), Redis 7 + MQTT Mosquitto 추가, asyncpg 비동기 드라이버, Alembic 마이그레이션 (16 리비전), HPA 오토스케일링, GitHub Actions CI/CD (Lint→Test→Build→Deploy), Prometheus + Grafana 모니터링, Cilium NetworkPolicy, TLS Ingress, slowapi Rate Limiting, 환경별 구성 매트릭스 |
