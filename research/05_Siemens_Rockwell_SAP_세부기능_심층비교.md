# MES 3대 솔루션 세부 기능 심층 비교 분석

> 조사일: 2026년 3월 | 대상: Siemens Opcenter, Rockwell Plex MES, SAP Digital Manufacturing
> 기반 데이터: 2024~2026년 공식 문서, Gartner/IDC 분석, 사용자 리뷰

---

## 조사 개요

본 문서는 글로벌 MES 시장을 이끄는 3대 솔루션인 **Siemens Opcenter**, **Rockwell Automation Plex MES**, **SAP Digital Manufacturing(DMC)**를 11개 기능 영역에서 세부 기능 단위까지 심층 비교한다. 단순 개요가 아닌 각 기능의 작동 방식과 경쟁사 대비 차별점을 구체적으로 밝히는 것을 목적으로 한다.

---

## 1. 생산 스케줄링 / APS (Advanced Planning & Scheduling)

### 1.1 Siemens Opcenter APS (구 Preactor)

| 항목 | 상세 내용 |
|------|----------|
| **유한 용량 스케줄링** | Opcenter APS Advanced Scheduling으로 완전한 유한 용량 스케줄링 지원. 무한/유한 용량 모드 전환 가능하며, 계획 시간 단위를 일/주/월 또는 혼합 조합으로 설정 가능 |
| **AI/ML 기반 최적화** | 유전 알고리즘(Genetic Algorithm), 몬테카를로 트리 탐색(MCTS), 자율 스케줄링 등 AI 기반 알고리즘 적극 투자. 메타휴리스틱 최적화 엔진으로 OTIF(납기 준수율), 흐름 시간, WIP, 셋업 시간 등 다중 목표 동시 최적화 |
| **실시간 리스케줄링** | 예상치 못한 생산 변경에 대한 빠르고 쉬운 대응 가능. What-if 시나리오 비교를 통해 의사 결정 지원 (초과 근무, 주문 우선순위, 배치 분할, 납기 협상 등) |
| **다중 제약 조건** | 스킬/크루, 시퀀스 의존 전환(Changeover), 클린룸 정책, 병렬/대체 라우팅, 재진입(Reentrant) 흐름, 웨이퍼/로트 규칙 등 반도체 수준의 고급 제약 모델링 |
| **ERP 연계** | SAP, Oracle 등 주요 ERP와 양방향 동기화. Teamcenter PLM과의 네이티브 연계로 설계-계획-실행 일관성 확보 |

**핵심 차별점**: 업계에서 가장 정교한 제약 조건 모델링 능력. 반도체/항공우주 같은 초복잡 공정에서도 유한 용량 스케줄링이 가능한 유일한 수준의 APS. IDC MarketScape에서 APS 분야 Leader로 선정.

---

### 1.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **유한 용량 스케줄링** | Plex Finite Scheduler를 통해 유한 용량 스케줄링 지원. 사용자 정의 규칙, 유한 용량, 가용 자원(직원 스킬, 공구, 공간) 기반 스케줄링 |
| **AI/ML 기반 최적화** | 고급 알고리즘 기반 추천 엔진 제공하나, Siemens 수준의 AI/메타휴리스틱 최적화에는 미치지 못함. 스케줄링 엔진의 추천을 기반으로 사용자가 판단 |
| **실시간 리스케줄링** | "오프라인" What-if 시나리오 탐색 가능. 계획 엔진의 추천을 검토하고 정제하는 방식. 실시간 생산 정보와 연계되어 스케줄링 정확도 향상 |
| **다중 제약 조건** | 속성 기반 작업 순서 최적화로 생산 라인 부하 분산. 대체 작업 센터 간 레벨 로딩(Level-Loading) 지원. 재사용 가능한 작업 템플릿(라우팅, 자재, 원료 포함) |
| **ERP 연계** | Plex 자체 ERP와 네이티브 통합(단일 데이터 소스). API를 통한 외부 ERP 연동 가능하나, Plex ERP 사용 시 최적 |

**핵심 차별점**: ERP-MES 간 단일 데이터 소스로 계획-실행 간 데이터 불일치 제거. 클라우드 기반 실시간 스케줄링으로 별도 인프라 없이 즉시 사용 가능. 다만 Siemens 수준의 초복잡 제약 모델링은 부족.

---

### 1.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **유한 용량 스케줄링** | SAP DM 자체에는 고급 APS가 내장되지 않음. **SAP S/4HANA PP/DS(Production Planning & Detailed Scheduling)**와 연계하여 유한 용량 스케줄링 구현. 이산/프로세스 제조 모두 지원 |
| **AI/ML 기반 최적화** | SAP S/4HANA PP/DS의 고급 알고리즘과 ML 기능 활용. SAP IBP(Integrated Business Planning)와 결합 시 수요, 자재, 설비, 인력 제약을 종합 고려한 최적화 가능 |
| **실시간 리스케줄링** | SAP DM 현장 실시간 데이터 기반으로 생산 일정 자동 조정. 기계 가용성, 노동 자원, 실시간 공장 성과에 따른 운영 스케줄링 |
| **다중 제약 조건** | PP/DS에서 용량 및 자재 가용성 제약을 동시 고려. IBP에서 중장기 전략/S&OP 계획, PP/DS에서 단기 상세 스케줄링의 계층적 접근 |
| **ERP 연계** | S/4HANA와의 네이티브 통합이 최대 강점. ERP-MES 간 별도 미들웨어 없이 실시간 데이터 교환. PP/DS가 S/4HANA에 내장되어 계획-실행 원활 동기화 |

**핵심 차별점**: APS가 MES 내장이 아닌 S/4HANA PP/DS에 의존하는 구조. SAP 생태계 내에서는 ERP-APS-MES 간 가장 긴밀한 통합을 제공하나, SAP 외부 ERP 사용 시 이점이 크게 감소. IBP+PP/DS 조합으로 전략-운영 계획의 수직 통합이 가능한 것이 고유한 강점.

---

### 1.4 스케줄링/APS 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| APS 내장 여부 | 독립 모듈(Opcenter APS) | 내장(Finite Scheduler) | 외부 의존(S/4HANA PP/DS) |
| 제약 모델링 깊이 | ★★★★★ (반도체급) | ★★★☆☆ (일반 제조) | ★★★★☆ (PP/DS 활용 시) |
| AI/ML 최적화 | 유전 알고리즘, MCTS | 기본 알고리즘 | ML 기반(IBP 연계 시) |
| 독립 사용 가능 | 가능 (어떤 ERP와도 연동) | Plex ERP 사용 시 최적 | SAP ERP 필수 |

---

## 2. 작업지시 관리 (Work Order Management)

### 2.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **전자 작업지시서(e-WI)** | 텍스트, 이미지, 동영상, **3D 데이터**, **증강현실(AR)** 모두 지원. 2D/3D 작업 지시 저작 및 뷰잉 애플리케이션 포괄 제공. 3D 뷰를 통해 조립 지시를 시각적으로 전달 |
| **작업 순서 강제/가이드** | 인터랙티브 작업 지시를 통한 단계별 가이드. 전자서명 요구 사항이 포함된 단계 검증(Step Validation). 편차 관리(Deviation Management) 내장 |
| **작업자 인터페이스** | 터치 환경 호환 인터페이스. Mendix 로우코드로 태블릿/키오스크용 커스텀 UI 개발 가능. AR 글래스를 통한 현장 지시 지원 |
| **다국어 지원** | Teamcenter Share 연계로 다국어 문서 관리. 글로벌 멀티사이트 환경 지원 |
| **EBR(전자배치기록)** | Opcenter Execution Pharma(구 SIMATIC IT eBR)로 완전한 전자 배치 기록 지원. 고급 워크플로 엔진과 전자 작업 지시(EWI) 기반 페이퍼리스 제조 |

**핵심 차별점**: 3D/AR 기반 작업 지시는 3사 중 가장 앞서 있음. Teamcenter PLM과의 직접 연계로 설계 변경이 실시간으로 작업 지시에 반영. 제약 산업용 EBR이 독립 모듈로 존재하여 GxP 환경에 최적.

---

### 2.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **전자 작업지시서(e-WI)** | **Guided Work Instructions(GWI)**와 Canvas Envision 연계 **Interactive Work Instructions(IWI)** 제공. 멀티미디어 콘텐츠(시각 자료, 동영상) 포함 가능 |
| **작업 순서 강제/가이드** | 단계별 디지털 지시로 오류 방지(Error-proofing). 가장 복잡한 작업도 단계별로 표준화하여 온보딩 시간 단축. 실시간 가이드 제공 |
| **작업자 인터페이스** | Connected Worker 솔루션으로 Rockwell 애플리케이션 및 서드파티 시스템과 통합. 디지털 작업 지시를 오퍼레이터 수준에서 직접 제공 |
| **다국어 지원** | **25개 이상 언어** 지원 (아랍어, 중국어, 한국어, 일본어, 힌디어, 히브리어 등 포함). 3사 중 가장 광범위한 다국어 지원 |

**핵심 차별점**: 25개 이상 언어 지원은 글로벌 다국적 제조업체에 결정적 이점. Connected Worker 솔루션으로 인력 관리와 작업 지시가 통합. 다만 3D/AR 수준의 고급 시각화는 Siemens에 뒤처짐.

---

### 2.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **전자 작업지시서(e-WI)** | **Production Operator Dashboard(POD)**를 통한 작업 지시 표시. Guided Steps를 통해 작업자를 구조화된 생산 프로세스로 안내. 작업 지시 열람 이력 자동 기록 |
| **작업 순서 강제/가이드** | POD 기반으로 작업 순서를 시각적으로 가이드. 컴포넌트 조립, 데이터 수집, 생산 데이터 기록 등을 단계별 안내 |
| **작업자 인터페이스** | POD가 현장 오퍼레이터와 시스템 간의 메인 인터페이스. 커스터마이징 가능한 대시보드 레이아웃. 여러 POD에서 공통 기능(작업 지시, 부품 조립, 데이터 수집) 공유 |
| **다국어 지원** | 자재 설명의 로컬라이즈 표시 지원. SAP 플랫폼의 글로벌 다국어 인프라 활용 |

**핵심 차별점**: POD(Production Operator Dashboard)는 직관적이고 커스터마이징이 용이하나, 3D/AR 지원에서는 Siemens에 뒤처짐. SAP S/4HANA 작업 오더와의 원활한 동기화가 강점. EBR 기능은 Siemens 대비 독립 모듈이 부재하여 제약 산업 적용 시 추가 솔루션 필요.

---

### 2.4 작업지시 관리 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| 3D 작업지시 | 내장 지원 | 미지원 | 미지원 |
| AR 지원 | 내장 지원 | 미지원 | 미지원 |
| 다국어 지원 | 지원 (수량 미공개) | 25개+ 언어 | SAP 글로벌 인프라 |
| EBR(전자배치기록) | 전용 모듈 (Pharma) | 미지원 | 제한적 |
| 로우코드 커스텀 UI | Mendix | Canvas Envision | POD 프레임워크 |

---

## 3. 품질 관리 (Quality Management)

### 3.1 Siemens Opcenter Quality (구 IBS QMS)

| 항목 | 상세 내용 |
|------|----------|
| **SPC 내장** | Opcenter Quality SPC 모듈 완전 내장. X-bar/R, X-bar/S, p, np, c, u 차트 등 표준 관리도 전체 지원. SPC 방법론의 체계적 구현 및 검사 문서화 |
| **검사 계획 자동 생성** | 품질 감사 관리(Audit Management) 모듈로 검사 계획 체계적 수립. 공정 내 검사, 초품 검사, 최종 검사 등 자동화 |
| **CAPA 워크플로** | 문서 관리, 교육 관리, 품질 이벤트 관리, CAPA 관리, 변경 관리, 불만 관리를 포괄하는 통합 품질 워크플로 |
| **불량 분류** | Pareto 분석, 근본 원인 분석(Root Cause Analysis) 내장. 성능 분석과 연계한 시정 조치 |
| **LIMS 연동** | **Opcenter Laboratory(구 SIMATIC IT Unilab)**와 네이티브 통합. 멀티사이트/다부서 커버 가능. 배치 샘플링 및 실험실 시험 관리를 MES와 직접 연계. 자동 릴리스 및 알림 처리 |

**핵심 차별점**: LIMS(Opcenter Laboratory)가 동일 벤더 포트폴리오에 포함되어 MES-LIMS 간 가장 긴밀한 네이티브 통합 가능. IBS QMS로부터 축적된 수십 년의 품질 관리 전문성. FDA, ISO 등 다양한 규제 표준 동시 지원.

---

### 3.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **SPC 내장** | SPC 데이터 수집 및 시각화 내장. 표준 편차, 공정 능력(Cp/Cpk) 자동 계산. 전자 게이지/계량기 직접 연결로 수동 입력 제거 가능 |
| **검사 계획 자동 생성** | 관리 계획(Control Plan)에서 품질 절차 직접 관리. 능력 연구(Capability Study), 입고 검사(Dock Audit), 치수 레이아웃, 초품/최종 검사 시트, 사용자 정의 검사 지원 |
| **CAPA 워크플로** | **8D, 5 Why** 등 표준 문제 해결 기법 내장. 봉쇄(Containment), 시정(Correction), 예방(Prevention) 조치 할당 및 추적. CAPA가 재고, 로트 추적, 불량품, 출하와 통합되어 컨테이너/개별 부품 수준까지 추적 |
| **불량 분류** | FMEA(DFMEA, PFMEA), HACCP 프로세스, PPAP, 초품 검사 등 포괄적 품질 도구. 편차 추적(Deviation Tracking) 내장 |
| **LIMS 연동** | 네이티브 LIMS 모듈 없음. 서드파티 LIMS와 API 연동 필요 |

**핵심 차별점**: CAPA가 재고/로트/출하 시스템과 직접 통합되어 불량 발생 시 즉각적인 격리 및 추적이 가능한 점이 독보적. 전자 게이지 직접 연결로 SPC 데이터 수동 입력 부담 제거. 식음료(HACCP, FSMA, SQF) 규정 준수에 특히 강함.

---

### 3.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **SPC 내장** | 자체 SPC는 제한적. **Syntax SPC** 등 파트너 솔루션 연계 또는 **Minitab Real-Time SPC** 통합으로 고급 SPC 기능 제공. POD에 실시간 데이터 시각화 및 자동 편차 알림 |
| **검사 계획 자동 생성** | SAP QM(Quality Management) 모듈과 연계하여 검사 계획 관리. 검사, 편차, CAPA를 엔지니어링/구매/생산 팀 간 공유 |
| **CAPA 워크플로** | SAP QM을 통한 CAPA 프로세스. 결함, 부적합, 시정 조치를 기록하고 부서 간 소통. SAP 워크플로 엔진 활용 |
| **불량 분류** | 품질 지표 추적 및 품질 관리 기능. 검사 및 편차에 대한 감사 준비 문서화 |
| **LIMS 연동** | **SAP QM 자체를 LIMS로 활용** 가능. S/4HANA와 직접 통합으로 자재 관리, 생산, 영업 프로세스와 데이터 격벽 없이 연계. 샘플 관리, 분석, 문서화의 end-to-end 추적 |

**핵심 차별점**: SPC를 파트너 솔루션(Minitab, Syntax)에 의존하는 것이 약점이나, SAP QM을 LIMS로 활용할 수 있어 별도 LIMS 구매 없이 실험실 관리가 가능. SAP ERP의 QM 모듈과 원활하게 통합되어 품질 데이터가 구매/생산/영업과 자연스럽게 연결.

---

### 3.4 품질 관리 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| SPC 내장 수준 | ★★★★★ (전용 모듈) | ★★★★☆ (내장 기본) | ★★☆☆☆ (파트너 의존) |
| CAPA 통합 깊이 | 품질 이벤트 전체 | 재고/로트/출하 직접 연계 | SAP QM 의존 |
| LIMS | 자체 보유(Opcenter Lab) | 서드파티 필요 | SAP QM as LIMS |
| 산업별 품질 규정 | 범산업 (FDA/ISO 등) | 식음료(HACCP/FSMA) 강점 | SAP 생태계 내 통합 |
| 전자 게이지 연결 | 지원 | 직접 연결 (차별화) | 제한적 |

---

## 4. 추적성/이력 관리 (Traceability & Genealogy)

### 4.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **추적 단위** | 개별 단품(Serial), 로트(Lot), 배치(Batch) 모두 지원. 산업별 특화 버전에 따라 웨이퍼/다이 수준 추적(반도체), 배치 기록(제약) 등 |
| **역추적/순추적** | 완전한 양방향 추적성. 완제품에서 원자재(Backward), 원자재에서 완제품(Forward) 모두 가능. 컴포넌트의 사용 이력 기록 및 계보(Genealogy) 관리 |
| **직렬화(Serialization)** | 개별 단품 직렬화 완전 지원. 제약 산업용 직렬화(Aggregation 포함) 전문 모듈 보유 |
| **바코드/QR/RFID** | 바코드, QR, RFID 전체 지원. Opcenter Intra Plant Logistics와 연계하여 캐리어 수준 추적 |

**핵심 차별점**: 반도체(웨이퍼/다이 추적), 제약(배치 기록/직렬화), 전자(PCB 추적) 등 산업별로 특화된 추적 단위와 규칙을 미리 구성하여 제공. Teamcenter PLM과 연계 시 설계-제조 전체 이력을 단일 디지털 스레드로 관리 가능.

---

### 4.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **추적 단위** | 직렬화된 바코드 기반 개별 추적 및 로트 추적 모두 지원. 컨테이너 또는 개별 부품 수준까지 추적 가능 |
| **역추적/순추적** | 양방향 추적성 지원. 리콜 발생 시 실시간 로트 추적으로 **수분 내 대응** 가능(벤더 공식 주장) |
| **직렬화(Serialization)** | 직렬화된 바코드 라벨 기반 추적. 각 공정 단계별로 일시, 소요 시간, 작업자, 수행 프로세스 기록 |
| **바코드/QR/RFID** | RFID 및 바코드 스캐닝을 재고 관리와 직접 통합. 실시간 정확성 확보 |

**핵심 차별점**: "수분 내 리콜 대응"을 강조하는 실시간 로트 추적 능력. RFID/바코드가 재고 관리 시스템과 원천 통합되어 추가 미들웨어 없이 작동. ERP-MES 단일 시스템이므로 추적 데이터의 일관성이 높음.

---

### 4.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **추적 단위** | **SFC(Shop Floor Control)** 단위로 추적. 반제품/완제품별 조립된 컴포넌트, 재고 ID, 시리얼 넘버 기록. **배치 크기 1(Batch Size 1)**까지 직렬화 가능 |
| **역추적/순추적** | **As-Built Record** 및 **Genealogy Record** 자동 생성. Product History Report(PHR), Product Genealogy Report(PGR), SFC Report 앱 제공. 조립 중 수집된 데이터 필드도 이력에 포함 |
| **직렬화(Serialization)** | SAP Business Network Material Traceability와 연계한 기업 간(Cross-enterprise) 직렬화. Genealogy API 제공으로 외부 시스템과 추적 데이터 교환 |
| **바코드/QR/RFID** | POD에서 직접 바코드/시리얼 넘버 스캔 및 기록. 자동화 시스템/센서 인터페이스를 통한 자동 데이터 수집 |

**핵심 차별점**: SAP Business Network을 통한 **기업 간(Cross-enterprise) 추적성**이 고유한 강점. 공급망 전체에 걸친 자재 추적이 가능. As-Built/Genealogy 기록이 자동 생성되어 수동 작업 최소화. PHR/PGR/SFC Report 등 다양한 리포팅 앱 제공.

---

### 4.4 추적성 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| 산업별 특화 추적 | ★★★★★ (반도체/제약 전용) | ★★★☆☆ (범용) | ★★★★☆ (SFC 기반) |
| 리콜 대응 속도 | 높음 | 매우 높음 (수분 내) | 높음 |
| 기업 간 추적 | 제한적 | 제한적 | ★★★★★ (SAP BN) |
| PLM 연계 이력 | Teamcenter 네이티브 | 서드파티 PLM 연동 | SAP PLM 연동 |

---

## 5. 설비/자산 관리 (Equipment/Asset Management)

### 5.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **OEE 자동 계산** | Opcenter Execution Foundation OEE 전용 모듈. 가용률(Availability), 성능(Performance), 품질(Quality/불량률) 자동 모니터링 및 계산. 기계 상태/성능 실시간 추적 |
| **예방보전(PM)** | 생산 수량 및 경과 사용 시간 기반 리소스 추적. 생산이 유지보수 요구를 초과하지 않도록 자동 관리 |
| **예지보전(PdM)** | OEE Analytics로 예측적 통찰 제공. 고급 알고리즘을 활용한 유지보수 일정 최적화. 예측 분석 기반 장비 효율 개선 |
| **실시간 모니터링** | 실시간 대시보드에서 KPI 모니터링. 자동화/IoT 수준까지 드릴다운 가능. 메시징/알람/시정 조치 관리 |
| **CMMS 연동** | 외부 CMMS와 API 연동 가능. 자체적으로는 MOM 차원의 자산 관리 초점 |

**핵심 차별점**: OEE 전용 모듈(Foundation OEE)이 독립적으로 존재하여 MES 없이도 OEE 관리 가능. IoT/자동화 수준까지의 드릴다운과 예측 분석이 결합된 종합적 접근.

---

### 5.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **OEE 자동 계산** | 생산 처리량, 가동 시간, 품질의 핵심 운영 KPI 기반 OEE 자동 계산. 비용 많은 다운타임 추적 및 감소 지원 |
| **예방보전(PM)** | 생산 추적, 스케줄링, 용량 계획, 예방보전, 설비 목록 등 다수 모듈과 통합 |
| **예지보전(PdM)** | **Plex APM(Asset Performance Management)** 전용 모듈. IIoT 기술과 스마트 분석 기반 예지보전. 기계 건강 상태 실시간 모니터링, 비계획 다운타임 감소, 장비 수명 연장 |
| **실시간 모니터링** | 시설/작업 셀/자산별 라이브 대시보드. 색상 코딩(Off, In-Cycle, Idle, Problem, Other)으로 즉각 상태 파악. 맥락화된(Contextualized) 기계 데이터(작업 번호, 부품 번호, 작업 센터 상태) |
| **CMMS 연동** | 자체 APM이 CMMS 기능 일부 대체. 외부 CMMS와 API 연동 가능 |

**핵심 차별점**: APM 전용 모듈이 IIoT와 결합하여 예지보전에 특히 강함. 색상 코딩 실시간 대시보드는 현장 가시성 측면에서 가장 직관적. 클라우드 기반이므로 멀티사이트 설비 데이터 중앙 집중 관리 용이.

---

### 5.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **OEE 자동 계산** | OEE 성능 지표를 분석 대시보드에서 제공. 사전 구성된 산업 표준 KPI 및 커스텀 KPI 지원 |
| **예방보전(PM)** | SAP Enterprise Asset Management(EAM)와 연계. SAP PM(Plant Maintenance) 모듈 통합 |
| **예지보전(PdM)** | **SAP Asset Performance Management(APM)** 연계. IoT 센서, ML 기반 고장 확률 계산 및 잔존 수명(RUL) 추정. Deloitte 보고: PdM으로 다운타임 5~15% 감소, 노동 생산성 5~20% 향상 |
| **실시간 모니터링** | IoT 센서 데이터 실시간 수집. 조건 모니터링(Condition Monitoring) 기반 상태 감시 |
| **CMMS 연동** | **LLumin CMMS+** 등 SAP Store 파트너와 연동. SAP S/4HANA와 통합되어 작업 오더, 자원, 일정 관리를 ERP 워크플로에 정렬 |

**핵심 차별점**: SAP EAM/PM과의 네이티브 통합으로 자산 관리가 전사적 ERP 워크플로에 포함되는 것이 강점. 다만 DMC 자체보다는 SAP PM, SAP APM 등 외부 모듈에 의존하는 구조.

---

### 5.4 설비/자산 관리 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| OEE 전용 모듈 | Foundation OEE (독립) | 내장 | 분석 대시보드 |
| 예지보전 AI/ML | OEE Analytics | APM (IIoT 결합) | SAP APM (외부 모듈) |
| 실시간 모니터링 UI | 드릴다운 대시보드 | 색상 코딩 라이브 대시보드 | IoT 센서 기반 |
| CMMS 통합 | API 연동 | APM이 일부 대체 | SAP PM/EAM 네이티브 |

---

## 6. 데이터 수집 (Data Collection/Acquisition)

### 6.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **PLC/SCADA 연결** | **OPC UA** 기반 핸드셰이크 메시지 전송(v4.4 이상). Automation Gateway를 통한 표준화된 shopfloor 통합. SIMATIC S7-300/400/1200/1500 네이티브 지원. OPC DA, Modbus TCP 등 레거시 프로토콜 게이트웨이 지원 |
| **엣지 게이트웨이** | **Siemens Industrial Edge** 플랫폼 제공. 엣지에서 데이터 전처리/필터링 후 MES로 전송. 노이즈 및 중복 데이터 최대 60% 감소 가능 |
| **수동 입력** | 터치 패널, 모바일 디바이스. Mendix 앱으로 커스텀 입력 화면 개발. 계량기/저울 OPC UA 인터페이스 직접 연결 |
| **수집 주기** | 밀리초 단위 고속 데이터 수집 가능 (Industrial Edge 활용 시). MES 레벨에서는 초~분 단위 |

**핵심 차별점**: Siemens 자체 PLC(SIMATIC S7)와의 네이티브 통합은 타사 추종 불가. Industrial Edge 플랫폼으로 엣지-클라우드 하이브리드 아키텍처 구현. OPC UA 기반 표준화된 연결 방식.

---

### 6.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **PLC/SCADA 연결** | OPC UA, MQTT를 주요 프로토콜로 사용. **Plex Mach2**를 통한 생산 현장 기계 연결. 표준화된 형식으로 프로토콜 변환 |
| **엣지 게이트웨이** | 엣지 디바이스를 통한 전처리 및 필터링. 노이즈/중복 데이터 제거 후 중앙 시스템 전송. 엣지에서의 실시간 분석 및 로컬 액션 가능 |
| **수동 입력** | Production Monitoring 모듈 통한 현장 입력. 전자 게이지/계량기 직접 연결 자동 입력 |
| **수집 주기** | 실시간 스트리밍 기반. 클라우드 네이티브 아키텍처로 대량 데이터 처리 |

**핵심 차별점**: Plex Mach2를 통한 플러그앤플레이 방식의 기계 연결. 클라우드 기반이므로 데이터 수집 후 즉시 전사적 가시성 확보. Allen-Bradley PLC(Rockwell 자사 제품)와의 친화성이 높음.

---

### 6.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **PLC/SCADA 연결** | **SAP Production Connector** 에이전트 기반. OPC DA, OPC HDA, OPC UA, MQTT, IP21, PI AF 등 다양한 프로토콜 지원. .NET 기반 온프레미스 애플리케이션으로 생산 네트워크 내 설치 |
| **엣지 게이트웨이** | **SAP Digital Manufacturing for Edge Computing** 제공. SAP BTP 기반 엣지 라이프사이클 관리. SAP Plant Connectivity(PCo)를 통한 shopfloor 연결. 엣지에서 데이터 맥락화/필터링 후 클라우드 전송 |
| **수동 입력** | POD(Production Operator Dashboard)에서 직접 입력. 작업자 또는 기계에 의한 자재 소비, 스크랩, 노동 시간, 시리얼 넘버 기록 |
| **수집 주기** | 엣지에서 고속 트랜잭션 처리 후 클라우드로 요약 데이터 전송. 하이브리드 아키텍처로 지연 시간 최소화 |

**핵심 차별점**: Production Connector가 지원하는 프로토콜 범위가 가장 넓음(OPC DA/HDA/UA, MQTT, IP21, PI AF). SAP BTP 기반 엣지 라이프사이클 중앙 관리. 다만 Production Connector가 Windows .NET 기반이라는 제약.

---

### 6.4 데이터 수집 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| 자사 PLC 네이티브 | SIMATIC S7 | Allen-Bradley | 없음 |
| 지원 프로토콜 수 | OPC UA, OPC DA, Modbus | OPC UA, MQTT | OPC DA/HDA/UA, MQTT, IP21, PI AF |
| 엣지 플랫폼 | Industrial Edge | Plex Edge | SAP DM Edge (BTP) |
| 엣지 기반 기술 | Linux 컨테이너 | 클라우드 네이티브 | Windows .NET |

---

## 7. 리포팅/분석 (Reporting & Analytics)

### 7.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **내장 대시보드** | Opcenter Intelligence(구 Manufacturing Intelligence) 전용 모듈. OOTB(Out-Of-The-Box) 표준 대시보드 + 산업별 특화 대시보드. 실시간 및 이력 데이터 KPI 표시 |
| **커스텀 리포트** | 사용자 정의 인터랙티브 대시보드 생성 가능. 스코어카드 생성 및 실시간 드릴다운(자동화/IoT 수준까지) |
| **BI 도구 연동** | Insights Hub(구 MindSphere) 연계로 클라우드 기반 분석. 외부 BI 도구와 API 연동 가능 |
| **AI/ML 예측 분석** | OEE Analytics에서 예측 기반 유지보수 인사이트 제공. 패턴 인식 및 이상 감지. Insights Hub의 AI/ML 엔진 활용 |

---

### 7.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **내장 대시보드** | APM 라이브 대시보드(시설/작업 셀/자산별). 색상 코딩 상태 표시. 맥락화된 기계 데이터 실시간 표시 |
| **커스텀 리포트** | 예지보전 리포트, 기계 건강 리포트, OEE 리포트 등. 클라우드 기반이므로 어디서나 접근 가능 |
| **BI 도구 연동** | Power BI 등 외부 BI 도구 연동 지원. IIoT 분석 플랫폼 내장 |
| **AI/ML 예측 분석** | IIoT 기반 스마트 분석으로 예측 유지보수. 기계 학습 기반 패턴 인식 |

---

### 7.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **내장 대시보드** | **SAP DMi(DM for Insights)** 전용 분석 컴포넌트. **SAP Analytics Cloud(SAC)** 내장. 사전 구성된 산업 표준 KPI + 커스터마이징 가능 |
| **커스텀 리포트** | Query Designer로 특정 로직 기반 KPI 쉽게 생성. **노코드** 애플리케이션 빌드 플랫폼으로 커스텀 대시보드 제작 |
| **BI 도구 연동** | SAP Analytics Cloud 네이티브 내장. 외부 BI 도구 연동도 가능하나 SAC 사용이 최적 |
| **AI/ML 예측 분석** | **AI 기반 시각 검사(Visual Inspection)** 기능으로 결함 감지. 품질 이슈 예측, 운영 가시성 향상, 생산 변경 대응. 패턴 감지 및 맞춤형 성능 개선 |

---

### 7.4 리포팅/분석 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| 분석 전용 모듈 | Opcenter Intelligence | IIoT Analytics | SAP DMi + SAC |
| 노코드 대시보드 | Mendix | 제한적 | Query Designer + 노코드 |
| AI 시각 검사 | 미내장 | 미내장 | 내장 지원 |
| 클라우드 분석 | Insights Hub | 네이티브 클라우드 | SAP Analytics Cloud |

---

## 8. 재고/자재 관리 (Inventory/Material Management)

### 8.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **WIP 실시간 추적** | 작업 센터 내/간 이동 및 저장 추적. 자재, 공정 중 품목, 완제품의 이동/저장 관리 |
| **자재 소비 자동 기록** | 작업 오더 오퍼레이션별 자재 요구량, 소비량, 생산량 기록. Backflush 지원 |
| **로트별 재고 관리** | 배치/로트 기반 재고 추적. 계보(Genealogy)와 연계 |
| **WMS 연동** | **Opcenter Intra Plant Logistics** 전용 모듈로 창고-생산 라인 간 자재 흐름 관리. 커미셔닝, 키팅, 피킹 오케스트레이션. 입고품 등록/보관, 요청 시각화/우선순위 관리 |

**핵심 차별점**: Intra Plant Logistics 모듈로 MES 내에서 공장 내 물류를 직접 관리할 수 있어 별도 WMS 없이도 기본적인 창고 관리 가능. 캐리어 단위(단일 운반체 수준)까지의 정밀 추적.

---

### 8.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **WIP 실시간 추적** | 원자재 입고부터 출하까지 전 과정 실시간 추적. WIP 포함 세분화된(Granular) 가시성 제공 |
| **자재 소비 자동 기록** | 실시간 재고 수준 및 자재 사용량 자동 추적. 정확한 생산 계획 및 낭비 감소 지원 |
| **로트별 재고 관리** | 로트 추적 및 추적성과 완전 통합. 식음료 등 규제 산업의 로트 관리에 강점 |
| **WMS 연동** | ERP-MES 통합 플랫폼이므로 재고 관리가 네이티브 내장. 외부 WMS 연동도 API 지원 |

**핵심 차별점**: ERP와 MES가 단일 플랫폼이므로 재고 데이터의 실시간 정합성이 가장 높음. 별도 인터페이스 없이 재고-생산-품질-출하가 하나의 데이터베이스에서 관리.

---

### 8.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **WIP 실시간 추적** | SFC(Shop Floor Control) 단위로 WIP 실시간 추적. 자재 소비, 스크랩, 노동 시간 등 현장 데이터 실시간 기록 |
| **자재 소비 자동 기록** | 오퍼레이터/기계에 의한 자재 소비 직접 기록. POD에서 실시간 WIP 데이터 표시 |
| **로트별 재고 관리** | SAP MM(Material Management)와 네이티브 통합. 배치/로트 관리 SAP 수준 |
| **WMS 연동** | **SAP EWM(Extended Warehouse Management)**과 OOTB(Out-Of-The-Box) 통합. 별도 미들웨어 없이 창고-생산 데이터 교환 |

**핵심 차별점**: SAP EWM과의 기본 제공 통합이 가장 강력한 WMS 연동. SAP MM/PP와 연계하여 자재 소요 계획(MRP)부터 현장 소비까지 end-to-end 자재 관리.

---

### 8.4 재고/자재 관리 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| WMS 내장 수준 | Intra Plant Logistics | ERP 내 재고 관리 | SAP EWM OOTB 통합 |
| WIP 추적 세분화 | 캐리어 수준 | 컨테이너/부품 수준 | SFC 수준 |
| ERP 재고 동기화 | API 연동 | 네이티브(단일 DB) | S/4HANA 네이티브 |

---

## 9. 레시피/BOM 관리

### 9.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **다단계 BOM** | Opcenter Execution Process에서 다단계 BOM 완전 지원. 화학-기계 조립까지 단일 MES 인스턴스로 관리 |
| **레시피 버전 관리** | 사양 관리 시스템(Opcenter Specification, 구 Interspec)과 긴밀 통합. 포뮬러, 레시피, BOM의 정확한 버전 관리 |
| **ECN/ECO** | **Teamcenter CMII 인증 변경 관리**. ECN(Engineering Change Notification)에 대한 자동 변경 추적. 다수 사용자가 동시에 ECN에 편집 내용 연결 가능. 완전한 추적성 보장 |
| **PLM 연동** | Teamcenter PLM과 네이티브 심리스 통합. eBOM-mBOM 자동 동기화. Teamcenter Share를 통한 클라우드 문서 공유 |

**핵심 차별점**: Teamcenter PLM과의 네이티브 통합으로 eBOM(설계 BOM) -> pBOM(생산 BOM) -> mBOM(제조 BOM) 변환이 가장 자연스러움. CMII 인증 변경 관리는 변경 프로세스의 산업 표준 준수를 보장.

---

### 9.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **다단계 BOM** | 복잡한 BOM(Bill of Materials) 관리 지원. 엔지니어링 변경 관리 통합 |
| **레시피 버전 관리** | 식음료 산업용 레시피 관리 기능 내장. 로트 추적 및 품질 관리와 연계 |
| **ECN/ECO** | 엔지니어링 변경 관리 내장. CAD-to-BOM 인터페이스(CADLink) 연동으로 CAD 데이터에서 BOM 자동 생성 가능 |
| **PLM 연동** | 서드파티 PLM과 API 연동. CADLink로 CAD/PLM 시스템과 BOM 데이터 교환 |

**핵심 차별점**: CADLink를 통한 CAD-to-BOM 자동 변환이 독특한 기능. ERP-MES 통합 플랫폼이므로 BOM 변경이 생산 계획에 즉시 반영. 식음료 레시피 관리에 특화.

---

### 9.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **다단계 BOM** | SAP PP(Production Planning)의 BOM 관리와 네이티브 연계. 제조 BOM 구조 지원 |
| **레시피 버전 관리** | **SAP PLM Recipe Development(RD)** 모듈. 레시피에서 생산 BOM/마스터 레시피로 데이터 동기화. 시험 생산용 레시피 전송 지원 |
| **ECN/ECO** | SAP PLM 변경 관리 프로세스. 생산 버전 할당 시 레시피-BOM-마스터 레시피 동기화 |
| **PLM 연동** | **Siemens Teamcenter, 3DExperience, Windchill, Autodesk** 등 외부 PLM 시스템과 통합 지원. Configure-to-Order 시나리오 구현 가능 |

**핵심 차별점**: SAP PLM RD의 레시피-BOM 동기화 기능은 프로세스 산업(식품/화학/제약)에 매우 강력. 외부 PLM 시스템(Teamcenter, 3DX, Windchill 등)과의 통합 범위가 가장 넓음.

---

### 9.4 레시피/BOM 관리 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| PLM 네이티브 통합 | Teamcenter (자사) | 없음 (서드파티) | 다수 PLM 지원 |
| 변경 관리 인증 | CMII 인증 | 내장 (비인증) | SAP PLM |
| 레시피-BOM 동기화 | Specification 모듈 | 식음료 특화 | PLM RD 전용 |
| CAD-BOM 변환 | Teamcenter 경유 | CADLink 직접 | PLM 연동 경유 |

---

## 10. 규정 준수 / Compliance

### 10.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **21 CFR Part 11** | 완전 준수. Opcenter Quality는 21 CFR Part 11, FDA 820 준수 인증. 전자 기록/전자 서명 완전 지원 |
| **EU Annex 11** | 완전 준수. EU 규제 환경에 대한 검증된 지원 |
| **전자서명/감사추적** | 배치 기록 항목, 공정 파라미터 변경, 장비 세척 로그, 오퍼레이터 편차 등 전체 감사 추적. 전자 서명 요구 사항 내장 |
| **EBR 자동 생성** | **Opcenter Execution Pharma(구 SIMATIC IT eBR)** 전용 모듈. 완전한 페이퍼리스 제조 및 전자 배치 기록. 신약/백신 생산 가속화 |
| **GxP 밸리데이션** | ISO 9001, 13485, 14971, 27001 등 다수 표준 준수. 의료기기, 항공우주, 제약 등 규제 산업별 전용 버전 제공. 밸리데이션 간소화 도구 |

**핵심 차별점**: 규정 준수 분야에서 가장 포괄적인 지원. 제약/의료기기/반도체 등 규제 산업별 전용 버전이 존재하며, EBR 전용 모듈(Opcenter Pharma)은 업계 레퍼런스. "밸리데이션 없이는 지체만 발생한다(Without the Drag)"는 접근으로 밸리데이션 프로세스 자체를 간소화.

---

### 10.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **21 CFR Part 11** | 클라우드 SaaS 환경에서의 규정 준수 지원. 전자 기록/서명은 지원하나, Siemens 수준의 전용 규제 모듈은 부재 |
| **EU Annex 11** | 기본적 지원. 유럽 규제 환경 대응 가능 |
| **전자서명/감사추적** | 감사 추적 기능 내장. 전자 서명 지원 |
| **EBR 자동 생성** | 전용 EBR 모듈 부재. 프로세스 산업/제약 전용 기능 제한적 |
| **GxP 밸리데이션** | 식음료 규정 준수에 강점: **HACCP, FSMA, SQF** 준수 간소화. 감사 대비 및 CAPA 내장. 제약/의료기기 GxP에는 상대적 약점 |

**핵심 차별점**: 식음료 산업의 식품 안전 규정(HACCP, FSMA, SQF)에 가장 최적화. 제약/의료기기 등 GxP 규제 산업에는 Siemens/SAP에 비해 기능 부족. 클라우드 SaaS 특성상 "폐쇄 시스템(Closed System)" 여부에 대한 규제 해석 필요.

---

### 10.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **21 CFR Part 11** | **"GxP capable"** 솔루션으로 규정 준수 지원은 하나 인증은 아님. 고객이 GxP 규정 준수를 직접 검증해야 함 |
| **EU Annex 11** | 지원. SAP Quality Requirement Schedule 제공 |
| **전자서명/감사추적** | 공유 책임 모델(Shared Responsibility Model). SAP가 관리하는 영역과 고객이 책임지는 영역 구분. 감사권(Right to Audit) 보장 |
| **EBR 자동 생성** | 전용 EBR 모듈 부재. SAP 파트너 솔루션 필요 |
| **GxP 밸리데이션** | IQ/OQ/PQ 프로세스 지원. 확장(Extension) 개발 시 별도 GxP 평가 필요. 클린 코어 원칙 준수 권장. 생명과학 기업에 대한 규제 가이드 백서 제공 |

**핵심 차별점**: "GxP capable"이지만 "GxP certified"는 아니라는 점이 중요. 공유 책임 모델로 SAP와 고객 간 역할 분담이 명확. SAP 백서와 가이드가 풍부하여 규제 대응 프레임워크는 제공되나, 실제 규정 준수 입증은 고객 책임.

---

### 10.4 규정 준수 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| 21 CFR Part 11 | ★★★★★ (완전 준수) | ★★★☆☆ (기본 지원) | ★★★★☆ (GxP capable) |
| EBR 전용 모듈 | Opcenter Pharma | 없음 | 없음 |
| 식품안전 규정 | 지원 | ★★★★★ (HACCP/FSMA) | 지원 |
| GxP 밸리데이션 | 산업별 전용 버전 | 제한적 | 공유 책임 모델 |
| 감사 추적 | 완전 내장 | 내장 | 공유 책임 |

---

## 11. 시스템 아키텍처 / 확장성

### 11.1 Siemens Opcenter

| 항목 | 상세 내용 |
|------|----------|
| **아키텍처** | 모듈 기반 아키텍처. 완전한 마이크로서비스는 아니나 Mendix와 결합 시 마이크로서비스 패턴 구현 가능. Opcenter X(SaaS)는 클라우드 네이티브 설계 |
| **API 방식** | **REST API** 및 **SOAP** 제공. 데이터 모델과 API를 외부에 노출하여 컴포저블 아키텍처 지원 |
| **로우코드/노코드** | **Mendix 로우코드** 플랫폼 네이티브 통합. 비개발자도 워크플로/UI 확장 가능. 커스텀 코드, API, 마이크로서비스로 앱 확장. UI 개발 시간 50% 단축 |
| **멀티사이트** | 멀티사이트 글로벌 운영 지원. 중앙 관리/분산 실행 아키텍처. On-premises, Cloud, VPC, SaaS(Opcenter X) 배포 옵션 |
| **오프라인 운영** | On-premises 배포 시 네트워크 독립 운영 가능. Industrial Edge에서 로컬 데이터 처리 가능 |

**핵심 차별점**: Mendix 로우코드는 MES 업계에서 가장 성숙한 로우코드 확장 도구. 코어 제품을 오염시키지 않고(without polluting the core) 기능을 레이어링할 수 있는 컴포저블 아키텍처. 배포 옵션의 유연성(On-prem/Cloud/VPC/SaaS)이 가장 넓음.

---

### 11.2 Rockwell Plex MES

| 항목 | 상세 내용 |
|------|----------|
| **아키텍처** | **클라우드 네이티브, 싱글 인스턴스, 멀티테넌트 SaaS**. 2025년 **Elastic MES** 아키텍처로 진화: 독립 배포 가능한 모듈, 점진적 기능 확장(Land-and-Expand) 전략 |
| **API 방식** | **REST API** 제공. 고객 주문, 출하, JIS(Just-In-Sequence) 등 다양한 엔드포인트. 오픈 API로 ERP, 계획, 품질, 창고 시스템과 연결 |
| **로우코드/노코드** | **노코드 커스터마이징 도구** 제공하여 IT 의존도 감소. Elastic MES 플랫폼의 핵심 평가 기준 중 하나 |
| **멀티사이트** | 멀티사이트에서 공유 데이터/앱과 사이트별 데이터/앱 구분 관리 가능. 단일 인스턴스이므로 전사적 가시성 자동 확보 |
| **오프라인 운영** | **Elastic MES 엣지 노드**로 네트워크 단절 시에도 로컬 운영 유지. 연결 복구 시 생산/품질/재고 데이터 자동 동기화. **100% 클라우드부터 완전 레질리언트 엣지까지** 유연한 배포 |

**핵심 차별점**: 업계 유일의 "Elastic MES" 개념. 클라우드 네이티브이면서도 엣지 레질리언스를 갖추어 네트워크 단절에도 운영 지속 가능. 단일 인스턴스 멀티테넌트이므로 소프트웨어 업데이트가 모든 고객에게 동시 적용되어 항상 최신 버전 유지.

---

### 11.3 SAP Digital Manufacturing

| 항목 | 상세 내용 |
|------|----------|
| **아키텍처** | **SAP BTP(Business Technology Platform) Cloud Foundry** 기반 SaaS. **마이크로서비스 아키텍처**: 자원 관리, 주문 라우팅 등 기능별 독립 배포 가능. Azure/AWS 하이퍼스케일러 위에서 구동 |
| **API 방식** | **REST API** 및 **웹 서비스** 제공. SAP BTP 기반 통합 API/웹 서비스 연결. ERP, MES, PLM 시스템과 통합 |
| **로우코드/노코드** | **노코드 애플리케이션 빌드 플랫폼** 내장. POD 프레임워크로 커스텀 대시보드 생성. Query Designer로 KPI 자체 정의. 단, 확장 시 GxP 환경에서는 별도 IQ/OQ/PQ 필요 |
| **멀티사이트** | SAP S/4HANA/Cloud ERP와의 분산 제조 워크플로 지원. 데이터 중복, 책임 분리, 사용 편의성, 성능, 밸리데이션 요구 사항 간 균형 |
| **오프라인 운영** | **SAP DM for Edge Computing**으로 오프라인 운영 지원. 엣지에서 구성/비즈니스 데이터 동기화. 고가용성(HA) 옵션 제공. 엣지-클라우드 간 데이터 자동 동기화 |

**핵심 차별점**: SAP BTP 기반의 진정한 마이크로서비스 아키텍처는 3사 중 가장 현대적. 하이퍼스케일러(Azure/AWS) 위에서 구동되므로 글로벌 확장성이 뛰어남. 다만 SAP 생태계 의존도가 높아 독립 운영이 어려움.

---

### 11.4 시스템 아키텍처 3사 비교 요약

| 비교 항목 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|-----------------|---------|---------|
| 아키텍처 유형 | 모듈 기반 + Mendix | Elastic MES (클라우드 네이티브) | 마이크로서비스 (BTP) |
| 배포 옵션 | On-prem/Cloud/VPC/SaaS | 100% Cloud ~ Edge | SaaS + Edge |
| 로우코드 성숙도 | ★★★★★ (Mendix) | ★★★☆☆ (노코드 도구) | ★★★★☆ (노코드 빌더) |
| 오프라인 운영 | On-prem 가능 | Elastic Edge 노드 | DM Edge Computing |
| 멀티테넌트 | Opcenter X만 | 전체 (싱글 인스턴스) | BTP 클라우드 |
| 벤더 독립성 | 상 (다양한 ERP 연동) | 중 (Plex ERP 최적) | 하 (SAP 생태계 필수) |

---

## 종합 비교 매트릭스

| 기능 영역 | Siemens Opcenter | Plex MES | SAP DMC |
|----------|:---:|:---:|:---:|
| **1. APS/스케줄링** | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| **2. 작업지시 관리** | ★★★★★ | ★★★★☆ | ★★★☆☆ |
| **3. 품질 관리** | ★★★★★ | ★★★★★ | ★★★☆☆ |
| **4. 추적성/이력** | ★★★★★ | ★★★★☆ | ★★★★★ |
| **5. 설비/자산 관리** | ★★★★☆ | ★★★★★ | ★★★☆☆ |
| **6. 데이터 수집** | ★★★★★ | ★★★★☆ | ★★★★☆ |
| **7. 리포팅/분석** | ★★★★☆ | ★★★★☆ | ★★★★★ |
| **8. 재고/자재 관리** | ★★★★☆ | ★★★★★ | ★★★★☆ |
| **9. 레시피/BOM** | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| **10. 규정 준수** | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| **11. 아키텍처/확장성** | ★★★★☆ | ★★★★★ | ★★★★☆ |
| **종합** | **4.6** | **3.8** | **3.7** |

---

## 솔루션별 최종 평가

### Siemens Opcenter - "가장 포괄적인 MOM 플랫폼"

**강점**
- 11개 기능 영역 중 7개에서 최고 수준(APS, 작업지시, 품질, 추적성, 데이터 수집, BOM, 규정 준수)
- Teamcenter PLM과의 네이티브 디지털 스레드로 설계-제조 연속성 확보
- Mendix 로우코드로 업계 최고 수준의 확장성
- 산업별 전용 버전(반도체, 제약, 전자, 의료기기 등)으로 깊이 있는 지원
- Gartner/IDC 양대 분석 기관에서 모두 Leader 선정

**약점**
- 높은 초기 도입 비용 및 구현 복잡도
- Siemens 에코시스템 종속 가능성
- 순수 클라우드 네이티브 아키텍처로의 전환이 경쟁사 대비 느림

**적합 대상**: 대기업, 멀티사이트 글로벌 운영, 규제 산업(제약/의료기기/반도체), PLM 연계 필수 환경

---

### Rockwell Plex MES - "클라우드 네이티브 통합 플랫폼"

**강점**
- 업계 유일의 Elastic MES 개념으로 클라우드-엣지 최적 균형
- ERP-MES 단일 플랫폼으로 데이터 일관성 최고
- 25개+ 다국어 지원으로 글로벌 다국적 기업에 최적
- 설비/자산 관리(APM)에서 IIoT 기반 예지보전 차별화
- 식음료(HACCP/FSMA/SQF) 규정 준수에 최적화
- 빠른 배포 및 즉시 사용 가능(SaaS)

**약점**
- Plex ERP를 함께 사용해야 최적 성능(All-or-Nothing 경향)
- 반도체/제약 등 초복잡/고규제 산업 기능 부족
- APS 깊이가 Siemens에 비해 부족
- PLM 네이티브 통합 부재

**적합 대상**: 클라우드 우선 전략 기업, 중견기업, 식음료/자동차/소비재, 빠른 배포 필요 환경

---

### SAP Digital Manufacturing - "SAP 생태계 최강 통합"

**강점**
- S/4HANA와의 네이티브 통합이 타의 추종 불허
- SAP BTP 기반 마이크로서비스 아키텍처(가장 현대적)
- SAP Analytics Cloud 내장으로 분석/리포팅 강력
- AI 기반 시각 검사(Visual Inspection) 내장
- SAP Business Network 통한 기업 간 추적성
- 외부 PLM 시스템(Teamcenter, 3DX, Windchill 등) 폭넓은 연동

**약점**
- SAP 생태계 외부에서는 가치가 크게 감소
- SPC, EBR 등 핵심 기능이 파트너/외부 모듈 의존
- APS가 S/4HANA PP/DS에 의존하여 독립 사용 불가
- 높은 복잡도, 중견 기업에는 과중한 시스템
- "GxP capable"이지 "GxP certified"는 아님

**적합 대상**: SAP S/4HANA 사용 대기업, 자동차/항공우주/화학, SAP 생태계 올인 전략

---

## 참고 자료

- [Siemens Opcenter Execution 공식 페이지](https://plm.sw.siemens.com/en-US/opcenter/execution/)
- [Siemens Opcenter APS 공식 페이지](https://plm.sw.siemens.com/en-US/opcenter/advanced-planning-scheduling-aps/)
- [Siemens Opcenter Quality SPC](https://blogs.sw.siemens.com/opcenter/boost-statistical-process-control/)
- [Siemens Opcenter Execution Pharma (EBR)](https://plm.sw.siemens.com/en-US/opcenter/execution/pharma/)
- [Siemens Opcenter Foundation OEE](https://plm.sw.siemens.com/en-US/opcenter/execution/foundation-oee/)
- [Siemens Opcenter Intelligence](https://plm.sw.siemens.com/en-US/opcenter/manufacturing-intelligence/)
- [Siemens Opcenter Intra Plant Logistics](https://plm.sw.siemens.com/en-US/opcenter/intraplant-logistics/)
- [Siemens Opcenter Laboratory (LIMS)](https://plm.sw.siemens.com/en-US/opcenter/research-development-laboratory/laboratory/)
- [Siemens Mendix-Opcenter 통합](https://www.sw.siemens.com/en-US/integrate-mendix-with-opcenter-mes-software/)
- [Rockwell Plex Smart Manufacturing Platform](https://plex.rockwellautomation.com/en-us.html)
- [Rockwell Plex QMS](https://plex.rockwellautomation.com/en-us/quality-management-system-capterra.html)
- [Rockwell Plex Finite Scheduler](https://plex.rockwellautomation.com/en-us/products/plex-finite-scheduler.html)
- [Rockwell Plex APM](https://www.plex.com/products/asset-performance-management)
- [Rockwell Plex Elastic MES](https://plex.rockwellautomation.com/en-us/products/manufacturing-execution-system/elastic-mes-guide.html)
- [Rockwell Plex Guided Work Instructions](https://www.plex.com/blog/every-worker-every-step-transform-your-operational-efficiency-guided-work-instructions)
- [SAP Digital Manufacturing 공식 페이지](https://www.sap.com/products/scm/digital-manufacturing/features.html)
- [SAP Digital Manufacturing FAQ](https://pages.community.sap.com/topics/digital-manufacturing/faq)
- [SAP Digital Manufacturing for Edge Computing](https://help.sap.com/docs/sap-digital-manufacturing/integration-guide/sap-digital-manufacturing-for-edge-computing-integration)
- [SAP Digital Manufacturing 규제 환경 백서](https://help.sap.com/doc/0143cc4d32a2411497e3eb26e0b329a3/Latest/en-US/4.0-SAP%20Digital%20Manufacturing%20in%20Regulated%20Environments%20Quality%20and%20Compliance.pdf)
- [SAP S/4HANA PP/DS](https://www.sap.com/products/scm/manufacturing-for-planning-and-scheduling.html)
- [SAP Production Connector](https://www.systema.com/portfolio/sap-manufacturing/sap-production-connector)
- [SAP Analytics Cloud for Manufacturing](https://community.sap.com/t5/supply-chain-management-blog-posts-by-sap/sap-digital-manufacturing-and-role-of-artificial-intelligence/ba-p/13893261)
- [Gartner Peer Insights - MES Reviews 2026](https://www.gartner.com/reviews/market/manufacturing-execution-systems)
- [IDC MarketScape: Worldwide MES 2024-2025](https://plex.rockwellautomation.com/content/dam/plex/legacy/2025-03/Rockwell_Automation_IDC%20MarketScape%20MES%20Vendor%20Assessment%202025.pdf)
- [Siemens vs Plex vs SAP MES 비교 (CLEVR)](https://www.clevr.com/blog/siemens-opcenter-vs-other-mom-tools-top-mom-solutions-compared)

---

> **면책 조항**: 본 문서는 2024~2026년 공개 자료(벤더 공식 문서, Gartner/IDC 분석 보고서, 사용자 리뷰)를 기반으로 한 비교 분석이며, 별점 평가는 기능의 깊이, 성숙도, 차별성을 종합한 상대적 평가입니다. 정확한 기능 범위 및 가격은 각 벤더에 직접 확인하시기 바랍니다.
