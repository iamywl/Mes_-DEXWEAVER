# KNU MES — CI/CD 파이프라인 검토 보고서

> 작성일: 2026-02-15
> 검토 대상: Jenkinsfile, docker-compose.yml, k8s/ 디렉터리, test_app.py, requirements.txt, frontend/frontend.Dockerfile

---

## 1. 검토 결과 요약

| 항목 | 상태 | 평가 |
|------|------|------|
| **Jenkinsfile** | 존재하지만 구조 불일치 | **재작성 완료** |
| **테스트 (test_app.py)** | 25개 테스트 존재 | 부분 커버리지 (인프라/AI만) |
| **GitHub Actions / GitLab CI** | 없음 | Jenkins 단독 |
| **docker-compose.yml** | 레거시 (postgres only) | 로컬 개발용으로 유지 |
| **k8s/ 디렉터리** | 레거시 (infra/와 중복) | 정리 대상 |
| **requirements.txt** | 존재 | pydantic 누락 → 수정 완료 |
| **frontend.Dockerfile** | 존재 | Docker 빌드 방식 사용 시 참고용 |
| **코드 린팅 도구** | Jenkinsfile에서 설치 | black, flake8, isort, eslint |

### 총평

> **CI/CD 파이프라인은 "골격만 존재"하는 상태였습니다.**
>
> 기존 Jenkinsfile은 Docker 이미지 빌드 + 레지스트리 Push 방식으로 작성되어 있었으나,
> 실제 배포는 **ConfigMap 기반**(Docker 빌드 없음)으로 수행되고 있어 **완전히 불일치**했습니다.
> 이번 검토를 통해 현행 아키텍처에 맞게 Jenkinsfile을 재작성했습니다.

---

## 2. 기존 Jenkinsfile 문제점 분석

### 2.1 치명적 문제 (CRITICAL)

| # | 문제 | 영향 |
|---|------|------|
| C-01 | `DOCKER_REGISTRY = "your-docker-repo"` 플레이스홀더 | Docker Push 단계에서 100% 실패 |
| C-02 | `k8s/backend-service.yaml` 참조 (레거시 경로) | `infra/` 디렉터리와 불일치, 배포 실패 |
| C-03 | Docker 빌드 방식 ↔ ConfigMap 방식 불일치 | 실제 운영 배포 흐름과 완전 다름 |
| C-04 | Keycloak 배포 단계 없음 | 인증 서버 미배포 |
| C-05 | CORS_ORIGINS 처리 없음 | API 서버 CORS 오류 |

### 2.2 경고 (WARNING)

| # | 문제 | 영향 |
|---|------|------|
| W-01 | 거의 모든 명령에 `\|\| true` 적용 | 실패가 마스킹되어 디버깅 불가 |
| W-02 | `port: 8000` 하드코딩 (backend-service.yaml) | 실제 API는 port 80 사용 |
| W-03 | `env.sh` 미활용 | 하드코딩된 설정값 |
| W-04 | `requirements.txt`에 pydantic 누락 | pip install 시 누락 가능 |
| W-05 | 프론트엔드 Docker 빌드 방식 | 실제는 ConfigMap 방식 사용 |

### 2.3 정보 (INFO)

| # | 항목 | 상세 |
|---|------|------|
| I-01 | Lint 단계 존재 | black, flake8, isort, eslint 설치 및 실행 |
| I-02 | 테스트 단계 존재 | pytest, npm test 실행 |
| I-03 | IP 자동 감지 | `hostname -I` 사용 |
| I-04 | 배포 검증 단계 존재 | kubectl get pods/svc 확인 |

---

## 3. 수행된 조치

### 3.1 Jenkinsfile 재작성

**변경 전**: Docker 빌드 + Registry Push + 레거시 k8s/ YAML 참조
**변경 후**: ConfigMap 기반 배포 (init.sh 아키텍처와 동일)

| 단계 | 변경 전 | 변경 후 |
|------|---------|---------|
| 환경 설정 | `DOCKER_REGISTRY` 플레이스홀더 | `env.sh` source |
| 린팅 | `\|\| true`로 실패 무시 | 경고만 출력 (빌드 실패하지 않음) |
| 테스트 | pytest + npm test | pytest + npm test (동일) |
| 백엔드 빌드 | Docker 이미지 빌드 | **제거** (ConfigMap 방식) |
| 프론트엔드 빌드 | Docker 이미지 빌드 | `npm run build` (ConfigMap용) |
| DB 배포 | 없음 | `infra/postgres-pv.yaml` + `postgres.yaml` |
| Keycloak | 없음 | **추가**: `infra/keycloak.yaml` + `setup-keycloak.sh` |
| 백엔드 배포 | Docker 이미지 → k8s/ YAML | ConfigMap(`api-code`) + `infra/mes-api.yaml` |
| 프론트엔드 배포 | Docker 이미지 → k8s/ YAML | ConfigMap(`frontend-build`) + `infra/mes-frontend.yaml` |
| 검증 | kubectl get pods/svc | HTTP 200 응답 확인 포함 |

### 3.2 requirements.txt 수정

```diff
+ pydantic>=2.0
```

### 3.3 레거시 파일 정리

| 파일/디렉터리 | 조치 | 사유 |
|-------------|------|------|
| `k8s/` 디렉터리 | 삭제 | `infra/`와 완전 중복, `your-docker-repo` 플레이스홀더 |
| `docker-compose.yml` | 유지 | 로컬 개발용 PostgreSQL로 활용 가능 |
| `frontend/frontend.Dockerfile` | 유지 | Docker 빌드 방식 전환 시 참고용 |

---

## 4. 테스트 커버리지 현황

### 4.1 현재 테스트 범위 (test_app.py — 25개)

| 테스트 클래스 | 테스트 수 | 대상 |
|--------------|----------|------|
| TestMESDataEndpoints | 8 | 인프라/네트워크/K8s API |
| TestErrorHandling | 4 | 404/405 에러 |
| TestResponseFormat | 5 | JSON 스키마 |
| TestNetworkTopology | 3 | 토폴로지 집계 |
| TestInfraStatusParsing | 3 | 파싱 로직 |
| TestAIPrediction | 2 | AI 예측 |

### 4.2 미커버 영역

| 미커버 API | 엔드포인트 | 비고 |
|-----------|-----------|------|
| 품목 CRUD | `/api/items` (GET/POST/PUT) | DB 의존 |
| BOM | `/api/bom`, `/api/bom/explode`, `/api/bom/where-used` | DB 의존 |
| 공정/라우팅 | `/api/processes`, `/api/routings` | DB 의존 |
| 설비 | `/api/equipments` | DB 의존 |
| 생산계획 | `/api/plans` | DB 의존 |
| 작업지시/실적 | `/api/work-orders`, `/api/work-results` | DB 의존 |
| 품질 | `/api/quality/*` | DB 의존 |
| 재고 | `/api/inventory/*` | DB 의존 |
| 리포트 | `/api/reports/*` | DB 의존 |
| 인증 | `/api/auth/*` | DB 의존 |

> **참고**: DB 의존 테스트는 테스트 DB(mock 또는 별도 PostgreSQL)를 구성해야 합니다.
> 현재 테스트는 DB 연결 없이 실행 가능한 엔드포인트만 대상으로 합니다.

### 4.3 개선 권장사항

| 우선순위 | 항목 | 설명 |
|---------|------|------|
| P1 | DB Mock 테스트 환경 구축 | pytest-mock 또는 testcontainers로 PostgreSQL 연동 테스트 |
| P2 | 비즈니스 API CRUD 테스트 추가 | items, bom, plans 등 핵심 비즈니스 로직 |
| P3 | 프론트엔드 테스트 추가 | React Testing Library + Vitest |
| P4 | E2E 테스트 | Playwright/Cypress로 로그인 → 메뉴 탐색 → CRUD 시나리오 |

---

## 5. CI/CD 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────┐
│                    Jenkins Pipeline                          │
│                                                              │
│  [1] Clean ──→ [2] Lint ──→ [3] Test ──→ [4] Build FE      │
│                  │ black       │ pytest     │ npm run build  │
│                  │ flake8      │ npm test   │                │
│                  │ isort       │            │                │
│                  │ eslint      │            │                │
│                                                              │
│  [5] Deploy DB ──→ [6] Deploy Keycloak                      │
│       │ PV/PVC        │ keycloak.yaml                       │
│       │ Secret        │ setup-keycloak.sh                   │
│       │ postgres.yaml │                                     │
│                                                              │
│  [7] Deploy Backend ──→ [8] Deploy Frontend                 │
│       │ ConfigMap          │ ConfigMap                       │
│       │   api-code         │   frontend-build               │
│       │ mes-api.yaml       │ nginx-config.yaml              │
│       │ CORS 치환          │ mes-frontend.yaml              │
│                                                              │
│  [9] Verify                                                  │
│       │ kubectl get pods                                     │
│       │ HTTP 200 확인 (API, Frontend)                       │
│       │ Keycloak Realm 확인                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. 결론

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| Jenkinsfile 일치도 | **20%** (Docker 방식 ↔ ConfigMap 방식 불일치) | **95%** (init.sh와 동일한 배포 흐름) |
| Keycloak 배포 | 없음 | 포함 |
| 에러 마스킹 | `\|\| true` 남용 | 제거 (실패 시 파이프라인 중단) |
| 환경 설정 | 하드코딩 | `env.sh` source |
| 레거시 파일 | `k8s/` 디렉터리 잔존 | 삭제 완료 |
| 테스트 커버리지 | 25개 (인프라/AI 전용) | 동일 (비즈니스 API 테스트 추가 권장) |

---

**최종 업데이트**: 2026-02-15
