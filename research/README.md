# MES 프로젝트 기획 리서치 자료

> 이 디렉토리는 **기획/사업 기획용 리서치 자료**를 보관합니다.
> 개발 문서(`doc/`)와는 별도로 관리됩니다.

## 디렉토리 구조

```
research/
├── README.md
│
│  ── Part 1. 기본 리서치 ──
├── 01_MES_개요_및_핵심기능.md
├── 02_MES_시장규모.md
├── 03_경쟁사_분석_및_시장점유율.md
├── 04_경쟁사_솔루션_기능_비교.md
│
│  ── Part 2. 세부 기능 심층 비교 ──
├── 05_Siemens_Rockwell_SAP_세부기능_심층비교.md
├── 06_Dassault_Honeywell_GE_세부기능_심층비교.md
├── 07_AVEVA_Oracle_Aegis_Critical_한국벤더_세부기능_심층비교.md
│
│  ── Part 3. 경영학적 프레임워크 분석 ──
├── 08_전략적_시장구조_분석_Porter_BCG_SWOT.md
├── 09_내부역량_운영효율성_분석_VRIO_ValueChain_7S.md
├── 10_고객가치_제품차별화_분석_Kano_JTBD_Canvas.md
├── 11_실행전략_기술인텔리전스_7P_Patent_Benchmark.md
│
│  ── Part 4. 한계점 분석 ──
└── limitations/
    ├── 00_종합_한계점_요약.md
    ├── 01_기능갭_분석_MESA11_비교.md
    ├── 02_아키텍처_한계점_분석.md
    └── 03_리서치_방법론_한계점.md
```

---

## Part 1. 기본 리서치

| # | 문서명 | 설명 |
|---|--------|------|
| 01 | MES 개요 및 핵심기능 | MES 정의, ISA-95 표준, MESA 11대 기능, ERP/SCADA/PLM 비교, 최신 트렌드 |
| 02 | MES 시장규모 | 글로벌·국내 시장 규모(2023-2030), CAGR, 산업별·지역별·배포유형별 분석 |
| 03 | 경쟁사 분석 및 시장점유율 | 글로벌·국내 주요 MES 벤더, 시장 점유율, Gartner/IDC 평가 |
| 04 | 경쟁사 솔루션 기능 비교 | 벤더별 솔루션 요약 비교 매트릭스, 산업별·전략별 추천 가이드 |

---

## Part 2. 세부 기능 심층 비교 (11개 기능 영역)

| # | 문서명 | 비교 대상 |
|---|--------|----------|
| 05 | Siemens / Rockwell / SAP 심층비교 | Opcenter, Plex MES, SAP DMC |
| 06 | Dassault / Honeywell / GE 심층비교 | DELMIA Apriso, MXP, Proficy |
| 07 | AVEVA / Oracle / Aegis / Critical + 한국벤더 | 4개 글로벌 + 미라콤/포스코DX/삼성SDS/SK AX/LG CNS |

**비교 영역**: 스케줄링/APS, 작업지시, 품질(SPC/CAPA), 추적성, 설비관리, 데이터수집, 리포팅/AI, 재고/WMS, 레시피/BOM, 규정준수, 아키텍처

---

## Part 3. 경영학적 프레임워크 분석

### 08. 전략적 시장 지위 및 구조 분석 (Strategic Context)

| 프레임워크 | 분석 내용 |
|-----------|---------|
| **Porter's Five Forces** | 산업 경쟁 강도(높음), 신규 진입자 위협(중~높음), 대체재 위협(중간), 공급자 교섭력(중간), 구매자 교섭력(중~높음) |
| **BCG Matrix** | Star(Siemens Opcenter, Rockwell Plex), Cash Cow(SAP ME/MII, 한국벤더 국내사업), Question Mark(Tulip, Critical Mfg), Dog(일부 니치 온프레미스 MES) |
| **SWOT 분석** | Siemens/Rockwell/SAP/Dassault/한국벤더 5개 벤더별 S-W-O-T 교차 전략 도출 |

### 09. 내부 역량 및 운영 효율성 진단 (Capability & Operation)

| 프레임워크 | 분석 내용 |
|-----------|---------|
| **VRIO 프레임워크** | 6개 벤더(Siemens/Rockwell/SAP/Dassault/삼성SDS/미라콤) 핵심 자원 V-R-I-O 평가, 지속 가능한 경쟁 우위(SCA) 요소 도출 |
| **가치사슬 분석** | MES 산업 9개 활동 정의, Siemens(포괄적 차별화)/Rockwell(클라우드 비용 우위)/SAP(ERP 레버리지) 가치 창출 패턴 비교 |
| **McKinsey 7S 모델** | Siemens vs Rockwell 7개 요소 비교, 정합성 원천(Siemens=공유가치 중심, Rockwell=전략-시스템 중심) 분석 |

### 10. 고객 가치 및 제품 차별화 분석 (Product Value)

| 프레임워크 | 분석 내용 |
|-----------|---------|
| **전략 캔버스** | 14개 경쟁 요소 × 6개 벤더 가치 곡선 비교, 6개 블루오션 기회 식별 |
| **카노 모델** | MES 기능을 5개 범주(당연적/일원적/매력적/무관심/역)로 분류, 벤더별 Wow Point 식별 |
| **JTBD 분석** | 핵심/관련/감정적/소비체인 Job 정의, 미충족 니즈 우선순위화 (AI 품질예측, 도입실패 리스크 해소) |
| **포지셔닝 맵** | 3종 맵(가격×기능, 배포×특화, 편의성×확장성)으로 White Space 식별 |

### 11. 실행 전략 및 기술 인텔리전스 (Execution & Intelligence)

| 프레임워크 | 분석 내용 |
|-----------|---------|
| **마케팅 믹스 7P** | 5개 벤더 Product/Price/Place/Promotion/People/Process/Physical Evidence 비교 |
| **특허 맵** | Siemens 55,000+ 특허(압도적), 기술 영역별 분포, R&D 방향 예측 |
| **벤치마킹** | 성과(OEE +8~15%, 불량률 -20~30%), 프로세스(구현 4주~18개월), 전략(M&A/R&D/클라우드), 기능(산업별 성과) 4차원 비교 |

---

## 적용된 분석 프레임워크 전체 목록

| 구분 | 프레임워크 | 문서 |
|------|-----------|------|
| 전략 | Porter's Five Forces | 08 |
| 전략 | BCG Matrix | 08 |
| 전략 | SWOT 분석 | 08 |
| 역량 | VRIO 프레임워크 | 09 |
| 역량 | 가치사슬(Value Chain) 분석 | 09 |
| 역량 | McKinsey 7S 모델 | 09 |
| 고객 | 전략 캔버스 (Blue Ocean) | 10 |
| 고객 | 카노 모델 (Kano Model) | 10 |
| 고객 | JTBD (Jobs-to-be-Done) | 10 |
| 고객 | 포지셔닝 맵 (Perceptual Map) | 10 |
| 실행 | 마케팅 믹스 (7P) | 11 |
| 실행 | 특허 맵 (Patent Map) | 11 |
| 실행 | 벤치마킹 (Benchmarking) | 11 |

---

## Part 4. 한계점 분석 (현재 MES vs 업계 표준)

> `limitations/` 디렉토리에서 현재 개발 중인 DEXWEAVER MES의 한계점을 업계 표준 및 경쟁사와 비교 분석합니다.

| # | 문서명 | 분석 내용 |
|---|--------|----------|
| 00 | **종합 한계점 요약** | 전체 분석 결과 취합, TOP 10 시급 문제, 3단계 개선 로드맵, 차별화 전략 제안 |
| 01 | 기능 갭 분석 (MESA-11) | MESA-11 기능별 현재 구현 수준 vs 업계 표준 비교, 종합 41.4/100점, 코드 레벨 문제점 |
| 02 | 아키텍처 한계점 분석 | 10개 영역별 아키텍처 성숙도 평가, 종합 1.6/5.0점, 구체적 코드/설계 개선안 |
| 03 | 리서치 방법론 한계점 | 기존 리서치 자료(01~11)의 데이터 출처/프레임워크/분석 방법론 신뢰도 자기 평가 |

### 핵심 발견

- **MESA-11 기능 충족도**: 41.4/100 (업계 평균 75~85)
- **아키텍처 성숙도**: 1.6/5.0 (경쟁사 평균 4.2)
- **가장 시급한 3가지**: OEE 자동 계산, SPC 관리도, 프론트엔드 모듈화
- **차별화 전략**: AI 네이티브 통합 + 클라우드 네이티브를 강점으로 "AI-First 경량 MES" 포지셔닝

---

## 참고사항

- 조사 기준일: 2026년 3월
- 주요 출처: Gartner, IDC MarketScape, Mordor Intelligence, Grand View Research, MarketsandMarkets, Fortune Business Insights, SelectHub, Nucleus Research, 각 벤더 공식 사이트, 특허 DB
- 이 자료는 기획 단계의 참고 자료이며, 의사결정 시 최신 데이터로 업데이트가 필요합니다
