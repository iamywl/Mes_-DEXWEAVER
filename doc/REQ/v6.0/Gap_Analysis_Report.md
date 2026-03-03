# DEXWEAVER MES v6.0 — 경쟁사 및 국제표준 대비 갭 분석 보고서

> **분석일**: 2026-03-03
> **대상**: v6.0 요구사항 정의서 (REQ-001~051, NFR-001~010) vs 국제표준 + 글로벌 경쟁사
> **분석 기준**: ISA-95, ISA-88, FDA 21 CFR Part 11, IEC 62443, ISO 22400, ISO 9001/IATF 16949
> **비교 경쟁사**: Siemens Opcenter, Rockwell Plex, SAP DMC, Critical Manufacturing, MPDV HYDRA

---

## 1. 국제표준 준수 현황

### 1.1 ISA-95 (IEC 62264) — 제조 엔터프라이즈 시스템

#### Level 모델 커버리지

| ISA-95 Level | 설명 | v6.0 커버리지 | 평가 |
|:---:|--------|-------------|:---:|
| Level 0 | 물리적 공정 (센서/액추에이터) | REQ-042(MQTT), REQ-046(OPC-UA) | 부분 |
| Level 1 | 기본 제어 (PLC/DCS) | REQ-046(OPC-UA)으로 PLC 연동 | 부분 |
| Level 2 | 감시/제어 (SCADA/HMI) | 미정의 — SCADA 연동 부재 | **갭** |
| Level 3 | 제조 운영 관리 (MES) | REQ-001~051 핵심 영역 | 커버 |
| Level 4 | 비즈니스 계획 (ERP) | REQ-045(ERP 연동) Phase 3 | 부분 |

**핵심 갭**: Level 2-3 인터페이스에 **Edge Gateway / Data Historian** 계층 부재. ISA-95는 SCADA→MES 사이에 데이터 문맥화, 버퍼링, Store-and-Forward 기능을 요구하나 현재 센서→MES 직접 연결만 정의됨.

#### Activity Model 충족

| ISA-95 Activity Model | v6.0 매핑 | 충족도 | 잔여 갭 |
|---|---|:---:|---|
| Production Operations | REQ-013~020 | 65% | 자동 디스패칭 규칙 엔진 부재, 자재 역산(Backflush) 미구현 |
| Quality Operations | REQ-021~024, REQ-035~036 | 65% | MSA, FMEA, 제품 출하 판정 워크플로우 부재 |
| Inventory Operations | REQ-025~028, REQ-039 | 55% | 자재 상태 모델(HOLD/QUARANTINE) 부재, WMS 연동 미정의 |
| Maintenance Operations | REQ-040, REQ-031 | 50% | MTTF/MTTR/MTBF 자동 계산 부재, 교정 관리 미구현 |
| Order Processing | REQ-013 | 40% | **고객 주문 관리 미구현, ATP(Available-to-Promise) 부재** |

#### Information Model 갭

- **B2MML 미지원**: ERP↔MES 데이터 교환에 ISA-95 표준 메시지 포맷(B2MML) 미정의
- **자재 상태 모델 부재**: AVAILABLE/HOLD/QUARANTINE/REJECTED 상태 관리 없음
- **Process Segment**: ISA-95 정의의 공정 세그먼트 모델(자원 요구사항 + 파라미터 포함)이 아닌 단순 공정/라우팅만 존재

---

### 1.2 ISA-88 (IEC 61512) — 배치 제어

#### REQ-041 (레시피 관리) ISA-88 평가

| ISA-88 요구사항 | REQ-041 커버리지 | 갭 |
|---|---|---|
| General/Site/Master/Control 레시피 계층 | 단일 레시피만 | **미커버** — 레시피 유형 계층 없음 |
| Procedural Model (Procedure→Unit Procedure→Operation→Phase) | 미정의 | **미커버** — 절차 계층 구조 없음 |
| Control Recipe (배치별 실행 인스턴스) | 미정의 | **미커버** |
| 레시피-장비 능력 매핑 | 미정의 | **미커버** |
| Formula Management (입출력 물질) | parameters로 부분 커버 | 부분 |
| Batch State Machine (Idle/Running/Held/Complete/Stopped/Aborted) | 미구현 | **미커버** |
| 배치 예외 처리 (Hold/Resume/Abort) | 미구현 | **미커버** |
| 전자배치기록 (eBR) 자동 생성 | 미정의 | **미커버** |

**ISA-88 종합: 약 25% 커버**. REQ-041이 레시피 마스터의 기초를 제공하나, 배치 실행 엔진과 절차 계층이 근본적으로 부재.

---

### 1.3 FDA 21 CFR Part 11 — 전자기록/전자서명

#### REQ-049 (감사추적) 평가

| 21 CFR Part 11 요구사항 | v6.0 커버리지 | 충족 |
|---|---|:---:|
| 11.10(a) 시스템 밸리데이션 (IQ/OQ/PQ) | NFR-008 테스트만 | 불충분 |
| 11.10(b) 정확한 기록 생성 | REQ-049 자동 기록 | 커버 |
| 11.10(c) 기록 보호 (무단 변경 방지) | 미정의 | **불충분** |
| 11.10(d) 시스템 접근 제어 | REQ-003 RBAC | 부분 |
| 11.10(e) 감사 추적 | REQ-049 (who/what/when/why) | 커버 |
| 11.50 전자서명 표시 (서명자명+일시+의미) | REQ-049 e_signature 필드 | **갭** — 서명 표시 규격 미상세 |
| 11.70 서명-기록 불가분 연결 | 미정의 | **갭** — 암호학적 연결 방법 미정의 |
| 11.200 비생체 전자서명 (2요소 인증) | 미정의 | **갭** — ID+PW만, 2차 인증 부재 |

**추가 부족사항**:
- 감사추적 불변성(Immutability) 보장 메커니즘 미정의
- 감사추적 보존 기간 정책 부재 (FDA: 최소 문서 수명 기간)
- 시간 동기화(NTP) 보장 미명시
- GAMP 5 기반 시스템 밸리데이션 절차(IQ/OQ/PQ) 미정의

**21 CFR Part 11 종합: 약 40% 커버**

---

### 1.4 IEC 62443 — 산업 사이버보안

| IEC 62443 요구사항 | v6.0 커버리지 | 평가 |
|---|---|:---:|
| Zone/Conduit 모델 | 미정의 | **미커버** |
| Security Level (SL 1-4) | 미정의 | **미커버** |
| FR1: 식별/인증 | REQ-001, REQ-003 | 부분 — MFA, 서비스간 인증 부재 |
| FR2: 사용 제어 | REQ-003 RBAC | 부분 — 최소 권한 원칙 미강제 |
| FR3: 시스템 무결성 | 미정의 | **미커버** |
| FR4: 데이터 기밀성 | 미정의 | **미커버** — TLS/AES 요구사항 없음 |
| FR5: 데이터 흐름 제한 | 미정의 | **미커버** — 네트워크 세그멘테이션 없음 |
| FR6: 시기적절한 이벤트 대응 | REQ-038 알림 | 부분 — 보안 이벤트 탐지/경보 부재 |
| 패치 관리 | 미정의 | **미커버** |
| 사고 대응 절차 | 미정의 | **미커버** |

**IEC 62443 종합: 약 15% 커버**

---

### 1.5 ISO 22400 — 제조 KPI

34개 표준 KPI 중 v6.0 커버 현황:

| ISO 22400 KPI 카테고리 | 정의된 KPI 수 | v6.0 커버 | 미커버 핵심 KPI |
|---|:---:|:---:|---|
| 생산 (7개) | 7 | 1 (OEE) | Worker Efficiency, Throughput Rate, NEE, Utilization Efficiency |
| 품질 (6개) | 6 | 2 (Quality Ratio, Cpk) | **FPY (First Pass Yield)**, Scrap Ratio, Rework Ratio |
| 재고 (5개) | 5 | 0 | **Inventory Turns**, WIP, Finished Goods Ratio |
| 보전 (5개) | 5 | 0 | **MTTF, MTTR, MTBF**, Corrective Maintenance Ratio |
| 시간 (6개) | 6 | 0 | **Production Lead Time, Cycle Time, Setup Time** |
| 환경 (5개) | 5 | 0 | Energy Intensity, Emission Intensity (전체 미구현) |
| **합계** | **34** | **3~4** | **약 30개 미커버** |

**ISO 22400 종합: 약 12% 커버 (34개 중 4개)**

---

### 1.6 ISO 9001:2015 / IATF 16949

| 조항 | v6.0 커버리지 | 갭 |
|---|---|---|
| 7.1.5 모니터링/측정 자원 | 미정의 | **MSA/Gage R&R, 교정 관리 부재** |
| 8.4 외부 공급자 관리 | 미정의 | **공급업체 품질 관리(SQM) 부재** |
| 8.6 제품 출시 | REQ-022 검사 | **제품 출하 판정/보류/처분 워크플로우 부재** |
| 8.7 부적합 출력물 | REQ-036 CAPA | **부적합품 관리(NCR)/MRB 심의 부재** |
| IATF 8.5.6.1 변경관리 | 미정의 | **ECN/ECO 관리 부재** |
| IATF 9.1.1.2 MSA 적용 | 미정의 | **측정 시스템 분석 부재** |

---

## 2. 경쟁사 대비 미커버 기능

### 2.1 Siemens Opcenter 대비

| 분류 | Siemens 기능 | v6.0 상태 | 심각도 |
|---|---|---|:---:|
| 멀티사이트 관리 | 중앙관리/분산실행 아키텍처 | 미정의 | HIGH |
| PLM 연동 | Teamcenter eBOM→mBOM 동기화 | 미정의 | HIGH |
| ECN/ECO | CMII 인증 변경관리 프로세스 | 미정의 | HIGH |
| 3D/AR 작업지시 | 3D 뷰 기반 조립 지시 | 미정의 | MED |
| 로우코드 확장 | Mendix 기반 커스터마이징 | 미정의 | MED |
| LIMS 통합 | Laboratory 네이티브 통합 | 미정의 | MED |
| 전자배치기록(eBR) | Pharma 전용 eBR 모듈 | 미정의 | HIGH |
| SPC 전용모듈 | p/np/c/u 관리도, 게이지 직연결 | REQ-035 X-bar/R만 | MED |
| Industrial Edge | 엣지 데이터 전처리 | 미정의 | MED |
| FMEA/8D/MSA | 종합 품질 도구 세트 | 미정의 | HIGH |

### 2.2 Rockwell Plex 대비

| 분류 | Plex 기능 | v6.0 상태 | 심각도 |
|---|---|---|:---:|
| 멀티테넌트 SaaS | 싱글 인스턴스 멀티테넌트 | 미정의 | HIGH |
| 2,600+ KPI | 사전 정의 KPI 라이브러리 | 약 4개 KPI | HIGH |
| Connected Worker | 인력관리+작업지시 통합 | REQ-044 기본 수준 | MED |
| 전자게이지 직연결 | SPC 수동입력 제거 | 미정의 | MED |
| Elastic MES | 오프라인 운영 + 동기화 | 미정의 | MED |
| HACCP/FSMA | 식품안전 규정 준수 내장 | 미정의 | MED |
| 시리얼 추적 | 개별 단위 시리얼 번호 관리 | LOT 수준만 (REQ-039) | HIGH |
| WO 원가추적 | 작업지시별 실제원가 집계 | 미정의 | MED |

### 2.3 SAP DMC 대비

| 분류 | SAP 기능 | v6.0 상태 | 심각도 |
|---|---|---|:---:|
| S/4HANA 네이티브 | 미들웨어 없이 실시간 교환 | REQ-045 별도 인터페이스 | HIGH |
| SAP EWM 통합 | WMS 네이티브 연동 | 미정의 | HIGH |
| AI 시각검사 | 카메라 기반 자동 결함 감지 | 미정의 | MED |
| POD 프레임워크 | 커스텀 작업자 대시보드 | 미정의 | MED |
| MRP 실시간 연동 | 자재소요계획 자동 연계 | 미정의 | HIGH |
| As-Built 자동생성 | 완제품 이력 자동 편집 | 미정의 | MED |

### 2.4 Critical Manufacturing / MPDV HYDRA

| 기능 | v6.0 상태 | 심각도 |
|---|---|:---:|
| 복합 라우팅 (재진입/분기) | REQ-010 순차만 | MED |
| SPC 자동격리 (auto-hold, auto-equip-down) | REQ-035 알림만 | HIGH |
| 에너지 관리 | 미정의 | MED |
| 셋업시간 매트릭스 | 미정의 | HIGH |
| 대시보드 위젯 드래그&드롭 | 미정의 | MED |

### 2.5 **전 경쟁사 공통 — v6.0에 없는 기능**

다음 기능은 **모든 주요 경쟁사가 기본 제공**하나 v6.0에 부재:

| 기능 | 설명 | 심각도 |
|---|---|:---:|
| **모바일/태블릿 UI** | 현장 작업자용 반응형 인터페이스 | **Critical** |
| **바코드/QR/RFID** | 자재/설비/LOT 자동 인식 | **Critical** |
| **전자 작업지시서 (e-WI)** | 단계별 멀티미디어 가이드 | **Critical** |
| **리포트 빌더** | 사용자 정의 리포트 | HIGH |
| **대시보드 빌더** | 커스텀 KPI 대시보드 | HIGH |
| **FPY (First Pass Yield)** | 일차 양품률 자동 계산 | HIGH |

---

## 3. MESA-11 잔여 갭 (v6.0 완전 구현 후 예상)

| # | MESA-11 기능 | v6.0 예상 점수 | 잔여 갭 |
|:---:|---|:---:|---|
| 1 | 자원 배분/상태 | 75% | 자원 예약/잠금 부재, 멀티사이트 자원 풀 |
| 2 | 상세 스케줄링 | 80% | 셋업시간 매트릭스, 인터랙티브 간트 |
| 3 | 작업 지시/디스패칭 | 65% | 자동 디스패칭, e-WI, 자재 역산 |
| 4 | 문서 관리 | 80% | ECN/ECO, 체크인/체크아웃 |
| 5 | 데이터 수집 | 70% | Edge Gateway, Data Historian, Modbus |
| 6 | 노동 관리 | 70% | T&A 단말 연동, 노무비 추적, 교육 관리 |
| 7 | 품질 관리 | 80% | MSA/Gage R&R, FMEA, 속성 관리도, NCR/MRB |
| 8 | 공정 관리 | 75% | ISA-88 절차 모델, 공정 인터록 |
| 9 | 유지보수 관리 | 75% | MTTF/MTTR/MTBF 자동계산, 교정 관리 |
| 10 | 제품 추적/계보 | 80% | 시리얼 번호, 바코드/RFID, As-Built |
| 11 | 성과 분석 | 75% | ISO 22400 전체 KPI, FPY, BI 도구 연동 |
| | **종합 평균** | **75%** | (v4.0 41.4% → v6.0 75%) |

---

## 4. 누락 요구사항 식별 결과

두 차례의 독립적 갭 분석을 통합하여 아래 요구사항을 도출하였다.

### 기능 요구사항 (REQ-052 ~ REQ-075)

#### Phase 1 확장 — Must-Have (3~6개월)

| ID | 모듈 | 기능명 | 상세설명 | 근거 | 우선순위 |
|:---:|---|---|---|---|:---:|
| REQ-052 | 시스템 | 바코드/QR/RFID 지원 | GS1-128/QR/DataMatrix 바코드 생성 및 인쇄, 스캐너 연동 API, RFID 미들웨어, LOT/시리얼/자재/설비 자동 인식, 작업 시작/완료/이동 스캔 기록 | GS1 표준, 전 경쟁사 기본 제공 | 상 |
| REQ-053 | 생산실행 | 전자 작업지시서(e-WI) | 공정 단계별 작업 가이드(Step-by-Step), 이미지/동영상/PDF/CAD 첨부 및 인라인 뷰어, 단계별 체크포인트 작업자 서명, SOP 자동 연결, 열람 이력 기록 | Siemens/Rockwell/SAP 핵심 기능, 21 CFR Part 11 | 상 |
| REQ-054 | 품질 | 부적합품 관리(NCR) | 부적합 발생 등록(자동/수동), 즉시 격리(Quarantine) 처리, MRB 심의 워크플로우(사용/재작업/폐기/특채 결정), 부적합 이력 통계, CAPA(REQ-036) 자동 연계 | ISO 9001:2015 8.7, Rockwell Plex 자동 격리 | 상 |
| REQ-055 | 품질 | SPC 자동격리조치 | SPC 위반 시: 해당 LOT 자동 보류, 설비 자동 정지, CAPA 자동 트리거, 품질 엔지니어 알림. 위반 유형별 조치 규칙 설정 가능 | Critical Manufacturing 핵심 차별화 | 상 |
| REQ-056 | 품질 | 제품출하판정 워크플로우 | 자재 상태 모델(AVAILABLE/HOLD/QUARANTINE/REJECTED), MRB(Material Review Board) 판정(사용/재작업/폐기/반품), 판정 이력 감사추적 | ISO 9001:2015 8.6/8.7, FDA 21 CFR Part 820 | 상 |
| REQ-057 | KPI | FPY 자동계산 | 공정단계별/품목별/라인별 FPY = (1차 양품수/투입수) 자동 계산, Rolled Throughput Yield(RTY) 전공정 산출, FPY 추이 분석 및 목표 관리 | ISO 22400, Six Sigma, 전 경쟁사 | 상 |
| REQ-058 | 설비 | 설비보전 KPI 자동계산 | equip_status_log + CMMS 데이터 기반: MTTF, MTTR, MTBF, PM 준수율(%), 시정보전/예방보전 비율 자동 계산 | ISO 22400, 전 경쟁사 CMMS 모듈 | 상 |

#### Phase 2 확장 — Should-Have (6~9개월)

| ID | 모듈 | 기능명 | 상세설명 | 근거 | 우선순위 |
|:---:|---|---|---|---|:---:|
| REQ-059 | 품질 | MSA/Gage R&R | Gage R&R 연구 관리(반복성/재현성), Type 1 연구, Bias/Linearity/Stability 분석, AIAG MSA 4th edition 준수 | IATF 16949 9.1.1.2, Siemens/Rockwell | 중 |
| REQ-060 | 품질 | SPC 속성관리도 | p-chart(불량률), np-chart(불량수), c-chart(결점수), u-chart(단위당결점수) 지원. REQ-035의 X-bar/R 확장 | ISO 7870-2, Siemens Opcenter Quality | 중 |
| REQ-061 | 품질 | FMEA 관리 | PFMEA 등록/관리: 고장모드, 영향, 원인, S/O/D 점수, RPN 자동계산, 권장조치, 이행추적. AIAG/VDA FMEA 핸드북 준수 | IATF 16949, Rockwell Plex, Siemens | 중 |
| REQ-062 | KPI | ISO 22400 KPI 라이브러리 | ISO 22400 핵심 KPI 구현: Throughput Rate, Production Lead Time, Cycle Time, Setup Time, Worker Efficiency, Inventory Turns, Scrap/Rework Ratio. 자동 계산 + 벤치마킹 | ISO 22400, Rockwell 2,600+ KPI | 중 |
| REQ-063 | 시스템 | 에너지 관리 | 설비별/라인별/제품별 에너지 소비량 모니터링, 에너지 KPI(kWh/unit) 자동계산, 에너지 비용 분석, 피크 수요 관리 알림 | ISO 50001, ISO 22400 환경 KPI, ESG | 중 |
| REQ-064 | 설비 | 교정 관리 | 측정기/계측기별 교정 주기 관리, 교정 실행 기록/성적서 관리, 교정 만료 시 해당 측정기 사용 자동 차단, 교정 이력↔검사 결과 연계 | ISO 9001 7.1.5, ISO/IEC 17025, GMP | 중 |
| REQ-065 | 품질 | 공급업체 품질 관리(SQM) | 공급업체별 품질 실적(입고 불량률, 납기 준수율) 자동 집계, 공급업체 평가 스코어카드, SCAR(공급업체 시정조치 요청) 워크플로우, ASL 관리 | ISO 9001 8.4, IATF 16949, SAP QM | 중 |
| REQ-066 | 생산실행 | 자동디스패칭/자재역산 | 스케줄링(REQ-050) 결과 → 작업지시 자동 생성, 작업지시 완료 시 BOM 기반 자재 소비 자동 역산(Backflush), 수동 자재 불출 제거 | ISA-95 Production Operations | 중 |
| REQ-067 | 생산계획 | 셋업시간 매트릭스 | 제품간 전환(Changeover) 셋업시간 매트릭스 관리, 순서 의존 셋업시간 모델링(REQ-050 스케줄링 연동), 계획 vs 실제 셋업시간 추적 | ISA-95, Siemens APS, MPDV HYDRA | 중 |
| REQ-068 | 생산실행 | WO 원가추적 | 작업지시별 실제 원가 집계: 노무비(시간×단가), 자재비(실소비×단가), 경비 배부. 표준원가 vs 실제원가 차이 분석 | ISA-95 Performance, SAP DMC | 중 |
| REQ-069 | 통계 | 커스텀 대시보드 빌더 | 사용자별 대시보드 위젯 드래그&드롭 구성, KPI 게이지/차트/테이블 위젯 라이브러리, 역할별 기본 프리셋(경영진/관리자/작업자), 대시보드 공유/내보내기 | Rockwell/SAP/Siemens/Critical Mfg | 중 |
| REQ-070 | 통계 | 리포트 빌더 | 사용자 정의 리포트 템플릿, 드래그&드롭 필드 배치, 그룹/집계/필터/정렬, PDF/Excel/CSV Export, 정기 자동 생성 및 이메일 발송 | Rockwell/SAP 커스텀 리포트 | 중 |

#### Phase 3 확장 — Nice-to-Have (9~12개월)

| ID | 모듈 | 기능명 | 상세설명 | 근거 | 우선순위 |
|:---:|---|---|---|---|:---:|
| REQ-071 | 공정 | 배치실행엔진 | ISA-88 Batch State Machine 구현, Procedure→Unit Procedure→Operation→Phase 실행 계층, 배치 예외 처리(Hold/Resume/Abort) | ISA-88, 프로세스 산업 필수 | 하 |
| REQ-072 | 공정 | 전자배치기록(eBR) | 배치 실행 중 모든 활동(파라미터/자재/작업자/시간) 자동 기록 → eBR 생성, 배치 기록 검토/승인 워크플로우, PDF 출력 | FDA 21 CFR Part 11, ISA-88 | 하 |
| REQ-073 | 시스템 | 설계변경관리(ECM) | ECR→ECN→ECO 워크플로우, BOM/라우팅/레시피 변경 영향분석(Impact Analysis), 변경이력 추적, 유효일자(Effectivity Date) 관리 | IATF 16949, Siemens CMII | 하 |
| REQ-074 | 생산실행 | 복합라우팅 | 재진입 라우팅(동일 설비 다회 방문), 조건 분기(IF 검사PASS THEN 다음 ELSE 재작업), 병렬 라우팅(분기/합류), 재작업 루프 | Critical Manufacturing, ISA-88 | 하 |
| REQ-075 | 시스템 | 멀티사이트 관리 | Enterprise→Site→Area→Line 계층 모델(ISA-95/ISA-88), 사이트별 독립 운영 + 본사 통합 가시성, 크로스사이트 재고/자원 공유, 글로벌 KPI 통합 | ISA-95, Siemens/DELMIA | 하 |

### 비기능 요구사항 (NFR-011 ~ NFR-020)

#### Phase 1 확장

| ID | 영역 | 항목 | 상세설명 | 근거 | 우선순위 |
|:---:|---|---|---|---|:---:|
| NFR-011 | UI/UX | 모바일/태블릿 반응형 UI | 현장 작업자용 PWA 또는 반응형 인터페이스, 작업지시/실적입력/품질검사/설비상태 터치 최적화, 오프라인 캐싱 | 전 경쟁사 기본 제공 | 상 |
| NFR-012 | 보안 | 데이터 암호화 | TLS 1.3 전 통신 필수, AES-256 민감 데이터 저장 암호화, DB 연결 SSL | IEC 62443 FR4, FDA 21 CFR Part 11 | 상 |
| NFR-013 | 보안 | 보안 이벤트 로깅 | 인증 실패/권한 위반/의심 패턴 중앙 로깅, 5회 실패 → 15분 잠금, 세션 타임아웃(30분), 로그 보존 ≥1년 | IEC 62443 FR6, ISO 27001 | 상 |
| NFR-014 | 준수 | 감사추적 불변성 보장 | REQ-049 감사추적 레코드 append-only(UPDATE/DELETE 불가), Hash chain 또는 암호화 연결, 보존 기간 정책(품질 3년, 제약 7년) | FDA 21 CFR Part 11.10(c), EU GMP Annex 11 | 상 |

#### Phase 2 확장

| ID | 영역 | 항목 | 상세설명 | 근거 | 우선순위 |
|:---:|---|---|---|---|:---:|
| NFR-015 | 보안 | 네트워크 구역 세그멘테이션 | IEC 62443 Zone/Conduit 모델: IT Zone(Frontend, API), OT Zone(MQTT, OPC-UA), DMZ(Reverse Proxy), DB Zone. Kubernetes NetworkPolicy(Cilium) 적용 | IEC 62443, ISA-95 Level 분리 | 중 |
| NFR-016 | 성능 | 고주파 데이터 수집 | MQTT/OPC-UA 소스에서 ≥10,000 data points/sec 지원, 시계열 데이터 보존/다운샘플링, 메시지 큐 버퍼링(Redis Streams/Kafka) | ISA-95 Level 2-3, Siemens | 중 |
| NFR-017 | 준수 | 전자서명 상세규격 | FDA 21 CFR Part 11 준수: 최소 2개 식별요소(ID+PW), 서명 표시(서명자명+일시+의미), 서명-기록 암호화 연결, 서명 재사용/양도 불가 | FDA 21 CFR Part 11.50/11.70/11.200 | 중 |
| NFR-018 | 아키텍처 | API 버전관리 | REST API 버전관리(/api/v1/, /api/v2/), 사용 중단 정책(최소 6개월 사전 고지), OpenAPI 3.0 자동 생성 | 엔터프라이즈 MES 표준 관행 | 중 |

#### Phase 3 확장

| ID | 영역 | 항목 | 상세설명 | 근거 | 우선순위 |
|:---:|---|---|---|---|:---:|
| NFR-019 | 안정성 | 오프라인/장애 대응 모드 | MQTT 브로커 다운(로컬 큐), ERP 미접속(트랜잭션 버퍼), Redis 다운(DB 폴백), 프론트엔드 오프라인 모드 | Rockwell Plex Elastic MES, IEC 62443 FR7 | 하 |
| NFR-020 | 준수 | 시스템 밸리데이션(IQ/OQ/PQ) | GAMP 5 기반 IQ/OQ/PQ 프로토콜 지원, 밸리데이션 실행 기록 및 문서 자동 생성, 요구사항-설계-코드-테스트 Traceability Matrix 자동 생성 | FDA 21 CFR Part 11, GAMP 5, EU Annex 11 | 하 |

---

## 5. 종합 평가 요약

### 표준 준수 달성률

| 표준 | v4.0 | v6.0 (현재) | 갭 요구사항 반영 후 |
|---|:---:|:---:|:---:|
| ISA-95 (IEC 62264) | 40% | 65% | **85%** |
| ISA-88 (IEC 61512) | 10% | 25% | **50%** |
| FDA 21 CFR Part 11 | 10% | 40% | **80%** |
| IEC 62443 | 5% | 15% | **55%** |
| ISO 22400 | 12% | 15% | **60%** |
| ISO 9001/IATF 16949 | 40% | 55% | **80%** |

### 경쟁사 기능 동등성

| 경쟁사 | v4.0 | v6.0 (현재) | 갭 반영 후 |
|---|:---:|:---:|:---:|
| Siemens Opcenter | 25% | 45% | **70%** |
| Rockwell Plex | 25% | 45% | **75%** |
| SAP DMC | 20% | 40% | **65%** |
| Critical Manufacturing | 30% | 50% | **70%** |
| MPDV HYDRA | 30% | 50% | **80%** |

### 핵심 발견사항 TOP 5

1. **모바일/바코드/e-WI 전무** — 전 경쟁사가 기본 제공하는 현장 작업자 인터페이스(모바일, 바코드, 전자작업지시)가 미정의. 현장 활용도에 직접적 영향.

2. **KPI 체계의 극단적 격차** — ISO 22400 34개 KPI 중 4개만 커버. MTTF/MTTR/MTBF, FPY, Lead Time, Cycle Time 등 핵심 KPI 대거 누락.

3. **데이터 수집 계층 부재** — OPC-UA/MQTT가 Phase 2~3에 배정되어 Edge Gateway, Data Historian, Store-and-Forward 등 데이터 인프라가 근본적으로 부재.

4. **IEC 62443 보안 최저 수준** — IT 보안 기본(JWT, RBAC)은 있으나 OT 환경 보안(Zone/Conduit, 네트워크 세그멘테이션, 데이터 암호화)이 전무.

5. **ISA-88 배치 제어 구조적 부재** — 레시피 관리(REQ-041)만으로는 배치 실행 엔진, 절차 계층, 배치 상태 머신 구현 불가. 프로세스 산업 대응에 근본적 제약.

---

## 추가 요구사항 요약

| 구분 | 추가 건수 | ID 범위 |
|---|:---:|---|
| 기능 요구사항 (Phase 1) | 7건 | REQ-052~058 |
| 기능 요구사항 (Phase 2) | 12건 | REQ-059~070 |
| 기능 요구사항 (Phase 3) | 5건 | REQ-071~075 |
| 비기능 요구사항 (Phase 1) | 4건 | NFR-011~014 |
| 비기능 요구사항 (Phase 2) | 4건 | NFR-015~018 |
| 비기능 요구사항 (Phase 3) | 2건 | NFR-019~020 |
| **합계** | **34건** | |

v6.0 최종 요구사항: REQ-001~075(75건) + NFR-001~020(20건) = **총 95건**

---

*최종 업데이트: 2026-03-03*
*분석 도구: 소스코드 전수 분석 + ISA-95/88/IEC 62443/ISO 22400 표준 대조 + 경쟁사 기능 벤치마크*
