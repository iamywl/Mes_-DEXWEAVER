# ADR-002: 문서 전수 점검 결과 및 잔여 이슈

| 항목 | 내용 |
|------|------|
| **상태** | 1차 조치 완료, 잔여 이슈 추적 중 |
| **작성일** | 2026-02-27T17:30:00 KST |
| **작성자** | QA팀 |
| **대상** | 평가 보고서 10건, README, USER_MANUAL |

---

## 1. 점검 배경

2026-02-27 전체 프로젝트 문서 및 평가 보고서에 대한 정합성 점검을 수행하였다. 4개 병렬 에이전트를 통해 계획서(3건), 테스트 결과(3건), 인증 평가(5건), 루트 문서(3건)를 교차 검증하였다.

---

## 2. 1차 조치 완료 항목

### 2.1 제거한 상이 문서 (2건)

| 제거 파일 | 사유 | 조치일 |
|-----------|------|--------|
| `BLACKBOX_TEST_REPORT_20260227.md` | 50건/98% → 199건 종합테스트에 완전 포함. 응답시간·TPS 수치가 종합테스트 JSON과 충돌 | 2026-02-27T17:00 |
| `SW_QUALITY_VERIFICATION_REPORT_20260227.md` | 86건/100.0점 주장 → 실제 JSON(199건/99.0%, 2건 FAIL)과 정면 충돌. 테스트 수 축소 및 실패 미반영 | 2026-02-27T17:00 |

### 2.2 수정 완료한 팩트 오류

| 항목 | 수정 전 | 수정 후 | 영향 문서 |
|------|---------|---------|-----------|
| 시스템 버전 | v4.3 | v4.0 (app.py 기준) | 전 보고서 8건 |
| DB 테이블 수 | 12 / 19 혼재 | 21개 (init.sql 실측) | VV_PLAN, TEST_PLAN, SP, FINAL |
| 백엔드 모듈 수 | 24 | 18개 (app.py import 기준) | VV_PLAN, FINAL |
| 코드 줄 수(LoC) | 4,726 | 4,780 (실측) | VV_PLAN, TEST_PLAN, RTM, FINAL |
| PostgreSQL 버전 | 17 (ISO25010) | 15 (전 문서 통일) | ISO25010_31CHAR |
| 시스템명 | Smart Factory MES | DEXWEAVER MES | ISO25010_31CHAR |
| API 엔드포인트 수 | 37+ / 40+ | 46개 (실측) | README, FINAL |
| 인증 기술 | Keycloak OIDC/PKCE | JWT (PyJWT + bcrypt) | README |
| Swagger URL | /docs | /api/docs | README |
| USER_MANUAL 푸터 | v5.5 / 2026-02-24 | v4.0 / 2026-02-27 | USER_MANUAL |

### 2.3 수정 완료한 오해 표현

| 수정 전 | 수정 후 | 사유 |
|---------|---------|------|
| "GS인증 1등급 적합" | "GS인증 1등급 기준 적합 (자체평가)" | 공식 TTA 인증이 아닌 자체 평가임을 명시 |
| "SP인증 Level 2 충족" | "SP Level 2 기준 충족 (자체진단)" | 공식 NIPA 인증이 아닌 자체 진단임을 명시 |
| "품질 적합성이 인증됨" | "자체 검증을 통해 확인됨" | "인증"은 제3자 공식 심사를 의미하므로 "확인"으로 변경 |
| KISA "12항목" | "23항목" | 실제 검증한 Q4 보안 TC 수 기준 |
| 열화율 기준 50% | 20% | IQ/OQ/PQ·FAT/SAT 보고서와 일치시킴 |
| SP 영역별 항목수 (2/4/3/2/2=13) | (3/5/4/3/2=17) | SP 보고서 원본과 일치시킴 |

---

## 3. 잔여 이슈 (미조치)

### 3.1 [HIGH] 요구사항 수 불일치

| 출처 | 요구사항 수 |
|------|------------|
| `Requirements_Specification.md` | REQ-001 ~ REQ-034 = **34건** |
| 평가 보고서 전체 | FN-001 ~ FN-038 = **38건** (+ NF 12 + SEC 12 = 62건) |
| `app.py` 주석 | FN-001 ~ FN-038 |

**고민 사항**: 요구사항 명세서(34건)와 보고서(38건)가 4건 차이 난다. FN-035~038은 구현은 되어있으나 Requirements_Specification.md에 반영되지 않았을 가능성이 높다.

**권고**: Requirements_Specification.md를 업데이트하여 FN-035~038(AI 엔진 4종 또는 LOT 추적 등)을 추가하거나, 보고서의 FN 수를 34건으로 하향 조정해야 한다.

### 3.2 [MEDIUM] RTM 모듈별 줄 수 부정확

RTM Section 5의 모듈별 줄 수 추정치가 실측과 대폭 차이난다.

| 모듈 | RTM 기재 | 실측 | 차이 |
|------|---------|------|------|
| mes_auth.py | ~280 | 374 | +94 |
| mes_reports.py | ~350 | 647 | +297 |
| mes_equipment.py | ~350 | 415 | +65 |
| mes_plan.py | ~280 | 384 | +104 |
| mes_work.py | ~300 | 380 | +80 |
| k8s_service.py | ~180 | 272 | +92 |

**권고**: RTM Section 5 역방향 추적표의 줄 수를 실측값으로 교체.

### 3.3 [MEDIUM] ISO 25010 표준 연도 문제

보고서에서 **ISO/IEC 25010:2023**을 인용하면서 **8대 특성 + 31개 부특성** 모델을 사용한다. 그러나:
- 2011 버전: 8대 특성, 31개 부특성
- 2023 개정판: **9대 특성** (Safety 추가), 부특성 구조 변경

현재 사용 중인 모델은 실질적으로 2011 버전 구조이다.

**권고**: 표준 인용을 `ISO/IEC 25010:2011`로 변경하거나, 2023 모델에 맞춰 Safety 특성을 추가 평가해야 한다.

### 3.4 [MEDIUM] VV_PLAN에 테스트 결과가 포함됨

V&V **계획서**에 실제 테스트 결과(98%, 45.3 TPS 등)가 기재되어 있다. IEEE 1012에서 계획서(Plan)는 "무엇을 할 것인지"를 정의하는 문서이므로, 결과 수치는 별도 V&V 결과 보고서에 기재하는 것이 정확하다.

**권고**: VV_PLAN에서 결과 수치를 제거하고, 결과는 ISO25010_31CHAR_REPORT 또는 FINAL_QUALITY_CERTIFICATION에서 참조하도록 변경.

### 3.5 [LOW] Keycloak 인프라 잔재

상세 내용은 [ADR-001](ADR-001_auth_keycloak_vs_jwt.md) 참조.
- `infra/keycloak.yaml` — K8s 매니페스트 존재
- `setup-keycloak.sh` — 초기화 스크립트 존재
- `frontend/package.json` — `keycloak-js` 패키지 존재
- `README.md` — `setup-keycloak.sh` 언급 존재

**권고**: JWT 커스텀 유지 결정 시 삭제 정리. Keycloak 전환 계획 시 유지.

### 3.6 [LOW] api_modules/ 미사용 모듈 11개

app.py에서 import하지 않는 Python 파일이 11개 존재한다:
```
mes_execution.py, mes_logic.py, mes_logistics.py, mes_master.py,
mes_material_receipt.py, mes_performance.py, mes_production.py,
mes_service.py, mes_work_order.py
```

**권고**: 사용하지 않는 모듈은 삭제하거나 `_deprecated/` 디렉토리로 이동.

### 3.7 [LOW] docker-compose.yml 미문서화

프로젝트 루트에 `docker-compose.yml`이 존재하나 README에는 K8s 배포만 설명되어 있다. Docker Compose 배포 옵션이 문서화되어 있지 않다.

**권고**: README에 Docker Compose 배포 방법 섹션 추가 또는, K8s 전용이라면 docker-compose.yml의 용도(개발용 등)를 명시.

---

## 4. 이슈 우선순위 요약

| 우선순위 | ID | 이슈 | 난이도 |
|---------|-----|------|--------|
| HIGH | 3.1 | 요구사항 수 불일치 (34 vs 38) | 중 |
| MEDIUM | 3.2 | RTM 모듈 줄 수 부정확 | 하 |
| MEDIUM | 3.3 | ISO 25010 표준 연도 (2011 vs 2023) | 하 |
| MEDIUM | 3.4 | VV_PLAN에 결과 수치 혼재 | 중 |
| LOW | 3.5 | Keycloak 잔재 정리 | 하 |
| LOW | 3.6 | 미사용 모듈 11개 | 하 |
| LOW | 3.7 | docker-compose.yml 미문서화 | 하 |
