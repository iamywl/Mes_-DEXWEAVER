# DEXWEAVER MES 사용자 설명서

> **DEXWEAVER MES v4.0** | Manufacturing Execution System
> 최종 업데이트: 2026-02-27

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [접속 및 로그인](#2-접속-및-로그인)
3. [메뉴 구성](#3-메뉴-구성)
4. [Dashboard (대시보드)](#4-dashboard-대시보드)
5. [Items (품목 관리)](#5-items-품목-관리)
6. [BOM (자재명세서)](#6-bom-자재명세서)
7. [Process (공정 관리)](#7-process-공정-관리)
8. [Equipment (설비 관리)](#8-equipment-설비-관리)
9. [Plans (생산계획)](#9-plans-생산계획)
10. [Work Order (작업지시)](#10-work-order-작업지시)
11. [Quality (품질 관리)](#11-quality-품질-관리)
12. [Inventory (재고 관리)](#12-inventory-재고-관리)
13. [AI Center (AI 분석)](#13-ai-center-ai-분석)
14. [Reports (리포트)](#14-reports-리포트)
15. [Network / Infra / K8s (인프라 모니터링)](#15-network--infra--k8s-인프라-모니터링)
16. [권한 관리](#16-권한-관리)
17. [FAQ 및 문제 해결](#17-faq-및-문제-해결)

---

## 1. 시스템 개요

DEXWEAVER MES는 제조 현장의 생산 계획부터 실적, 품질, 재고까지 전 과정을 관리하는 **통합 제조 실행 시스템**입니다.

### 주요 특징

| 특징 | 설명 |
|------|------|
| **14개 메뉴** | 기준정보, 생산, 품질, 재고, AI 분석, 인프라 모니터링 |
| **40+ API** | RESTful API 기반 백엔드 (FastAPI) |
| **5종 AI 엔진** | 수요예측(Prophet), 일정최적화(OR-Tools), 불량예측(XGBoost), 고장예측(IsolationForest), 분석인사이트 |
| **역할 기반 권한** | admin / manager / worker / viewer 4단계 접근 제어 |
| **JWT 인증** | 모든 API에 백엔드 토큰 인증 적용 (KISA 보안 기준) |
| **LOT 추적성** | 완제품 LOT → 원자재 → 설비 → 작업자 역추적 |
| **실시간 모니터링** | K8s Pod 상태, 인프라 CPU/메모리, 네트워크 토폴로지 |

### 접속 정보

| 서비스 | URL |
|--------|-----|
| 웹 UI (프론트엔드) | `http://<서버IP>:30173` |
| API 문서 (Swagger) | `http://<서버IP>:30461/api/docs` |
| 건강체크 (Health) | `http://<서버IP>:30461/api/health` |

---

## 2. 접속 및 로그인

### 2.1 로그인

1. 웹 브라우저에서 `http://<서버IP>:30173`에 접속합니다.
2. **Login** 탭에서 User ID와 Password를 입력합니다.
3. **Login** 버튼을 클릭합니다.

### 2.2 테스트 계정

| 계정 | 비밀번호 | 역할 | 권한 |
|------|----------|------|------|
| `admin` | `admin1234` | 관리자 | 모든 메뉴 읽기/쓰기 |
| `mgr01` | `mgr1234` | 관리자 | 모든 메뉴 읽기/쓰기 |
| `mgr02` | `mgr1234` | 관리자 | 품질/리포트/대시보드 |
| `worker01` | `worker1234` | 작업자 | 생산계획/작업지시/재고 |
| `worker02` | `worker1234` | 작업자 | 작업지시/설비 |
| `worker03` | `worker1234` | 작업자 | 작업지시/품질(조회) |
| `worker04` | `worker1234` | 작업자 | 품질/작업지시(조회) |
| `worker05` | `worker1234` | 작업자 | 재고/작업지시(조회) |
| `viewer01` | `viewer1234` | 조회전용 | 대시보드/리포트 (조회만) |
| `viewer02` | `viewer1234` | 조회전용 | 대시보드/재고 (조회만) |

### 2.3 회원가입

1. 로그인 화면에서 **Register** 탭을 클릭합니다.
2. User ID, Password, 이름, 이메일, 역할을 입력합니다.
3. **Register** 버튼을 클릭하면 계정이 생성됩니다.
4. 생성된 계정으로 **Login** 탭에서 로그인합니다.

### 2.4 로그아웃

- 화면 우측 상단의 **Logout** 버튼을 클릭합니다.

---

## 3. 메뉴 구성

로그인 후 좌측 사이드바에 메뉴가 표시됩니다. 사용자 권한에 따라 표시되는 메뉴가 다릅니다.

| 카테고리 | 메뉴 | 설명 |
|----------|------|------|
| 대시보드 | Dashboard | 생산/설비 현황 종합 대시보드 |
| 기준정보 | Items | 품목(제품/원자재) 마스터 관리 |
| | BOM | 자재명세서 (정전개/역전개) |
| | Process | 공정 마스터 및 라우팅 관리 |
| | Equipment | 설비 등록/상태/가동률 관리 |
| 생산관리 | Plans | 생산계획 수립 및 진척 관리 |
| | Work Order | 작업지시 및 실적 등록 |
| 품질/재고 | Quality | 품질기준/검사/불량 관리 |
| | Inventory | 입고/출고/재고 현황 |
| AI 분석 | AI Center | 수요예측, 불량예측, 고장예측 |
| 리포트 | Reports | 생산/품질 보고서, AI 인사이트 |
| 인프라 | Network | 네트워크 토폴로지 및 트래픽 |
| | Infra | 서버 CPU/메모리 모니터링 |
| | K8s | Kubernetes Pod 관리 |

---

## 4. Dashboard (대시보드)

### 4.1 화면 구성

대시보드는 제조 현장의 전체 상태를 한눈에 보여줍니다.

- **생산 현황 카드**: 오늘의 생산 목표, 달성률, 불량률, 가동률
- **생산계획 테이블**: 진행 중인 생산계획 목록과 진척률
- **설비 현황**: 전체 설비의 가동/정지/고장 상태

### 4.2 주요 지표

| 지표 | 설명 |
|------|------|
| Production | 금일 총 생산 수량 |
| Achievement | 계획 대비 달성률 (%) |
| Defect Rate | 전체 불량률 (%) |
| Uptime | 설비 평균 가동률 (%) |

---

## 5. Items (품목 관리)

### 5.1 품목 조회

- **필터**: 카테고리(완제품/원자재/반제품/부자재), 검색어로 필터링
- **테이블**: 품목코드, 품목명, 카테고리, 단위, 규격, 안전재고 표시

### 5.2 품목 등록

1. **+ New Item** 버튼을 클릭합니다.
2. 모달 창에서 다음 정보를 입력합니다:
   - **Name**: 품목명 (필수)
   - **Category**: 완제품(PRODUCT) / 원자재(MATERIAL) / 반제품(SEMI) / 부자재(SUB) 선택
   - **Unit**: 단위 (EA, KG, M 등)
   - **Spec**: 규격
   - **Safety Stock**: 안전재고 수량
3. **Register** 버튼을 클릭하면 품목코드(ITEM-NNN)가 자동 생성됩니다.

---

## 6. BOM (자재명세서)

### 6.1 탭 구성

| 탭 | 설명 |
|----|------|
| **BOM List** | BOM 전체 목록 (부모품목 → 자식품목, 소요량, 손실률) |
| **BOM Tree** | 특정 품목을 선택하면 하위 자재를 트리 구조로 전개 |
| **Where Used** | 특정 자재가 어떤 상위 품목에 사용되는지 역전개 |
| **BOM Summary** | BOM 통계 요약 |

### 6.2 BOM 등록

1. **+ New BOM** 버튼을 클릭합니다.
2. 모달 창에서 입력합니다:
   - **Parent Item**: 상위 품목 선택
   - **Child Item**: 하위 자재 선택
   - **Qty per Unit**: 단위당 소요량
   - **Loss Rate**: 손실률 (소수, 예: 0.02 = 2%)
3. **Register** 버튼을 클릭합니다.

### 6.3 BOM 전개 (Tree)

1. **BOM Tree** 탭을 클릭합니다.
2. 드롭다운에서 대상 품목을 선택합니다.
3. 해당 품목에 필요한 모든 하위 자재가 트리 구조로 표시됩니다.
4. 필요 수량을 입력하면 소요량이 자동 계산됩니다.

### 6.4 역전개 (Where Used)

1. **Where Used** 탭을 클릭합니다.
2. 특정 자재를 선택하면, 해당 자재를 사용하는 상위 품목 목록이 표시됩니다.

---

## 7. Process (공정 관리)

### 7.1 탭 구성

| 탭 | 설명 |
|----|------|
| **Process Master** | 공정 목록 (공정코드, 공정명, 표준시간, 설비) |
| **Routing Viewer** | 품목별 공정순서(라우팅) 조회 |

### 7.2 공정 등록

1. **+ New Process** 버튼을 클릭합니다.
2. 입력 항목:
   - **Process Name**: 공정명 (필수)
   - **Standard Time (min)**: 표준 작업시간 (분)
   - **Description**: 공정 설명
   - **Equipment**: 해당 공정에 사용하는 설비 선택
3. **Register**를 클릭합니다.

### 7.3 라우팅 등록

1. **+ New Routing** 버튼을 클릭합니다.
2. 입력 항목:
   - **Item**: 라우팅 대상 품목 선택
   - **Process Steps**: 공정 순서를 지정합니다
     - 각 행에서 공정을 선택하고 Cycle Time(분)을 입력합니다
     - **+ Add Step** 버튼으로 공정 추가
     - **x** 버튼으로 공정 삭제
3. **Register**를 클릭합니다.

---

## 8. Equipment (설비 관리)

### 8.1 설비 조회

- **필터**: 상태(RUNNING/STOP/DOWN), 공정별 필터링
- **테이블**: 설비코드, 설비명, 공정, 시간당 생산능력, 상태, 설치일

### 8.2 설비 등록

1. **+ New Equipment** 버튼을 클릭합니다.
2. 입력 항목:
   - **Equipment Name**: 설비명 (필수)
   - **Process**: 소속 공정 선택
   - **Capacity per Hour**: 시간당 생산능력
   - **Install Date**: 설치일자
3. **Register**를 클릭합니다. 설비코드(EQP-NNN)가 자동 생성됩니다.

### 8.3 설비 상태 변경

1. **Change Status** 버튼을 클릭합니다.
2. 입력 항목:
   - **Equipment**: 대상 설비 선택
   - **Status**: RUNNING(가동) / STOP(정지) / DOWN(고장) 선택
   - **Reason**: 변경 사유
   - **Worker ID**: 작업자 ID
3. **Update**를 클릭합니다.

> **비가동 시간 자동계산**: 설비가 DOWN/STOP에서 RUNNING으로 변경되면, 비가동 시간(분)이 자동으로 계산되어 표시됩니다.

### 8.4 가동률 대시보드

- 설비 목록에 **Uptime Today** 컬럼이 표시됩니다.
- 금일 0시부터 현재까지의 가동 시간 비율(%)로 계산됩니다.
- 현재 작업 중인 작업지시(Current Job)도 함께 표시됩니다.

---

## 9. Plans (생산계획)

### 9.1 생산계획 조회

- **필터**: 상태(WAIT/PROGRESS/DONE), 우선순위(HIGH/MID/LOW), 검색어
- **테이블**: 계획번호, 품목명, 수량, 납기일, 상태, 우선순위, 진척률(%)

### 9.2 생산계획 등록

1. **+ New Plan** 버튼을 클릭합니다.
2. 입력 항목:
   - **Item**: 생산할 품목 선택 (필수)
   - **Plan Qty**: 생산 계획 수량 (필수)
   - **Due Date**: 납기일 (필수)
   - **Priority**: 우선순위 (HIGH/MID/LOW)
3. **Register**를 클릭합니다.

### 9.3 진척률 확인

- 생산계획에 연계된 작업지시의 실적(양품 수량)이 자동 집계됩니다.
- 진척률 = (양품 수량 합계 / 계획 수량) x 100%

### 9.4 AI 일정 최적화

1. **Optimize Schedule** 버튼을 클릭합니다.
2. 최적화할 생산계획을 체크박스로 선택합니다.
3. **Optimize** 버튼을 클릭합니다.
4. AI가 최적 일정을 계산하여 다음을 표시합니다:
   - **Makespan**: 전체 소요시간 (분)
   - **Utilization**: 설비 활용률 (%)
   - **Gantt Chart**: 설비별 작업 배치를 시각적으로 표시
   - **Schedule Table**: 상세 일정표 (순서, 계획, 설비, 시작/종료/소요시간)

> **AI 엔진**: OR-Tools CP-SAT 제약 프로그래밍 솔버 사용. 설비 배정, 작업 비중첩, 우선순위 가중치를 고려하여 최적해를 탐색합니다.

---

## 10. Work Order (작업지시)

### 10.1 작업지시 조회

- **필터**: 상태(WAIT/WORKING/DONE), 검색어
- **테이블**: 작업지시번호, 작업일자, 계획수량, 양품/불량, 상태, 작업자

### 10.2 작업지시 등록

1. **+ New Work Order** 버튼을 클릭합니다.
2. 입력 항목:
   - **Plan**: 연계할 생산계획 선택
   - **Work Date**: 작업 예정일
   - **Equipment**: 사용 설비 선택
3. **Register**를 클릭합니다.

### 10.3 작업 실적 등록

1. **+ Record Result** 버튼을 클릭합니다.
2. 입력 항목:
   - **Work Order**: 대상 작업지시 선택
   - **Good Qty**: 양품 수량
   - **Defect Qty**: 불량 수량
   - **Defect Code**: 불량 코드 (예: DEF-001)
   - **Worker ID**: 작업자 ID
   - **Start/End Time**: 작업 시작/종료 시간
3. **Record**를 클릭합니다.

> 실적 등록 시 작업지시의 상태가 자동으로 WORKING으로 변경되고, 생산계획의 진척률이 갱신됩니다.

---

## 11. Quality (품질 관리)

### 11.1 불량 현황 조회

- 기간/품목별 불량 현황을 테이블로 조회합니다.
- 불량률, 불량 유형, 검사 결과(PASS/FAIL)를 확인할 수 있습니다.

### 11.2 품질기준 등록

1. **+ Quality Standard** 버튼을 클릭합니다.
2. 입력 항목:
   - **Item**: 대상 품목 선택
   - **Check Items**: 검사 항목을 추가합니다
     - **Name**: 검사 항목명 (예: 두께, 강도)
     - **Type**: NUMERIC / VISUAL / FUNCTIONAL
     - **Min / Max**: 허용 범위 (숫자형일 때)
     - **Unit**: 단위 (mm, kg 등)
     - **+ Add Check**로 항목 추가
3. **Register**를 클릭합니다.

### 11.3 검사 실행

1. **+ New Inspection** 버튼을 클릭합니다.
2. 입력 항목:
   - **Inspection Type**: 수입검사(INCOMING) / 공정검사(PROCESS) / 출하검사(OUTGOING)
   - **Item**: 검사 대상 품목
   - **Lot No**: LOT 번호 (예: LOT-20260224-001)
   - **Inspector ID**: 검사자 ID
   - **Measurement Results**: 측정값 입력
     - **Check name**: 검사 항목명
     - **Value**: 측정값
     - **+ Add Result**로 항목 추가
3. **Submit Inspection**을 클릭합니다.

> **자동 판정**: 등록된 품질기준의 허용 범위(Min~Max)와 측정값을 비교하여 자동으로 PASS/FAIL 판정을 수행합니다. 불합격 항목이 있으면 결과에 표시됩니다.

---

## 12. Inventory (재고 관리)

### 12.1 재고 현황 조회

- **필터**: 창고별, 카테고리별, 검색어
- **테이블**: 품목코드, 품목명, LOT번호, 수량, 창고, 위치
- 안전재고 미만 품목은 **LOW** 뱃지로 경고 표시

### 12.2 입고 처리

1. **+ Receive (입고)** 버튼을 클릭합니다.
2. 입력 항목:
   - **Item**: 입고할 품목 선택
   - **Qty**: 입고 수량
   - **Supplier**: 공급업체명
   - **Warehouse**: 창고 코드 (예: WH-A)
   - **Location**: 위치 (예: A-01-01)
3. **Submit**을 클릭합니다.

### 12.3 출고 처리

1. **+ Issue (출고)** 버튼을 클릭합니다.
2. 입력 항목:
   - **Item**: 출고할 품목 선택
   - **Qty**: 출고 수량
   - **Out Type**: 출고 유형 (출하SHIP / 사용USE / 이동MOVE)
   - **Ref ID**: 참조번호 (출하전표, 작업지시 번호 등)
3. **Submit**을 클릭합니다.

---

## 13. AI Center (AI 분석)

AI Center에서는 3가지 AI 예측 기능을 사용할 수 있습니다.

### 13.1 수요예측 (Demand Forecast)

**AI 엔진**: Facebook Prophet (시계열 예측)

1. **Demand Prediction** 섹션에서 품목코드를 선택합니다.
2. **Predict** 버튼을 클릭합니다.
3. 결과:
   - **예측 수량**: 향후 기간별 예상 수요량
   - **신뢰 구간**: 상한/하한 범위
   - **사용 모델**: Prophet 또는 LinearRegression (데이터 부족 시)

> 충분한 과거 출하/생산 데이터가 있을 때 더 정확한 예측이 가능합니다.

### 13.2 불량예측 (Defect Prediction)

**AI 엔진**: XGBoost + SHAP (설명가능 AI)

1. **Defect Prediction** 섹션에서 공정 파라미터를 입력합니다:
   - **Temperature**: 온도 (예: 200)
   - **Pressure**: 압력 (예: 10)
   - **Speed**: 속도 (예: 50)
   - **Humidity**: 습도 (예: 55)
2. **Predict** 버튼을 클릭합니다.
3. 결과:
   - **Defect Probability**: 불량 발생 확률 (%)
   - **Risk Level**: HIGH / MEDIUM / LOW
   - **Factor Analysis**: 각 파라미터가 불량에 기여하는 정도 (SHAP 값)
   - **Recommendation**: 한국어 조치 권고사항

### 13.3 고장예측 (Failure Prediction)

**AI 엔진**: IsolationForest (비지도 이상탐지)

1. **Failure Prediction** 섹션에서 설비를 선택하고 센서값을 입력합니다:
   - **Equipment**: 대상 설비
   - **Vibration**: 진동값
   - **Temperature**: 온도
   - **Current**: 전류 (A)
2. **Predict** 버튼을 클릭합니다.
3. 결과:
   - **Failure Probability**: 고장 확률 (%)
   - **Anomaly Score**: 이상 점수 (0=정상, 1=이상)
   - **Remaining Life**: 예상 잔여 수명 (시간)
   - **Factor Analysis**: 각 센서값의 Z-Score 기반 기여도
   - **Recommendation**: 한국어 조치 권고사항

> 센서 데이터가 10건 이상 축적되면 IsolationForest 모델이 자동으로 학습됩니다. 이전에는 규칙 기반(RuleBased)으로 예측합니다.

---

## 14. Reports (리포트)

### 14.1 생산실적 보고서

- 기간별 생산 실적을 집계합니다.
- **지표**: 총 생산량, 양품 수량, 불량 수량, 불량률, 달성률
- **그룹**: 일별 / 품목별 그룹핑 가능

### 14.2 품질 보고서

- 기간별 품질 현황을 보여줍니다.
- **Cpk (공정능력지수)**: 통계적 공정능력 지수
  - Cpk = min(CPU, CPL) / 3σ
  - Cpk > 1.33: 공정능력 충분
  - Cpk > 1.0: 보통
  - Cpk < 1.0: 공정능력 부족 (개선 필요)
- **관리도 데이터**: UCL(상한), CL(중심), LCL(하한) 표시

### 14.3 AI 인사이트

- **Analyze** 버튼을 클릭하면 AI가 4가지 영역을 종합 분석합니다:

| 분석 영역 | 내용 |
|-----------|------|
| **생산** | 계획 달성률 미달 품목, 주간 생산량 추세 |
| **설비** | 고장 설비, 장기 비가동, 센서 이상 감지 |
| **품질** | 불량률 추세, 높은 불량률 품목 |
| **재고** | 안전재고 미달 품목 |

- **KPIs**: 달성률, 설비가동률, 불량률, 재고부족 품목 수 등 핵심 지표
- **Issues**: 심각도(CRITICAL/WARNING/MEDIUM) 순으로 정렬된 이슈 목록
- **Recommendations**: 각 이슈에 대한 한국어 조치 권고사항

---

## 15. Network / Infra / K8s (인프라 모니터링)

### 15.1 Network (네트워크)

- **Service Map**: Kubernetes 서비스 간 연결 관계를 시각적으로 표시
- **Flow Table**: Hubble에서 수집한 네트워크 트래픽 흐름
- **필터**: Verdict(FORWARDED/DROPPED), Protocol, Namespace

### 15.2 Infra (인프라)

- **CPU 사용률**: 현재 서버 CPU 사용률 (%)
- **메모리 사용률**: 현재 서버 메모리 사용률 (%)
- 5초 간격으로 자동 갱신

### 15.3 K8s (Kubernetes)

- **Pod 목록**: 현재 실행 중인 모든 Pod의 상태
- **Pod 상세**: 이름, 상태(Running/Pending/Error), 재시작 횟수, IP
- **로그 조회**: Pod 선택 시 해당 Pod의 실시간 로그 표시

---

## 16. 권한 관리

### 16.1 역할별 기본 권한

| 역할 | 설명 | 기본 권한 |
|------|------|-----------|
| **admin** | 시스템 관리자 | 모든 메뉴 읽기/쓰기 + 사용자/권한 관리 |
| **worker** | 현장 작업자 | 할당된 메뉴만 접근 (권한 설정에 따름) |
| **viewer** | 조회 전용 | 할당된 메뉴 조회만 가능 (등록/수정 불가) |

### 16.2 메뉴별 권한 설정 (admin 전용)

1. 사이드바 하단의 **Permissions** 버튼을 클릭합니다.
2. 대상 사용자를 선택합니다.
3. 각 메뉴별로 **Read** (조회) / **Write** (등록/수정) 체크박스를 설정합니다.
4. **Select All** / **Clear All** 버튼으로 일괄 설정 가능합니다.
5. **Save Permissions** 버튼을 클릭하여 저장합니다.

### 16.3 사용자 등록 (admin 전용)

1. 사이드바 하단의 **Register User** 버튼을 클릭합니다.
2. User ID, Password, 이름, 이메일, 역할을 입력합니다.
3. **Register** 버튼을 클릭합니다.

### 16.4 권한이 없는 메뉴

- 읽기 권한이 없는 메뉴는 사이드바에 표시되지 않습니다.
- 쓰기 권한이 없는 메뉴에서는 등록/수정 버튼이 표시되지 않습니다.

---

## 17. FAQ 및 문제 해결

### Q1. 로그인이 되지 않습니다.

**A**: 다음을 확인하세요:
- User ID와 Password가 정확한지 확인합니다.
- 서버가 정상 구동 중인지 확인합니다: `kubectl get pods`
- API 서버가 시작 중일 수 있습니다 (pip install에 약 5~6분 소요). 잠시 후 다시 시도하세요.

### Q2. 페이지가 빈 화면으로 나옵니다.

**A**: 브라우저의 캐시를 삭제하고 새로고침(Ctrl+Shift+R)합니다. 문제가 지속되면:
```bash
# 프론트엔드 재배포
cd /home/c1_master1/MES_PROJECT/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend
```

### Q3. 502 Bad Gateway 에러가 발생합니다.

**A**: 백엔드 서버가 아직 시작 중이거나 에러가 발생한 상태입니다:
```bash
# 백엔드 로그 확인
kubectl logs deployment/mes-api --tail=30

# 아직 pip install 중이면 기다립니다 (최초 5~6분 소요)
# 에러가 있으면 코드 수정 후 재배포:
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code \
  --from-file=app.py=/home/c1_master1/MES_PROJECT/app.py \
  --from-file=/home/c1_master1/MES_PROJECT/api_modules/
kubectl rollout restart deployment mes-api
```

### Q4. AI 예측 결과가 나오지 않습니다.

**A**: AI 모델은 충분한 데이터가 필요합니다:
| AI 기능 | 필요 데이터 | 최소 건수 |
|---------|-------------|-----------|
| 수요예측 (Prophet) | 출하/생산 이력 | 10건 이상 |
| 불량예측 (XGBoost) | 불량 이력 (defect_history) | 10건 이상 |
| 고장예측 (IsolationForest) | 센서 데이터 (equip_sensors) | 10건 이상 |

데이터가 부족하면 규칙 기반(fallback) 모델이 자동으로 사용됩니다.

### Q5. 특정 메뉴가 보이지 않습니다.

**A**: 현재 로그인한 계정의 권한을 확인하세요. admin 계정으로 로그인하여 **Permissions** 메뉴에서 해당 사용자에게 메뉴 권한을 부여할 수 있습니다.

### Q6. 시스템 전체를 재시작하고 싶습니다.

**A**: 초기화 스크립트를 실행합니다:
```bash
sudo bash /home/c1_master1/MES_PROJECT/init.sh
```
이 스크립트는 DB, Keycloak, 백엔드, 프론트엔드를 모두 재배포합니다. 기존 데이터(PostgreSQL)는 유지됩니다.

---

## 부록: AI 엔진 상세

| AI 엔진 | 라이브러리 | 용도 | 알고리즘 |
|---------|-----------|------|----------|
| **Prophet** | prophet >= 1.1 | 수요예측 | 시계열 분해 (트렌드 + 계절성 + 휴일) |
| **OR-Tools** | ortools >= 9.8 | 일정최적화 | CP-SAT 제약 프로그래밍 (장비배정, 비중첩, 우선순위) |
| **XGBoost** | xgboost >= 2.0 | 불량예측 | Gradient Boosting + SHAP 설명가능 AI |
| **IsolationForest** | scikit-learn >= 1.3 | 고장예측 | 비지도 이상탐지 + Z-Score 기여도 분석 |
| **Rule Engine** | 내장 | 종합인사이트 | 4영역(생산/설비/품질/재고) KPI 분석 |

---

## 부록: API 전체 목록

### 인증 (Auth)
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/auth/login` | 로그인 (JWT 토큰 발급) |
| POST | `/api/auth/register` | 회원가입 |
| GET | `/api/auth/users` | 사용자 목록 (admin) |
| GET | `/api/auth/permissions/{user_id}` | 사용자 권한 조회 |
| PUT | `/api/auth/permissions/{user_id}` | 사용자 권한 수정 (admin) |

### 기준정보 (Master Data)
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/items` | 품목 목록 |
| POST | `/api/items` | 품목 등록 |
| GET | `/api/items/{item_code}` | 품목 상세 |
| PUT | `/api/items/{item_code}` | 품목 수정 |
| DELETE | `/api/items/{item_code}` | 품목 삭제 |
| GET | `/api/bom` | BOM 목록 |
| POST | `/api/bom` | BOM 등록 |
| GET | `/api/bom/summary` | BOM 통계 |
| GET | `/api/bom/explode/{item_code}` | BOM 전개 |
| GET | `/api/bom/where-used/{item_code}` | BOM 역전개 |
| GET | `/api/processes` | 공정 목록 |
| POST | `/api/processes` | 공정 등록 |
| GET | `/api/routings` | 라우팅 요약 목록 |
| POST | `/api/routings` | 라우팅 등록 |
| GET | `/api/routings/{item_code}` | 품목별 라우팅 조회 |

### 설비 (Equipment)
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/equipments` | 설비 목록 |
| POST | `/api/equipments` | 설비 등록 |
| GET | `/api/equipments/status` | 설비 상태 대시보드 (가동률) |
| PUT | `/api/equipments/{code}/status` | 설비 상태 변경 |

### 생산관리 (Production)
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/plans` | 생산계획 목록 |
| POST | `/api/plans` | 생산계획 등록 |
| GET | `/api/plans/{plan_id}` | 생산계획 상세 |
| GET | `/api/work-orders` | 작업지시 목록 |
| POST | `/api/work-orders` | 작업지시 등록 |
| GET | `/api/work-orders/{wo_id}` | 작업지시 상세 |
| POST | `/api/work-results` | 작업실적 등록 |
| GET | `/api/dashboard/production` | 생산 대시보드 |

### 품질 (Quality)
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/quality/standards` | 품질기준 등록 |
| POST | `/api/quality/inspections` | 검사 실행 |
| GET | `/api/quality/defects` | 불량 현황 조회 |

### 재고 (Inventory)
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/inventory` | 재고 현황 |
| POST | `/api/inventory/in` | 입고 처리 |
| POST | `/api/inventory/out` | 출고 처리 |
| POST | `/api/inventory/move` | 재고 이동 |

### AI 분석
| Method | URL | 설명 |
|--------|-----|------|
| POST | `/api/ai/demand-forecast` | 수요예측 (Prophet) |
| GET | `/api/ai/demand-prediction/{item_code}` | 수요예측 간편 조회 |
| POST | `/api/ai/schedule-optimize` | AI 일정최적화 (OR-Tools) |
| POST | `/api/ai/defect-predict` | 불량예측 (XGBoost+SHAP) |
| POST | `/api/ai/failure-predict` | 고장예측 (IsolationForest) |
| POST | `/api/ai/insights` | AI 종합 인사이트 |

### 리포트 (Reports)
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/reports/production` | 생산실적 보고서 |
| GET | `/api/reports/quality` | 품질 보고서 (Cpk) |

### 인프라 (Infrastructure)
| Method | URL | 설명 |
|--------|-----|------|
| GET | `/api/infra/status` | CPU/메모리 상태 |
| GET | `/api/k8s/pods` | Pod 목록 |
| GET | `/api/k8s/logs/{name}` | Pod 로그 |
| GET | `/api/network/topology` | 네트워크 토폴로지 |
| GET | `/api/network/hubble-flows` | Hubble 트래픽 흐름 |
| GET | `/api/network/service-map` | 서비스 맵 |

---

**KNU Smart Factory MES v5.5**
**경북대학교 컴퓨터학부 클라우드컴퓨팅 연구실**
**최종 업데이트: 2026-02-24**
