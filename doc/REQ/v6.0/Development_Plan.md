# DEXWEAVER MES v6.0 — 개발계획서

> **버전**: v6.0
> **작성일**: 2026-03-03
> **근거 문서**: [요구사항 정의서](Requirements_Specification.md) | [기능명세서](Functional_Specification.md) | [DB 스키마](DatabaseSchema.md) | [인프라 요구사항](Infrastructure_Requirements.md) | [갭 분석 보고서](Gap_Analysis_Report.md) | [테스트 데이터 전략](TestData_Generation_Strategy.md)
>
> **총 요구사항**: 95건 (기능 75건 + 비기능 20건)
> **현재 구현**: v4.0 기준 34건 (REQ-001~034) + FN-001~037 구현 완료
> **신규 개발 대상**: 기능 41건 + 비기능 20건 = **61건**

---

## 1. 개발 전략 개요

### 1.1 Phase 구성

| Phase | 기간 | 기능 요구사항 | 비기능 요구사항 | 핵심 목표 |
|:-----:|:----:|:------------:|:--------------:|:---------:|
| **Phase 1** | 1~3개월 | REQ-035~039 (5건) | NFR-001~005 (5건) | 핵심 기능 보완 + 아키텍처 기반 확립 |
| **Phase 1+** | 3~6개월 | REQ-052~058 (7건) | NFR-011~014 (4건) | 경쟁사 필수 기능 + 보안 강화 |
| **Phase 2** | 4~6개월 | REQ-040~044 (5건) | NFR-006~010 (5건) | 고급 기능 + 운영 품질 강화 |
| **Phase 2+** | 6~9개월 | REQ-059~070 (12건) | NFR-015~018 (4건) | 표준 준수 강화 + 고급 인프라 |
| **Phase 3** | 9~12개월 | REQ-045~051 (7건) | NFR-019~020 (2건) | 엔터프라이즈 전환 |
| **Phase 3+** | 9~12개월 | REQ-071~075 (5건) | — | 엔터프라이즈 고급 기능 |

### 1.2 개발 원칙

1. **아키텍처 우선**: Phase 1에서 프론트엔드 모듈화(NFR-001) + Docker 빌드(NFR-002) + 인증 통합(NFR-004)을 가장 먼저 수행하여 이후 기능 개발의 기반 확립
2. **인프라 선행**: DB 마이그레이션(NFR-005), Redis 캐싱(NFR-009) 등 공통 인프라를 기능 개발보다 선행
3. **점진적 검증**: 각 Sprint 종료 시 통합테스트 실행, Phase 종료 시 성능/보안 테스트
4. **하위 호환성**: 기존 v4.0 API(FN-001~037)는 유지, 신규 API 추가 방식으로 확장

---

## 2. Phase 1: 핵심 기능 보완 + 아키텍처 기반 (1~3개월)

### 2.1 Sprint 계획

#### Sprint 1-1 (Week 1~2): 아키텍처 기반 확립

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | FastAPI 인증 미들웨어 통합 — `Depends(get_current_user)` 패턴으로 43개 엔드포인트 보일러플레이트 제거 | NFR-004 | `api_modules/auth_middleware.py` |
| BE | app.py → 도메인별 APIRouter 분리 (auth, items, plans, quality, equipment, inventory, ai, reports) | NFR-010 | `api_modules/routers/*.py` |
| FE | App.jsx(2,851줄) → 14개 페이지 컴포넌트 분리, React Router v7 도입 | NFR-001 | `frontend/src/pages/*.jsx` |
| FE | API 서비스 레이어 분리 (인라인 fetch → axios 서비스 모듈) | NFR-001 | `frontend/src/services/*.js` |
| Infra | Alembic 도입 — init.sql 기반 baseline 생성, 마이그레이션 자동화 | NFR-005 | `alembic/`, `alembic.ini` |

**기대 효과**:
- 프론트엔드 God Component 해소 (2,851줄 → 평균 200줄/컴포넌트)
- 백엔드 인증 코드 43회 반복 → 1회로 통합
- DB 스키마 변경 이력 추적 가능

#### Sprint 1-2 (Week 3~4): 인프라 전환

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| Infra | 멀티스테이지 Dockerfile 작성 (Python 3.11 + Node 20 빌드) | NFR-002 | `Dockerfile`, `frontend/Dockerfile` |
| Infra | docker-compose.yml 작성 (PostgreSQL 15 + Redis 7 + API + Frontend) | NFR-002 | `docker-compose.yml` |
| Infra | K8s 매니페스트 업데이트 — HPA(min:2, max:8), Ingress(TLS), Secret 관리 | NFR-002 | `infra/*.yaml` 업데이트 |
| Infra | GitHub Actions CI/CD 파이프라인 구성 (Build → Test → Push → Deploy) | NFR-002 | `.github/workflows/ci-cd.yml` |
| BE | AI 모델 캐싱 — Prophet/XGBoost/IsolationForest 학습 모델 pickle 저장/재사용, Redis 메타데이터 캐싱 | NFR-003 | `api_modules/ai_model_cache.py` |

**기대 효과**:
- 배포 시간: ConfigMap 방식 (~5분) → 이미지 배포 (~2분)
- AI API 응답: Prophet ~5초 → <200ms (캐시 히트 시)
- 오토스케일링 대응 가능

#### Sprint 1-3 (Week 5~6): SPC + CAPA

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| DB | Phase 1 신규 테이블 7개 마이그레이션 생성 (spc_rules, spc_violations, capa, capa_actions, oee_daily, notifications, notification_settings) | DB 스키마 | Alembic 마이그레이션 |
| BE | SPC 관리도 API — X-bar/R차트 데이터 생성, Cp/Cpk 자동 계산, UCL/LCL 설정, Western Electric 규칙 위반 탐지 | REQ-035 | `api_modules/mes_spc.py` |
| BE | CAPA 프로세스 API — CRUD, 워크플로우(OPEN→INVESTIGATION→ACTION→VERIFICATION→CLOSED), 이력 추적 | REQ-036 | `api_modules/mes_capa.py` |
| FE | SPC 관리도 화면 — X-bar/R 차트(Recharts), Cp/Cpk 표시, 이상 경보 알림 | REQ-035 | `frontend/src/pages/SPC.jsx` |
| FE | CAPA 관리 화면 — 등록폼, 워크플로우 상태 표시, 조치 이력 타임라인 | REQ-036 | `frontend/src/pages/CAPA.jsx` |
| Test | SPC/CAPA 단위 테스트 및 API 통합 테스트 | NFR-008 | `tests/test_spc.py`, `tests/test_capa.py` |

**처리 로직 (SPC)**:
1. 검사 데이터 입력 시 서브그룹 분할 (sample_size 기준)
2. X-bar = 서브그룹 평균의 평균, R = 서브그룹 범위의 평균
3. UCL/LCL = X-bar ± A2 × R-bar (A2는 서브그룹 크기별 상수)
4. Cp = (USL - LSL) / (6σ), Cpk = min((USL - X̄)/(3σ), (X̄ - LSL)/(3σ))
5. Western Electric 규칙 적용: 1점 >3σ, 연속 2점 >2σ, 연속 4점 >1σ, 연속 8점 한쪽

#### Sprint 1-4 (Week 7~8): OEE + 실시간 알림

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | OEE 자동 계산 API — 가용률×성능률×품질률, 6대 로스 분석, 일일 집계 배치 | REQ-037 | `api_modules/mes_oee.py` |
| BE | WebSocket 실시간 알림 — FastAPI WebSocket, 알림 구독/발행, 알림 설정 관리 | REQ-038 | `api_modules/mes_notification.py` |
| FE | OEE 대시보드 — OEE 게이지, 가용률/성능률/품질률 차트, 6대 로스 파레토 | REQ-037 | `frontend/src/pages/OEE.jsx` |
| FE | 알림 센터 — WebSocket 연결, 알림 팝업, 미읽음 뱃지, 알림 이력 | REQ-038 | `frontend/src/components/NotificationCenter.jsx` |
| Test | OEE/알림 테스트 | NFR-008 | `tests/test_oee.py`, `tests/test_notification.py` |

**처리 로직 (OEE)**:
1. 가용률 = (계획가동시간 - 정지시간) / 계획가동시간
2. 성능률 = (이론 사이클타임 × 총생산수) / 실제가동시간
3. 품질률 = 양품수 / 총생산수
4. OEE = 가용률 × 성능률 × 품질률
5. 매일 00:00 배치 잡으로 전일 OEE 자동 집계 → oee_daily 저장

#### Sprint 1-5 (Week 9~10): LOT 추적 + 테스트 데이터

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | LOT 추적 강화 API — Forward/Backward 추적 그래프 탐색, 계보도 트리 생성, 리콜 시뮬레이션 | REQ-039 | `api_modules/mes_lot_trace.py` |
| FE | LOT 계보도 화면 — 트리 시각화(D3.js/react-flow), Forward/Backward 토글, 리콜 영향 범위 표시 | REQ-039 | `frontend/src/pages/LotTrace.jsx` |
| Data | Phase 1 테스트 데이터 생성 스크립트 (기존 21개 + 신규 7개 테이블) | 테스트 데이터 전략 | `db/seed_phase1.sql`, `scripts/generate_test_data.py` |
| Test | 전체 통합 테스트, 성능 벤치마크 | NFR-008 | `tests/integration/` |

#### Sprint 1-6 (Week 11~12): Phase 1 안정화 + 모니터링

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| Infra | Prometheus + Grafana 모니터링 스택 구성 | 인프라 요구사항 | `infra/monitoring/` |
| Infra | FastAPI /metrics 엔드포인트 (prometheus-fastapi-instrumentator) | 인프라 요구사항 | app.py 수정 |
| QA | Phase 1 전체 회귀 테스트 | — | 테스트 결과 보고서 |
| QA | 보안 취약점 스캔 (OWASP 기본 항목 점검) | NFR-007 | 보안 점검 보고서 |
| Doc | API 문서 갱신 (OpenAPI/Swagger) | — | `/docs` 자동 생성 |

### 2.2 Phase 1 완료 기준

| 항목 | 기준 |
|:----:|:----:|
| 기능 완료 | REQ-035~039 전체 구현 + API/UI 동작 확인 |
| 비기능 완료 | NFR-001~005 전체 적용 |
| 테스트 | 단위 테스트 커버리지 ≥50%, 통합 테스트 전 API 통과 |
| 성능 | AI API 응답 <500ms (캐시 미적중), <200ms (캐시 적중) |
| 문서 | OpenAPI 스펙 자동 생성 완료 |

---

## 3. Phase 1+: 경쟁사 필수 기능 + 보안 강화 (3~6개월)

### 3.1 Sprint 계획

#### Sprint 1+-1 (Week 13~14): 보안 기반 + 바코드

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | Rate Limiting (slowapi) — 엔드포인트별 제한, JWT Secret 환경변수 전환, CORS 엄격화 | NFR-007 |  `api_modules/security.py` |
| BE | 보안 이벤트 로깅 — 인증실패/권한위반 중앙 로그, 5회 실패→15분 잠금, 세션 타임아웃 30분 | NFR-013 | `api_modules/security_logger.py` |
| BE | 바코드/QR 생성 API — GS1-128/QR/DataMatrix 생성, python-barcode + qrcode 라이브러리 | REQ-052 | `api_modules/mes_barcode.py` |
| FE | 바코드 스캔 뷰어 — 카메라/스캐너 입력 연동, LOT/자재/설비 자동 인식 | REQ-052 | `frontend/src/pages/Barcode.jsx` |
| Infra | TLS 1.3 적용, DB SSL 연결, AES-256 민감 데이터 암호화 | NFR-012 | 인프라 설정 |

#### Sprint 1+-2 (Week 15~16): 전자 작업지시서 + 부적합품 관리

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | 전자 작업지시서(e-WI) API — 단계별 가이드 CRUD, 미디어 첨부, 체크포인트 서명, SOP 연결 | REQ-053 | `api_modules/mes_ewi.py` |
| BE | 부적합품 관리(NCR) API — NCR 등록, 격리(Quarantine) 처리, MRB 워크플로우, CAPA 자동 연계 | REQ-054 | `api_modules/mes_ncr.py` |
| FE | e-WI 스텝 뷰어 — 단계별 진행, 이미지/동영상 인라인 뷰, 서명 캡처 | REQ-053 | `frontend/src/pages/WorkInstruction.jsx` |
| FE | NCR 관리 화면 — 등록폼, 격리 상태 표시, MRB 판정 워크플로우 | REQ-054 | `frontend/src/pages/NCR.jsx` |

#### Sprint 1+-3 (Week 17~18): SPC 자동조치 + 제품출하판정 + 모바일

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | SPC 자동격리조치 — 위반 시 LOT 보류, 설비 정지, CAPA 트리거, 알림 발송 | REQ-055 | `api_modules/mes_spc.py` 확장 |
| BE | 제품출하판정 — 자재 상태 모델(AVAILABLE/HOLD/QUARANTINE/REJECTED), MRB 판정, 감사추적 | REQ-056 | `api_modules/mes_disposition.py` |
| FE | SPC 자동조치 규칙 설정 화면 | REQ-055 | SPC 페이지 확장 |
| FE | 출하판정 워크플로우 화면 | REQ-056 | `frontend/src/pages/Disposition.jsx` |
| FE | 모바일/태블릿 반응형 UI — 핵심 기능(작업지시/실적입력/품질검사/설비상태) 터치 최적화 | NFR-011 | Tailwind 반응형 적용 |

#### Sprint 1+-4 (Week 19~20): KPI + 감사추적 불변성

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | FPY 자동계산 API — 공정별/품목별/라인별 FPY, RTY 산출, 추이 분석 | REQ-057 | `api_modules/mes_kpi.py` |
| BE | 설비보전 KPI API — MTTF/MTTR/MTBF, PM 준수율, CM/PM 비율 자동 계산 | REQ-058 | `api_modules/mes_equip_kpi.py` |
| DB | 감사추적 불변성 — audit_trail 테이블 append-only (REVOKE UPDATE/DELETE), Hash chain 무결성 | NFR-014 | DB 트리거/정책 |
| FE | KPI 대시보드 — FPY/RTY 차트, MTTF/MTTR/MTBF 게이지, 목표 대비 현황 | REQ-057, REQ-058 | `frontend/src/pages/KPI.jsx` |
| Test | Phase 1+ 통합 테스트 + 보안 테스트 | — | 테스트 보고서 |

### 3.2 Phase 1+ 완료 기준

| 항목 | 기준 |
|:----:|:----:|
| 기능 완료 | REQ-052~058 전체 구현 |
| 보안 완료 | NFR-011~014 전체 적용, TLS 1.3, 암호화, 계정 잠금 동작 확인 |
| 모바일 | 작업지시/실적입력/품질검사/설비상태 4개 화면 모바일 동작 확인 |
| 테스트 | 커버리지 ≥60%, 보안 취약점 0건 (Critical/High) |

---

## 4. Phase 2: 고급 기능 + 운영 품질 강화 (4~6개월)

### 4.1 Sprint 계획

#### Sprint 2-1 (Week 21~22): DB 비동기 전환 + CMMS

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | psycopg2 → asyncpg 전환, 커넥션 풀링 (min:5, max:20) | NFR-006 | `api_modules/database.py` 재작성 |
| BE | Redis 캐싱 레이어 — API 응답 캐싱, 세션 캐싱, 마스터 데이터 캐싱, TTL 전략 | NFR-009 | `api_modules/cache.py` |
| BE | CMMS 유지보수 API — PM 일정관리, 정비 작업지시, 정비 이력/비용 관리, 예비부품 재고 | REQ-040 | `api_modules/mes_cmms.py` |
| DB | Phase 2 신규 테이블 8개 마이그레이션 (maintenance_plans, maintenance_orders, recipes, recipe_parameters, mqtt_config, sensor_data, documents, worker_skills) | DB 스키마 | Alembic 마이그레이션 |
| FE | CMMS 화면 — 보전 캘린더, 정비 작업지시서, 정비 이력 | REQ-040 | `frontend/src/pages/CMMS.jsx` |

#### Sprint 2-2 (Week 23~24): 레시피 관리 + MQTT

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | 레시피 관리 API — ISA-88 기반 레시피 마스터, 버전관리, 설정값 vs 실적값 비교 | REQ-041 | `api_modules/mes_recipe.py` |
| BE | MQTT 데이터 수집 — Eclipse Mosquitto 연동, 센서 데이터 자동 수집, 수집 상태 모니터링 | REQ-042 | `api_modules/mes_mqtt.py` |
| Infra | MQTT 브로커(Mosquitto) K8s 배포, sensor_data 테이블 시계열 파티셔닝 | REQ-042 | `infra/mosquitto.yaml` |
| FE | 레시피 관리 화면 — 버전 비교 뷰, 파라미터 설정 | REQ-041 | `frontend/src/pages/Recipe.jsx` |
| FE | MQTT 수집 대시보드 — 연결 상태, 수집 현황, 데이터 미수신 경보 | REQ-042 | `frontend/src/pages/DataCollect.jsx` |

#### Sprint 2-3 (Week 25~26): DMS + 노동 관리 + 테스트 자동화

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | 문서 관리(DMS) API — 문서 CRUD, 버전관리, PDF 출력, 승인 워크플로우 | REQ-043 | `api_modules/mes_dms.py` |
| BE | 노동 관리 API — 스킬 매트릭스, 작업자 배정 최적화, 교육 이력 | REQ-044 | `api_modules/mes_labor.py` |
| FE | DMS 화면 — 문서 목록, 뷰어, 업로드, 승인 플로우 | REQ-043 | `frontend/src/pages/DMS.jsx` |
| FE | 노동 관리 화면 — 스킬 매트릭스 표, 배정 현황, 교육 이력 | REQ-044 | `frontend/src/pages/Labor.jsx` |
| Test | pytest 기반 테스트 자동화 — 비즈니스 로직 단위테스트, API 통합테스트 | NFR-008 | `tests/` 확장 |
| Infra | CI/CD 테스트 자동 실행 연동 | NFR-008 | GitHub Actions 업데이트 |

### 4.2 Phase 2 완료 기준

| 항목 | 기준 |
|:----:|:----:|
| 기능 완료 | REQ-040~044 전체 구현 |
| 비기능 완료 | NFR-006~010 전체 적용 |
| 성능 | asyncpg 전환 후 API 응답 ≤200ms (p95), Redis 캐시 히트율 ≥70% |
| 테스트 | 커버리지 ≥70%, CI/CD 자동 실행 |
| MQTT | 센서 데이터 수집 1,000+ points/sec 처리 가능 |

---

## 5. Phase 2+: 표준 준수 강화 (6~9개월)

### 5.1 Sprint 계획

#### Sprint 2+-1 (Week 27~28): 품질 도구 고도화 (MSA/SPC속성/FMEA)

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | MSA/Gage R&R API — 반복성/재현성 분석, %GRR 계산, AIAG MSA 4th edition | REQ-059 | `api_modules/mes_msa.py` |
| BE | SPC 속성관리도 — p/np/c/u-chart 지원, REQ-035 확장 | REQ-060 | `api_modules/mes_spc.py` 확장 |
| BE | FMEA 관리 API — PFMEA CRUD, S/O/D 점수, RPN 자동계산, 이행추적 | REQ-061 | `api_modules/mes_fmea.py` |
| FE | MSA/FMEA 분석 화면 | REQ-059, REQ-061 | `frontend/src/pages/MSA.jsx`, `FMEA.jsx` |

#### Sprint 2+-2 (Week 29~30): KPI 라이브러리 + 에너지/교정

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | ISO 22400 KPI 라이브러리 — Throughput Rate, Lead Time, Cycle Time, Setup Time, Worker Efficiency, Inventory Turns | REQ-062 | `api_modules/mes_kpi.py` 확장 |
| BE | 에너지 관리 API — 에너지 소비 모니터링, kWh/unit, 비용 분석, 피크 알림 | REQ-063 | `api_modules/mes_energy.py` |
| BE | 교정 관리 API — 교정 주기, 성적서, 만료 자동 차단, 검사 연계 | REQ-064 | `api_modules/mes_calibration.py` |
| FE | ISO 22400 KPI 대시보드, 에너지 대시보드, 교정 캘린더 | REQ-062~064 | 각 페이지 |

#### Sprint 2+-3 (Week 31~32): SQM + 자동디스패칭 + 셋업시간

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | 공급업체 품질 관리(SQM) — 스코어카드, SCAR 워크플로우, ASL 관리 | REQ-065 | `api_modules/mes_sqm.py` |
| BE | 자동디스패칭/자재역산 — 스케줄→자동 작업지시, BOM 기반 Backflush | REQ-066 | `api_modules/mes_dispatch.py` |
| BE | 셋업시간 매트릭스 — 제품간 전환 셋업시간, 순서 의존 모델링 | REQ-067 | `api_modules/mes_setup.py` |
| FE | SQM 화면, 디스패칭 설정, 셋업 매트릭스 | REQ-065~067 | 각 페이지 |

#### Sprint 2+-4 (Week 33~36): WO 원가 + 대시보드/리포트 빌더 + 인프라

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | WO 원가추적 — 노무비/자재비/경비 집계, 표준 vs 실제 차이분석 | REQ-068 | `api_modules/mes_costing.py` |
| BE | 커스텀 대시보드 빌더 API — 위젯 레이아웃 CRUD, 프리셋 관리 | REQ-069 | `api_modules/mes_dashboard_builder.py` |
| BE | 리포트 빌더 API — 템플릿 관리, PDF/Excel/CSV Export, 정기 자동 생성 | REQ-070 | `api_modules/mes_report_builder.py` |
| FE | 대시보드 빌더 — 드래그&드롭(react-grid-layout), 위젯 라이브러리 | REQ-069 | `frontend/src/pages/DashboardBuilder.jsx` |
| FE | 리포트 빌더 — 필드 배치, 프리뷰, Export | REQ-070 | `frontend/src/pages/ReportBuilder.jsx` |
| Infra | 네트워크 구역 분리 — Cilium NetworkPolicy (IT/OT/DMZ/DB Zone) | NFR-015 | NetworkPolicy 매니페스트 |
| Infra | API 버전관리 — /api/v1/, /api/v2/ 병렬 운영, OpenAPI 3.0 | NFR-018 | 라우터 버전 분리 |
| BE | 전자서명 상세규격 — 2요소 인증, 서명 표시, 암호화 연결 | NFR-017 | `api_modules/e_signature.py` |

### 5.2 Phase 2+ 완료 기준

| 항목 | 기준 |
|:----:|:----:|
| 기능 완료 | REQ-059~070 전체 구현 (12건) |
| 비기능 완료 | NFR-015~018 전체 적용 |
| KPI | ISO 22400 핵심 KPI 15개+ 자동계산 동작 |
| 보안 | 4개 보안 구역 분리, 전자서명 21 CFR Part 11 준수 |

---

## 6. Phase 3: 엔터프라이즈 전환 (9~12개월)

### 6.1 Sprint 계획

#### Sprint 3-1 (Week 37~40): ERP 연동 + OPC-UA + 스케줄링 고도화

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| BE | ERP 연동 인터페이스 — SAP/Oracle 데이터 동기화, B2MML 매핑, 동기화 상태 대시보드 | REQ-045 | `api_modules/mes_erp.py` |
| BE | OPC-UA 연동 — asyncua 라이브러리, 태그 매핑, 실시간 데이터 구독 | REQ-046 | `api_modules/mes_opcua.py` |
| BE | 스케줄링 고도화 — 다목적 최적화, 실시간 리스케줄링, What-If 시뮬레이션 | REQ-050 | `api_modules/mes_scheduler.py` 확장 |
| DB | Phase 3 신규 테이블 4개 마이그레이션 (erp_sync_config, erp_sync_log, opcua_config, audit_trail) | DB 스키마 | Alembic 마이그레이션 |
| DB | audit_trail 테이블 월별 파티셔닝, sensor_data 파티셔닝 | DB 스키마 | Alembic + 파티션 DDL |

#### Sprint 3-2 (Week 41~44): 다국어 + 감사추적 + 자원 통합 관리

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| FE | 다국어 지원 — react-i18next, 한국어/영어 전환, 언어팩 관리 | REQ-047 | `frontend/src/i18n/`, `locales/` |
| BE | 감사 추적 API — 모든 데이터 변경 자동 기록, DB 트리거, 전자서명 연동 | REQ-049 | `api_modules/mes_audit.py` + DB 트리거 |
| BE | 자원 통합 관리 — 설비/작업자/금형/치공구/측정기 통합, M:N 매핑, 가용성 캘린더 | REQ-051 | `api_modules/mes_resource.py` |
| FE | 감사 추적 화면, 자원 통합 대시보드 | REQ-049, REQ-051 | 각 페이지 |

#### Sprint 3-3 (Week 45~48): 디지털 트윈 + 안정화

| 구분 | 작업 항목 | 관련 요구사항 | 산출물 |
|:----:|:-------:|:------------:|:------:|
| FE | 디지털 트윈 — Three.js 기반 공장 3D 뷰, 실시간 설비 상태 오버레이, 이상 하이라이트 | REQ-048 | `frontend/src/pages/DigitalTwin.jsx` |
| Infra | 오프라인/장애 대응 — MQTT 로컬 큐, ERP 트랜잭션 버퍼, Redis 폴백, 프론트엔드 오프라인 | NFR-019 | Graceful Degradation 로직 |
| QA | GAMP 5 IQ/OQ/PQ 프로토콜, Traceability Matrix 자동 생성 | NFR-020 | 밸리데이션 문서 |
| QA | 전체 시스템 회귀 테스트 + 성능/부하 테스트 | — | 최종 테스트 보고서 |

---

## 7. Phase 3+: 엔터프라이즈 고급 기능 (9~12개월, Phase 3과 병행)

> Phase 3+는 Phase 3과 시간적으로 겹치며, 팀 역량과 우선순위에 따라 선별적으로 구현한다.

| Sprint | 작업 항목 | 관련 요구사항 | 우선순위 |
|:------:|:-------:|:------------:|:--------:|
| 3+-1 | 배치실행엔진 — ISA-88 State Machine, 절차 계층, 예외 처리 | REQ-071 | 하 |
| 3+-1 | 전자배치기록(eBR) — 자동 기록, 검토/승인, PDF 출력 | REQ-072 | 하 |
| 3+-2 | 설계변경관리(ECM) — ECR→ECN→ECO 워크플로우, 영향분석 | REQ-073 | 하 |
| 3+-2 | 복합라우팅 — 재진입/조건분기/병렬/재작업 루프 | REQ-074 | 하 |
| 3+-3 | 멀티사이트 관리 — ISA-95 계층, 사이트별 독립 + 통합 가시성 | REQ-075 | 하 |

---

## 8. 기술 스택 변경 사항

### 8.1 백엔드

| 항목 | As-Is (v4.0) | To-Be (v6.0) | 적용 Phase |
|:----:|:------------:|:------------:|:----------:|
| Python 버전 | 3.9 | 3.11 | Phase 1 |
| DB 드라이버 | psycopg2 (동기) | asyncpg (비동기) | Phase 2 |
| DB 마이그레이션 | init.sql 수동 | Alembic | Phase 1 |
| 캐싱 | 없음 | Redis 7 (redis-py) | Phase 1 |
| MQTT 클라이언트 | 없음 | paho-mqtt / aiomqtt | Phase 2 |
| OPC-UA | 없음 | asyncua | Phase 3 |
| 바코드 생성 | 없음 | python-barcode, qrcode | Phase 1+ |
| PDF 생성 | 없음 | reportlab / weasyprint | Phase 2 |
| Rate Limiting | 없음 | slowapi | Phase 1+ |
| 보안 | JWT (PyJWT) | JWT + 계정잠금 + TLS + AES-256 | Phase 1+ |

### 8.2 프론트엔드

| 항목 | As-Is (v4.0) | To-Be (v6.0) | 적용 Phase |
|:----:|:------------:|:------------:|:----------:|
| 구조 | 단일 App.jsx (2,851줄) | 14+ 페이지 컴포넌트 | Phase 1 |
| 라우팅 | 자체 상태 기반 | React Router v7 | Phase 1 |
| API 호출 | 인라인 fetch | axios 서비스 레이어 | Phase 1 |
| 상태관리 | useState/useEffect | Zustand 또는 React Context | Phase 1 |
| 실시간 | 없음 | WebSocket (native) | Phase 1 |
| 차트 | Recharts | Recharts + D3.js (SPC 전용) | Phase 1 |
| 3D | 없음 | Three.js / react-three-fiber | Phase 3 |
| 다국어 | 없음 | react-i18next | Phase 3 |
| 드래그&드롭 | 없음 | react-grid-layout, @dnd-kit | Phase 2+ |
| PWA | 없음 | Service Worker + 오프라인 캐시 | Phase 1+ |

### 8.3 인프라

| 항목 | As-Is (v4.0) | To-Be (v6.0) | 적용 Phase |
|:----:|:------------:|:------------:|:----------:|
| 배포 | ConfigMap + pip install | Docker 이미지 빌드 | Phase 1 |
| 스케일링 | replicas: 1 | HPA (min:2, max:8) | Phase 1 |
| CI/CD | Jenkins (불일치) | GitHub Actions | Phase 1 |
| Service 노출 | NodePort | ClusterIP + Ingress (TLS) | Phase 1 |
| MQTT 브로커 | 없음 | Eclipse Mosquitto | Phase 2 |
| 모니터링 | 없음 | Prometheus + Grafana | Phase 1 |
| 네트워크 정책 | 없음 | Cilium NetworkPolicy | Phase 2+ |

---

## 9. DB 스키마 변경 계획

| Phase | 신규 테이블 | 테이블명 | Alembic 마이그레이션 시점 |
|:-----:|:---------:|:--------:|:------------------------:|
| Phase 1 | 7개 | spc_rules, spc_violations, capa, capa_actions, oee_daily, notifications, notification_settings | Sprint 1-3 |
| Phase 2 | 8개 | maintenance_plans, maintenance_orders, recipes, recipe_parameters, mqtt_config, sensor_data, documents, worker_skills | Sprint 2-1 |
| Phase 3 | 4개 | erp_sync_config, erp_sync_log, opcua_config, audit_trail | Sprint 3-1 |
| **합계** | **19개** | 기존 21개 + 신규 19개 = **총 40개** | — |

### 인덱스 추가 계획

- Phase 1: 기존 테이블 30개 인덱스 + 신규 테이블 14개 인덱스 = **44개**
- Phase 2: 신규 테이블 17개 인덱스
- Phase 3: 신규 테이블 8개 인덱스 + audit_trail 파티셔닝
- **총 69개 인덱스** (기존 0개 → 69개)

### 파티셔닝 대상

| 테이블 | 파티션 기준 | 전략 | Phase |
|:------:|:----------:|:----:|:-----:|
| sensor_data | collected_at | RANGE (월별) | Phase 2 |
| audit_trail | changed_at | RANGE (월별) | Phase 3 |
| equip_sensors | recorded_at | RANGE (월별) | Phase 1 |
| notifications | created_at | RANGE (월별) | Phase 1 |

---

## 10. 테스트 전략

### 10.1 Phase별 테스트 목표

| Phase | 단위 테스트 | 통합 테스트 | E2E 테스트 | 커버리지 목표 |
|:-----:|:---------:|:---------:|:--------:|:------------:|
| Phase 1 | 핵심 비즈니스 로직 (SPC, OEE 계산) | 전 API 엔드포인트 | 핵심 시나리오 5개 | ≥50% |
| Phase 1+ | 보안 로직, KPI 계산 | 바코드/NCR/판정 API | 현장 작업 시나리오 | ≥60% |
| Phase 2 | CMMS, 레시피, MQTT | 데이터 수집 파이프라인 | 전체 업무 플로우 | ≥70% |
| Phase 2+ | MSA, FMEA, 원가 | 빌더 API | 대시보드/리포트 생성 | ≥70% |
| Phase 3 | ERP 연동, 감사 | 전체 시스템 | 엔터프라이즈 시나리오 | ≥75% |

### 10.2 테스트 데이터

| 환경 | 데이터 규모 | 생성 방식 |
|:----:|:---------:|:---------:|
| Dev | 소량 (마스터 20건, 트랜잭션 100건) | SQL 스크립트 |
| Staging | 중량 (마스터 100건, 트랜잭션 10,000건) | Python/Faker |
| Load Test | 대량 (마스터 500건, 트랜잭션 1,000,000건, 센서 10M건) | Python + generate_series |

### 10.3 성능 테스트 기준

| 항목 | Phase 1 목표 | 최종 목표 (Phase 3) |
|:----:|:----------:|:------------------:|
| API 응답 (p95) | ≤500ms | ≤200ms |
| AI 예측 (캐시 히트) | ≤200ms | ≤100ms |
| 동시 접속자 | 50명 | 200명 |
| 센서 데이터 수집 | — | ≥10,000 points/sec |
| DB 쿼리 (p95) | ≤100ms | ≤50ms |

---

## 11. 리스크 관리

| # | 리스크 | 영향 | 가능성 | 완화 전략 |
|:-:|:------:|:----:|:------:|:---------:|
| 1 | 프론트엔드 모듈화 시 기존 기능 회귀 | 상 | 중 | E2E 테스트 선 작성 후 리팩토링, 점진적 분리 |
| 2 | asyncpg 전환 시 기존 동기 코드 호환성 | 상 | 중 | Phase 2에 배치, 충분한 테스트 기간 확보 |
| 3 | MQTT/OPC-UA 실 장비 연동 불확실성 | 중 | 상 | 시뮬레이터로 개발/테스트, 실 연동은 단계적 |
| 4 | 41건 신규 기능의 일정 초과 | 상 | 중 | Phase 1+ 이후는 우선순위 기반 선별 구현 |
| 5 | 팀 규모 대비 작업량 과다 | 상 | 상 | Phase 3+는 선택적 구현, 핵심 기능 우선 |
| 6 | GS인증 심사 일정과 개발 일정 충돌 | 상 | 중 | Phase 1/1+ 완료 후 심사 대응, Phase 2+ 이후는 심사 후 |

---

## 12. 산출물 목록

### 12.1 Phase별 주요 산출물

| Phase | 카테고리 | 산출물 |
|:-----:|:--------:|:------:|
| Phase 1 | 코드 | 14개 프론트엔드 컴포넌트, 5개 신규 API 모듈, 인증 미들웨어, 모델 캐시 |
| Phase 1 | 인프라 | Dockerfile, docker-compose.yml, K8s 매니페스트, CI/CD 파이프라인, 모니터링 |
| Phase 1 | DB | Alembic baseline + Phase 1 마이그레이션 (7개 테이블 + 44개 인덱스) |
| Phase 1+ | 코드 | 7개 신규 API 모듈, 바코드/NCR/판정/KPI 프론트엔드 |
| Phase 1+ | 보안 | TLS 설정, Rate Limiting, 보안 로깅, 감사추적 불변성 |
| Phase 2 | 코드 | 5개 신규 API 모듈, CMMS/레시피/MQTT/DMS/노동 프론트엔드 |
| Phase 2 | 인프라 | MQTT 브로커, asyncpg 전환, Redis 캐싱 |
| Phase 2 | DB | Phase 2 마이그레이션 (8개 테이블 + 17개 인덱스) |
| Phase 2+ | 코드 | 12개 신규 API 모듈, 대시보드/리포트 빌더 |
| Phase 2+ | 인프라 | NetworkPolicy, API 버전관리 |
| Phase 3 | 코드 | ERP/OPC-UA 연동, 감사추적, 디지털 트윈, 자원관리, 다국어 |
| Phase 3 | DB | Phase 3 마이그레이션 (4개 테이블 + 파티셔닝) |
| Phase 3 | 문서 | GAMP 5 밸리데이션 문서, Traceability Matrix |

### 12.2 코드 규모 예측

| 구분 | 현재 (v4.0) | Phase 1 후 | Phase 2 후 | 최종 (v6.0) |
|:----:|:-----------:|:----------:|:----------:|:-----------:|
| 백엔드 모듈 수 | 28개 | 35개 | 42개 | ~60개 |
| 프론트엔드 파일 수 | 1개 (App.jsx) | 20+ 파일 | 30+ 파일 | 45+ 파일 |
| DB 테이블 수 | 21개 | 28개 | 36개 | 40개 |
| API 엔드포인트 수 | 46개 | ~65개 | ~85개 | ~120개 |
| 테스트 파일 수 | 0개 | 10+ | 25+ | 40+ |

---

## 13. 마일스톤 요약

```
2026-03  ├── Phase 1 시작
         │   ├── Sprint 1-1: 아키텍처 기반 (NFR-001, NFR-004, NFR-010)
         │   ├── Sprint 1-2: 인프라 전환 (NFR-002, NFR-003, NFR-005)
         │   ├── Sprint 1-3: SPC + CAPA (REQ-035, REQ-036)
         │   ├── Sprint 1-4: OEE + 알림 (REQ-037, REQ-038)
         │   ├── Sprint 1-5: LOT 추적 (REQ-039)
2026-05  │   └── Sprint 1-6: 안정화 + 모니터링 ── Phase 1 완료 ✓
         │
         ├── Phase 1+ 시작
         │   ├── Sprint 1+-1: 보안 + 바코드 (NFR-007,012,013 / REQ-052)
         │   ├── Sprint 1+-2: e-WI + NCR (REQ-053, REQ-054)
         │   ├── Sprint 1+-3: SPC자동조치 + 출하판정 + 모바일 (REQ-055,056 / NFR-011)
2026-08  │   └── Sprint 1+-4: KPI + 감사불변성 (REQ-057,058 / NFR-014) ── Phase 1+ 완료 ✓
         │
         ├── Phase 2 시작
         │   ├── Sprint 2-1: 비동기DB + CMMS (NFR-006,009 / REQ-040)
         │   ├── Sprint 2-2: 레시피 + MQTT (REQ-041, REQ-042)
2026-09  │   └── Sprint 2-3: DMS + 노동 + 테스트자동화 (REQ-043,044 / NFR-008) ── Phase 2 완료 ✓
         │
         ├── Phase 2+ 시작
         │   ├── Sprint 2+-1: MSA/SPC속성/FMEA (REQ-059~061)
         │   ├── Sprint 2+-2: KPI + 에너지 + 교정 (REQ-062~064)
         │   ├── Sprint 2+-3: SQM + 디스패칭 + 셋업 (REQ-065~067)
2026-12  │   └── Sprint 2+-4: 원가 + 빌더 + 인프라 (REQ-068~070 / NFR-015~018) ── Phase 2+ 완료 ✓
         │
         ├── Phase 3 / 3+ 시작
         │   ├── Sprint 3-1: ERP + OPC-UA + 스케줄링 (REQ-045,046,050)
         │   ├── Sprint 3-2: 다국어 + 감사 + 자원관리 (REQ-047,049,051)
         │   ├── Sprint 3-3: 디지털트윈 + 안정화 (REQ-048 / NFR-019,020)
2027-03  │   └── Phase 3+ 선택 구현 (REQ-071~075) ── Phase 3 완료 ✓
         │
         └── v6.0 GA 릴리스
```

---

## 14. 우선순위 기반 최소 구현 범위 (MVP)

> 일정/리소스 제약 시 아래 범위를 최소 구현 목표로 설정

### 14.1 반드시 구현 (Must-Have) — 6개월 내

| 구분 | 요구사항 | 사유 |
|:----:|:--------:|:----:|
| 아키텍처 | NFR-001 (모듈화), NFR-002 (Docker), NFR-004 (인증), NFR-005 (Alembic) | 개발 생산성의 기반 |
| 핵심 기능 | REQ-035 (SPC), REQ-036 (CAPA), REQ-037 (OEE) | GS인증 핵심 품질 기능 |
| 알림 | REQ-038 (실시간 알림) | 전 기능의 알림 인프라 |
| 추적 | REQ-039 (LOT 추적) | 품질 추적성 필수 |
| 보안 | NFR-007 (보안 강화), NFR-012 (암호화) | GS인증 보안 항목 |
| 경쟁사 필수 | REQ-052 (바코드), REQ-053 (e-WI), REQ-057 (FPY) | 전 경쟁사 기본 기능 |

### 14.2 가능하면 구현 (Should-Have) — 9개월 내

| 구분 | 요구사항 |
|:----:|:--------:|
| 기능 | REQ-040 (CMMS), REQ-042 (MQTT), REQ-054 (NCR), REQ-055 (SPC자동조치), REQ-058 (설비KPI) |
| 품질 | NFR-008 (테스트 자동화), NFR-011 (모바일), NFR-013 (보안로깅) |

### 14.3 여유 시 구현 (Nice-to-Have) — 12개월 내

| 구분 | 요구사항 |
|:----:|:--------:|
| 기능 | REQ-045~051 (엔터프라이즈), REQ-059~070 (표준 준수), REQ-071~075 (고급) |
| 인프라 | NFR-015~020 |

---

*최종 업데이트: 2026-03-03*
*근거: v6.0 요구사항 정의서 95건 + 갭 분석 보고서 34건 추가 요구사항*
