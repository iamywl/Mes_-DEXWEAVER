# Dassault DELMIA / Honeywell MXP / GE Proficy 세부 기능 심층 비교

> 조사일: 2026년 3월 | 기반 데이터: 2024~2026년 최신 자료

---

## 1. 생산 스케줄링 / APS

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| APS 내장 여부 | **Ortems 별도 제품 (강력)** | 미내장 (ERP 의존) | Scheduler 별도 제품 |
| AI 최적화 | Ortems 내 AI 의사결정 지원 | 스케줄링에는 미적용 | CSense에서 AI/ML 분석 |
| What-if 시뮬레이션 | **수초 내 재최적화** | 미지원 | Gantt 기반 시나리오 |
| 강점 산업 | 이산/반복 제조 | 배치/연속 공정 | 공정/이산/혼합 제조 |

### 상세 분석

**DELMIA Apriso + Ortems**
- Apriso 자체는 MES 실행 계층, APS는 별도 제품인 **DELMIA Ortems**가 담당
- Ortems는 자재와 용량을 동시 고려하는 유한용량(Finite Capacity) 엔진 내장
- 기계, 공구, 작업자 등 **다중 자원 제약** 동시 처리
- "AI-driven decision support" 표방 → 자원 활용 극대화, 전환(changeover) 시간 최소화
- IIoT/MOM 신호 + 시뮬레이션으로 조건 변화 시 **수초 내 재최적화** 가능
- 긴급 주문/설비 고장 등 돌발 상황의 영향을 "What-if" 시뮬레이션으로 즉시 파악

**Honeywell MXP**
- MXP 자체에 독립적 APS 모듈 **미내장** → SAP 등 외부 ERP의 APS에 의존
- 배치 오케스트레이션 및 실행에 초점
- 배치 진행 상황의 실시간 시각화(process unit timeline, 장비 상태, 파라미터 트렌드)
- 편차 발생 시 신속 대응 가능하나 **자동 리스케줄링 엔진은 아님**
- 생명과학 배치 제조의 장비 가용성, 청소 주기, 규정 준수 등 배치 특화 제약 조건 관리

**GE Vernova Proficy + Scheduler**
- **Proficy Scheduler**(구 ROB-EX 인수)가 유한용량 스케줄링 담당
- 장비/공구/자원 가용성을 자동 고려, 인터랙티브 Gantt 차트 제공
- 스케줄링 자체보다는 **Proficy CSense**에서 AI/ML을 강력 적용
- CSense: 공정 디지털 트윈 구축, 분석-모니터링-예측-시뮬레이션-최적화 5개 기능 통합
- ERP/MES와 통합하여 수요 변화나 돌발 상황에 빠르게 스케줄 조정

---

## 2. 작업지시 관리

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 3D 작업지시 | **네이티브 지원 (3DEXPERIENCE)** | 미지원 | 미지원 |
| AR 지원 | **DELMIA Augmented Experience** | 미지원 | 미지원 |
| 지시서 강제 방식 | Step-by-step + 3D 오버레이 | ISA-88 배치 오케스트레이션 | 인터랙티브 Workflow |
| 주요 인터페이스 | 통합 UI + iOS 모바일 앱 | 역할별 대시보드 | Operations Hub (웹) |

### 상세 분석

**DELMIA Apriso**
- 텍스트, 이미지, 동영상 + **3D 작업지시서** 네이티브 지원 (3DEXPERIENCE 연동)
- **DELMIA Augmented Experience**: AR 기반 조립 가이드, 컴퓨터 비전, 딥러닝 자동 품질 검사
- 실제 부품 위에 3D 데이터 오버레이 → 조립 정확도 보장
- Step-by-step directed execution: 인라인 체크리스트, 안전 지침, 문서 통합
- 생산/보전/창고 업무를 하나의 통합 인터페이스에서 처리, iOS 모바일 앱 지원

**Honeywell MXP**
- 디지털 작업지시서 + 전자 로그북 지원
- 종이 기반 배치 기록서/작업 지시서/로그북을 디지털로 대체하는 데 초점
- ISA-88 기반 배치 절차: 레시피 단계 자동 오케스트레이션, 전자서명으로 각 단계 확인
- SOP 준수를 시스템적으로 강제
- 프로그래밍 지식 없이 구성 가능한 다중 역할별 인터페이스

**GE Vernova Proficy**
- **Proficy Workflow**: 동적이고 인터랙티브한 전자 작업지시서(eSOPs) 제공
- 종이 기반 절차를 전자 형식으로 전환
- Step-by-step 인터랙티브 가이드, 2025년 Activities operator "to-do" list 위젯 추가
- **Proficy Operations Hub**: 웹 기반 "Single Pane of Glass" 역할별 시각화

---

## 3. 품질 관리

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| SPC 내장 | **완전 내장** | TrackWise 연동 | **완전 내장** |
| 3D 결함 추적 | **3D VQDT (독보적)** | 미지원 | 미지원 |
| CAPA 엔진 | 내장 (8D/CAPA) | **TrackWise QMS (업계 최고)** | 기본 NCM |
| AI 품질 분석 | AI 의사결정 지원 | **TrackWise AI (NLP/ML)** | CSense AI/ML |

### 상세 분석

**DELMIA Apriso**
- SPC 모듈 내장: 관리도(Control Charts), 공정능력 분석, 샘플링 계획
- 생산 공정에 통합된 인라인 품질 검사 태스크 자동 할당
- Issue Management 모듈: 8D, CAPA 등 공식 이슈 관리 프로세스
- **3D Visual Quality Defect Tracking (3D VQDT)**: 3D 모델 위에 결함을 시각적 매핑 → 업계 독보적

**Honeywell MXP**
- 품질 관리는 **TrackWise Digital QMS** 통합으로 구현
- QMS에서 불만/편차/부적합/CAPA/변경관리/감사 처리
- TrackWise Digital: 업계 선도적인 CAPA 워크플로
- **TrackWise AI**: 생성형 AI, NLP, ML로 신호 탐지 개선, 품질 이벤트 간 패턴 자동 식별 → 3사 중 가장 진보된 AI 품질 분석

**GE Vernova Proficy**
- Quality Management 모듈에 SPC 내장: 실시간 트렌드, 통계, 알림
- 2025년: NCM 확장 + 다운그레이드 자재 정의 기능 추가
- **Proficy CSense**: AI/ML로 품질 변동 원인을 데이터 기반 분석
- Skjern Paper 사례: 6시간 컨설팅으로 품질 거부 원인 파악

---

## 4. 추적성/이력 관리

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 추적 단위 | 개별/로트/배치 모두 | **배치/로트 특화** | 직렬/비직렬 모두 |
| 글로벌 계보 | **중앙 글로벌 저장소** | Batch Historian 통합 | 공장 단위 계보 |
| RFID 네이티브 | **전용 모듈 보유** | 칭량배분 앱에서 지원 | 기본 지원 |
| 2025 신규 | - | - | 공구 추적성 추가 |

### 상세 분석

**DELMIA Apriso**
- 개별(Individual), 로트(Lot), 배치(Batch) 모두 지원
- 원자재~완제품 전체 제품 계보(Genealogy)를 **중앙 글로벌 저장소**에서 관리
- 사람/장비/공정/자재 포함 완전한 양방향 추적
- RFID 및 바코드 스캐너 네이티브 지원, IIoT/린 제조/JIT 연계

**Honeywell MXP**
- **배치 단위** 추적 특화 (생명과학 배치 공정)
- MXP + Experion Batch + Batch Historian 조합으로 완전한 추적성
- 자동 이벤트 로깅으로 중요 세부사항 누락 방지
- 칭량/배분(Weigh & Dispense) 앱에서 바코드/RFID 활용

**GE Vernova Proficy**
- 비직렬화 및 직렬화 생산 운영 모두 관리
- 제품 계보 보고서 생성, 양방향 추적
- 2025년: **공구 추적성(Tool Traceability)** 추가

---

## 5. 설비/자산 관리

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| OEE 지표 수 | **70+ 지표 (MIP)** | 기본 OEE 앱 | OEE+MTBF/MTTR 등 |
| 예지보전 | 기본 보전 모듈 | 미내장 | **SmartSignal (업계 최강)** |
| 오프라인 보전 | **서버 비연결 시 보전 가능** | 미확인 | 미확인 |
| 2025 신규 | - | - | Downtime 위젯 |

### 상세 분석

**DELMIA Apriso**
- **Machine Intelligence Pack**: OEE, 사이클타임, 양품/스크랩/불량 등 **70개 이상 장비 기반 지표** 자동 계산
- Apriso Maintenance 모듈: 생산/품질/창고 모듈과 긴밀 연동
- **오프라인 보전**: 서버 비연결 상태에서도 보전 오더 동기화/실행 가능 (독보적)
- Machine Integrator를 통한 실시간 설비 데이터 수집

**Honeywell MXP**
- OEE 앱/장비 보전 앱 모듈형 제공
- Experion DCS 통합으로 장비 상태 모니터링
- 배치 공정 장비 가용성/청소 주기 관리
- 예지보전 전용 모듈은 MXP 내 미확인

**GE Vernova Proficy**
- **Efficiency Management 모듈 + Cloud OEE**: OEE, MTBF, MTTR 등 핵심 KPI 추적
- **SmartSignal**: 실제 고장 시점 예측 → 유지보수 우선순위/일정 최적화 → 업계 최강 예지보전
- 2025년: Operations Hub Downtime 위젯 추가

---

## 6. 데이터 수집

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 주요 프로토콜 | OPC DA/UA, RS-232 | Modbus, DNP3, IEC, OPC | **OPC UA/DA, MQTT, 수백 개** |
| 수집 속도 | 실시간 (명시 미공개) | 실시간 (배치 중심) | **150K vals/sec, 10억/분** |
| MQTT 지원 | 미확인 | Experion 통해 가능 | **네이티브 지원** |
| 엣지 특성 | 장비 비의존적 | Experion 생태계 의존 | 클라우드/온프레미스 유연 |

### 상세 분석

**DELMIA Apriso**
- **Machine Integrator**: OPC DA/UA, RS-232 지원, OPC 서버 이중화(Failover)
- 장비 비의존적(Equipment Agnostic) 아키텍처
- 분산 구성 관리, 고신뢰성, 고가용성 메커니즘 내장
- OPC UA 보안 인증서 관리 지원

**Honeywell MXP**
- **Experion HS SCADA**: Modbus TCP/IP, DNP3, IEC 61850/60870, OPC DA/HDA/A&E
- ControlEdge PLC + OPC UA 인터페이스로 **90% 구성 시간 단축**
- Batch Historian 통합: 실시간 + 이력 데이터 관리
- 배치 공정 크리티컬 파라미터 실시간 트렌드 모니터링

**GE Vernova Proficy**
- **Proficy Historian**: OPC UA, OPC DA, MQTT + **수백 개 프로토콜** 데이터 컬렉터
- 프로토콜 컨버터로 어떤 산업 프로토콜이든 OPC UA로 변환
- 인터페이스당 최대 **150,000 values/second** 수집
- AWS 기반 **분당 10억 샘플** 수집률 달성

---

## 7. 리포팅/분석

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 자체 분석 엔진 | 데이터 웨어하우스 내장 | Batch Historian | **CSense (강력)** |
| AI/ML 분석 | 기본 수준 | TrackWise AI (QMS 중심) | **CSense (공정 최적화 특화)** |
| 모바일 대시보드 | Executive Intelligence Center | 웹 기반 | Operations Hub (웹) |
| GraphQL API | 미지원 | 미지원 | **2025년 신규 지원** |

### 상세 분석

**DELMIA Apriso**
- **Dashboard Builder**: 드래그앤드롭 인터랙티브 실시간 대시보드
- **Executive Intelligence Center**: 스마트폰/태블릿에서 경영진용 데이터
- EMI/BI 도구 없이도 실시간 분석 가능
- Analytics & Reporting 모듈(데이터 웨어하우스) 내장

**Honeywell MXP**
- 다중 역할별 실시간 대시보드, 배치 비교 분석 시각화
- Batch Historian이 시계열 데이터 관리
- **TrackWise AI**: QMS 영역에서 생성형 AI/NLP/ML → 신호 탐지 + 운영 효율성 개선
- Golden Batch 대비 편차 트렌드 분석

**GE Vernova Proficy**
- **Operations Hub**: 역할 기반 웹 시각화, 2025년 Downtime/Activities 위젯 추가
- 2025년 **GraphQL 커넥터** 추가 → Plant Apps 데이터 쉬운 접근
- **Proficy CSense**: AI/ML/최적화 알고리즘 통합 산업 분석 플랫폼
- 오프라인/실시간, 엣지/클라우드 유연 배포, 공정 디지털 트윈
- 주요 지표 **최대 10% 개선** 달성 사례

---

## 8. 재고/자재 관리

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 내장 WMS | **완전 내장 (45+ 지표)** | 미내장 (별도 Momentum) | 미내장 |
| 칭량/배분 | 기본 지원 | **Weigh & Dispense 전문** | 기본 지원 |
| 재고 통합 수준 | 생산+품질+창고 통합 DB | 배치 중심 자재 추적 | ERP 연동 중심 |

### 상세 분석

**DELMIA Apriso**
- 생산/품질/창고 모듈 통합 데이터베이스로 WIP 실시간 추적
- ERP 통합 Backflush 처리, 재고 업데이트 직접 리포팅
- **DELMIA Apriso Warehouse**: WMS 완전 내장
- **Warehouse Intelligence Pack**: 재고 정확도/창고 활용률/응답시간 등 **45개 이상 지표** 자동 리포팅

**Honeywell MXP**
- 배치 실행 중 자동 이벤트 로깅으로 배치 단위 WIP 추적
- **Weigh & Dispense** 앱: 생명과학 분야 칭량/배분 업무 전문 처리
- WMS 자체 내장 없음 (Honeywell Intelligrated Momentum WMS는 별도 제품)

**GE Vernova Proficy**
- 주문 우선순위/즉시 상태 조회/요약/이력 관리
- 자재 소비 추적 + ERP 연동 Backflush
- JIT 납품/폐기물 최소화에 초점, 별도 WMS 없음

---

## 9. 레시피/BOM 관리

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| PLM 연동 | **3DEXPERIENCE 네이티브 (최강)** | ERP 중심 | Orchestration Hub |
| 레시피 표준 | BOM/Route 기반 | ISA-88 (배치 특화) | ISA-88 + BOM |
| 설계-제조 연속성 | **폐쇄루프 동기화** | 미지원 | ERP/PLM 데이터 통합 |

### 상세 분석

**DELMIA Apriso**
- 경로(Route)/작업(Operations)/문서/BOM/속성 통합 관리
- 3DEXPERIENCE PLM(ENOVIA)과 **폐쇄루프 동기화(Closed-loop Synchronization)**
- PLM 변경 BOM/레시피가 MES로 자동 전파 → **독보적 PLM 연동**

**Honeywell MXP**
- ISA-88 표준 기반 클래스 기반 레시피: 마스터 레시피 → 제어 레시피 계층 관리
- 중앙 레시피 저장소, 승인/작업 워크플로, 변경 이력 관리
- FDA/EudraLex (21 CFR Part 11, GMP Annex 11) 준수

**GE Vernova Proficy**
- **Proficy Orchestration Hub**: ERP/PLM 등 이질적 시스템 데이터를 통합하여 생산 준비 형식으로 변환
- ISA-88 표준 지원, 중앙 레시피 저장소, 클래스 기반 레시피
- 단일/다중 사이트 공장 현장 시스템에 오케스트레이션

---

## 10. 규정 준수

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 규제 준수 깊이 | 완전 준수 | **생명과학 최적화 (최강)** | 기본 준수 |
| Review-by-exception | 미확인 | **지원 (배치 릴리스 가속)** | 미확인 |
| EBR 성숙도 | 높음 | **매우 높음 (전문)** | 중간 (Workflow 기반) |
| EU Annex 11 | 지원 | **명시적 지원** | 제한적 확인 |

### 상세 분석

**DELMIA Apriso**
- 21 CFR Part 11 / EU Annex 11 완전 준수
- 내장 전자서명, 디지털 감사추적(Audit Trail), 추적 보고서 자동 생성
- 생산 실행 과정에서 EBR 자동 생성

**Honeywell MXP**
- **생명과학 규정 준수에 가장 특화된 플랫폼**
- FDA 21 CFR Part 11, EU Annex 11(GMP), EudraLex 포괄적 준수
- **Review-by-exception**: 전자서명 결합으로 배치 검증/릴리스 대폭 가속화 → 독보적 강점
- 모든 변경/활동/트랜잭션에 대한 상세 감사추적 자동 유지

**GE Vernova Proficy**
- 21 CFR Part 11 지원 (Quality Management 모듈)
- Proficy Plant Applications e-Signature, Workflow 단계별 전자서명
- Proficy Workflow로 전자 마스터 배치 기록 생성

---

## 11. 시스템 아키텍처

### 핵심 차이점

| 항목 | DELMIA Apriso | Honeywell MXP | GE Proficy |
|------|-------------|---------------|------------|
| 아키텍처 | SOA 기반 | **모듈형 (MES+SCADA+Historian)** | **마이크로서비스 (K8s)** |
| API 현대성 | REST/Web API | 통합 API | **GraphQL + REST** |
| 글로벌 배포 | **Global Process Manager (최강)** | 모듈형 멀티사이트 | 분산 네트워크 지원 |
| 클라우드 네이티브 | 3DEXPERIENCE Cloud | 온프레미스 중심 | **AWS/Azure SaaS (최강)** |
| 노코드 수준 | Process Builder (중간) | 노코드 구성 | **80/20 노코드 (최강)** |

### 상세 분석

**DELMIA Apriso**
- **SOA(Service Oriented Architecture)** 기반, 3DEXPERIENCE 클라우드 연동
- Web API(REST): API Key/Access Token 두 가지 인증
- **Process Builder**: 시각적 프로세스 모델링 (SQL, HTML/JS/CSS, C#)
- **Global Process Manager**: 글로벌 다중 사이트 배포 관리 → **3사 중 가장 성숙한 글로벌 배포 역량**
- **오프라인 운영**: 서버 비연결 시 보전 오더 실행 → 이후 동기화

**Honeywell MXP**
- **모듈형 플랫폼**: MES + SCADA + Historian 단일 플랫폼 통합 → **유일한 제품**
- SAP/TrackWise/Experion DCS/3rd party 통합 API
- **프로그래밍 지식 없이 구성 가능**한 노코드 환경
- 로컬/글로벌 생산 환경 모두 적응하는 모듈형 아키텍처
- 오프라인 운영: 명시적 확인 안됨

**GE Vernova Proficy**
- **컨테이너화된 마이크로서비스 (Kubernetes)** → 3사 중 가장 현대적
- 2025년 **GraphQL 커넥터** 추가, REST API 지원
- **80% OOB + 20% 노코드 구성**: 전문 코딩 없이 워크플로/엣지 앱 관리
- 클라우드: AWS/Azure 기반 SaaS, 하이브리드 지원
- **Zero Downtime 업데이트**, High Availability

---

## 종합 비교 요약

| 평가 항목 | DELMIA Apriso 강점 | Honeywell MXP 강점 | GE Proficy 강점 |
|-----------|-------------------|-------------------|----------------|
| **산업 적합** | 이산/반복 제조 (자동차, 항공) | 생명과학 배치 (제약, 바이오) | 공정/이산/혼합 (F&B, CPG) |
| **차별 기능** | 3D 작업지시, AR, Virtual Twin, PLM 연동 | MES+SCADA+Historian 통합, TrackWise AI | CSense AI/ML, SmartSignal 예지보전 |
| **스케줄링** | Ortems APS (강력) | 외부 의존 | Scheduler (기본~중간) |
| **품질** | 3D VQDT + 내장 SPC | TrackWise QMS (업계 최고 CAPA) | SPC 내장 + CSense 분석 |
| **규정 준수** | 완전 준수 | **생명과학 최적화 (최강)** | 기본 준수 |
| **글로벌 배포** | **Global Process Manager (최강)** | 모듈형 멀티사이트 | 분산 네트워크 |
| **아키텍처** | SOA (중간) | 모듈형 (중간) | **마이크로서비스/K8s (최강)** |
| **데이터 수집** | 실시간 (중간) | 실시간 (배치 중심) | **10억 샘플/분 (최강)** |
| **Gartner 평점** | 4.2/5 | 3.9/5 | 4.5/5 |

---

## 참고 자료

- [DELMIA Apriso](https://www.3ds.com/products/delmia/apriso)
- [DELMIA Ortems APS](https://www.3ds.com/products/delmia/ortems)
- [DELMIA Augmented Experience](https://www.3ds.com/products/delmia/augmented-experience)
- [Honeywell MXP](https://process.honeywell.com/us/en/initiative/manufacturing-excellence-platform)
- [TrackWise Digital QMS](https://www.spartasystems.com/trackwise/)
- [TrackWise AI](https://www.spartasystems.com/qualitywise-ai/)
- [GE Vernova Proficy MES](https://www.gevernova.com/software/products/manufacturing-execution-systems)
- [Proficy CSense](https://www.gevernova.com/software/products/proficy/csense)
- [SmartSignal](https://www.gevernova.com/software/products/asset-performance-management/equipment-downtime-predictive-analytics)
- [Gartner Peer Insights MES](https://www.gartner.com/reviews/market/manufacturing-execution-systems)
