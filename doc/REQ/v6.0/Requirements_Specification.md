# DEXWEAVER MES v6.0 — 요구사항 정의서

> **버전**: v6.0 (v4.0 대비 기능 41건 + 비기능 20건 추가, 총 95건)
> **작성 근거**: 한계점 분석 + 경쟁사/국제표준 갭 분석
> **작성일**: 2026-03-03 (갭 분석 반영)
>
> **기능 요구사항 (REQ)**
> - Phase 1 (REQ-035~039): 핵심 기능 보완 — 3개월 내 구현
> - Phase 2 (REQ-040~044): 고급 기능 추가 — 6개월 내 구현
> - Phase 3 (REQ-045~051): 엔터프라이즈 전환 — 12개월 내 구현
> - Phase 1+ (REQ-052~058): 경쟁사/표준 갭 보완 Must-Have — 3~6개월
> - Phase 2+ (REQ-059~070): 경쟁사/표준 갭 보완 Should-Have — 6~9개월
> - Phase 3+ (REQ-071~075): 경쟁사/표준 갭 보완 Nice-to-Have — 9~12개월
>
> **비기능 요구사항 (NFR)**
> - NFR-001~005: 아키텍처 개선 — Phase 1 (3개월)
> - NFR-006~010: 운영 품질 강화 — Phase 2 (6개월)
> - NFR-011~014: 보안/준수 강화 — Phase 1+ (3~6개월)
> - NFR-015~018: 고급 인프라/준수 — Phase 2+ (6~9개월)
> - NFR-019~020: 엔터프라이즈 준수 — Phase 3+ (9~12개월)
>
> **참고 문서**: [갭 분석 보고서](Gap_Analysis_Report.md) | [인프라 요구사항](Infrastructure_Requirements.md) | [더미데이터 전략](TestData_Generation_Strategy.md)

---

## 기존 요구사항 (v4.0, REQ-001 ~ REQ-034)

| 요구사항ID |   모듈   |      기능명      |                      상세설명                      |                               입력항목                               |                     출력항목                    |      화면유형      | 우선순위 |
|:----------:|:--------:|:----------------:|:--------------------------------------------------:|:--------------------------------------------------------------------:|:-----------------------------------------------:|:------------------:|:--------:|
|   REQ-001  |  시스템  | 로그인           | 사용자 ID/PW로 로그인, JWT 토큰 발급               | user_id, password                                                    | access_token, user_info                         |         폼         |    상    |
|   REQ-002  |  시스템  | 회원가입         | 신규 사용자 계정 생성                              | user_id, password, name, email, role                                 | 가입완료 메시지                                 |         폼         |    상    |
|   REQ-003  |  시스템  | 권한관리         | 사용자별 메뉴 접근권한 설정 (관리자/작업자/조회자) | user_id, role, menu_permissions[]                                    | 권한설정 결과                                   |   테이블+체크박스  |    중    |
|   REQ-004  | 기준정보 | 품목등록         | 품목코드 자동생성, 품목정보 입력 후 DB저장         | item_name, category, unit, spec, safety_stock                        | item_code(자동), 등록결과                       |         폼         |    상    |
|   REQ-005  | 기준정보 | 품목목록조회     | 품목코드/명으로 검색, 페이징 처리된 목록 표시      | search_keyword, page, page_size                                      | 품목 리스트(코드,명,규격,단위,재고)             |       테이블       |    상    |
|   REQ-006  | 기준정보 | 품목수정/삭제    | 기존 품목정보 수정 또는 삭제(사용여부 N처리)       | item_code, 수정할 필드들                                             | 수정/삭제 결과                                  |         폼         |    중    |
|   REQ-007  | 기준정보 | BOM등록          | 완제품-반제품-원자재 계층구조 등록                 | parent_item, child_item, qty_per_unit, loss_rate                     | bom_id, 등록결과                                |       트리+폼      |    상    |
|   REQ-008  | 기준정보 | BOM조회          | 품목 선택시 BOM 트리구조로 전개하여 표시           | item_code                                                            | BOM 트리(레벨별 소요량 계산)                    |       트리뷰       |    상    |
|   REQ-009  | 기준정보 | 공정등록         | 공정코드/명/표준작업시간/작업설명 등록             | process_name, std_time_min, description, equipment_id                | process_code(자동), 등록결과                    |         폼         |    상    |
|   REQ-010  | 기준정보 | 라우팅등록       | 품목별 공정순서 및 각 공정 소요시간 설정           | item_code, process_list[{seq, process_code, cycle_time}]             | routing_id, 등록결과                            | 테이블(순서드래그) |    상    |
|   REQ-011  | 기준정보 | 설비등록         | 설비코드/명/공정/용량 등록                         | equip_name, process_code, capacity_per_hour, install_date            | equip_code(자동), 등록결과                      |         폼         |    중    |
|   REQ-012  | 기준정보 | 설비현황조회     | 설비별 상태(가동/정지/고장) 및 가동률 표시         | 조회조건(기간,설비)                                                  | 설비목록+상태+가동률(%)                         |   테이블+상태뱃지  |    중    |
|   REQ-013  | 생산계획 | 생산계획등록     | 품목/수량/납기일 입력하여 생산계획 생성            | item_code, plan_qty, due_date, priority                              | plan_id, 계획등록결과                           |         폼         |    상    |
|   REQ-014  | 생산계획 | 생산계획목록     | 기간별 생산계획 조회, 상태별 필터링                | start_date, end_date, status                                         | 계획목록(품목,수량,납기,상태,진척률)            |       테이블       |    상    |
|   REQ-015  | 생산계획 | AI수요예측       | 과거 12개월 출하데이터로 향후 3개월 수요 예측      | item_code, history_months                                            | 월별 예측수량, 신뢰구간, 예측그래프             |     차트+테이블    |    상    |
|   REQ-016  | 생산계획 | AI일정최적화     | 납기/설비용량 고려하여 최적 생산순서 자동산출      | plan_ids[], constraints{due_date, capacity}                          | 최적화된 작업순서, 예상완료일, 설비배정         |      간트차트      |    상    |
|   REQ-017  | 생산실행 | 작업지시생성     | 생산계획 기반 일별 작업지시서 자동생성             | plan_id, work_date, line_id                                          | work_order_id, 작업지시서(품목,수량,공정,설비)  |      폼+프린트     |    상    |
|   REQ-018  | 생산실행 | 작업지시목록     | 일자별 작업지시 현황 조회                          | work_date, line_id, status                                           | 작업지시목록(지시번호,품목,수량,상태)           |       테이블       |    상    |
|   REQ-019  | 생산실행 | 작업실적등록     | 작업자가 생산수량/불량수량/작업시간 입력           | work_order_id, good_qty, defect_qty, worker_id, start_time, end_time | 실적등록결과, 진척률 업데이트                   |         폼         |    상    |
|   REQ-020  | 생산실행 | 생산현황대시보드 | 실시간 라인별 생산현황, 목표대비 달성률 표시       | (실시간)                                                             | 라인별 현황카드, 달성률게이지, 시간대별차트     |      대시보드      |    상    |
|   REQ-021  |   품질   | 검사기준등록     | 품목별 검사항목/기준값/허용범위 설정               | item_code, check_items[{name, std_value, min, max, unit}]            | 검사기준ID, 등록결과                            |      테이블폼      |    중    |
|   REQ-022  |   품질   | 품질검사등록     | 입고/공정/출하 검사결과 입력, 자동 합부판정        | inspection_type, item_code, lot_no, measured_values[]                | 합격/불합격 판정, 검사성적서                    |     폼+결과표시    |    중    |
|   REQ-023  |   품질   | 불량현황조회     | 기간/품목/불량유형별 불량 현황 분석                | start_date, end_date, item_code                                      | 불량유형별 집계, 파레토차트                     |     차트+테이블    |    중    |
|   REQ-024  |   품질   | AI불량예측       | 공정 파라미터로 불량 발생 확률 실시간 예측         | process_params{temp, pressure, speed, humidity}                      | 불량확률(%), 주요원인 Top3, 권장조치            |     게이지+알림    |    상    |
|   REQ-025  |   재고   | 입고등록         | 자재/부품 입고 처리, 로트번호 자동생성             | item_code, qty, supplier, warehouse, location                        | lot_no(자동), 입고전표번호                      |         폼         |    상    |
|   REQ-026  |   재고   | 출고등록         | 생산투입 또는 출하를 위한 출고 처리(FIFO)          | item_code, qty, out_type, work_order_id                              | 출고전표번호, 차감된 로트정보                   |         폼         |    상    |
|   REQ-027  |   재고   | 재고현황조회     | 품목별 현재고/가용재고/안전재고 비교 표시          | warehouse, category                                                  | 품목별 재고현황, 안전재고미달 알림              |   테이블+경고표시  |    상    |
|   REQ-028  |   재고   | 재고이동         | 창고간/위치간 재고 이동 처리                       | item_code, qty, from_location, to_location                           | 이동전표번호                                    |         폼         |    중    |
|   REQ-029  |   설비   | 설비상태등록     | 설비별 가동/정지/고장 상태 변경 기록               | equip_code, status, reason, worker_id                                | 상태변경이력 저장                               |     폼+상태버튼    |    중    |
|   REQ-030  |   설비   | 설비가동현황     | 전체 설비 실시간 상태 모니터링                     | (실시간)                                                             | 설비배치도+상태, 가동률                         | 대시보드(레이아웃) |    중    |
|   REQ-031  |   설비   | AI고장예측       | 센서데이터(진동,온도) 분석하여 고장 예측           | equip_code, sensor_data{vibration, temperature, current}             | 고장확률(%), 예상잔여수명, 정비권고             |  게이지+트렌드차트 |    상    |
|   REQ-032  |   통계   | 생산실적분석     | 기간별/품목별/라인별 생산실적 집계 및 차트         | start_date, end_date, group_by                                       | 생산량추이, 달성률, 비교차트                    |     차트+테이블    |    중    |
|   REQ-033  |   통계   | 품질분석리포트   | 불량률 추이, 공정능력지수(Cpk) 분석                | start_date, end_date, item_code                                      | 불량률차트, Cpk값, 관리도                       |     차트+테이블    |    중    |
|   REQ-034  |   통계   | AI인사이트       | 생산/품질/설비 데이터 종합분석, 개선점 제안        | analysis_period, target_kpi                                          | AI분석리포트(현황요약,문제점,개선제안,예상효과) |      리포트뷰      |    중    |

---

## 신규 요구사항 — Phase 1: 핵심 기능 보완 (REQ-035 ~ REQ-039, 3개월 내 구현)

| 요구사항ID |   모듈   |        기능명       |                                        상세설명                                       |                                       입력항목                                      |                              출력항목                             |       화면유형      | 우선순위 |
|:----------:|:--------:|:-------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:-----------------------------------------------------------------:|:-------------------:|:--------:|
|   REQ-035  |   품질   | SPC 관리도          | X-bar/R차트 자동 생성, Cp/Cpk 자동 계산, 관리 한계선(UCL/LCL) 자동 설정, 이상 경보 발생 | item_code, process_code, check_item, measured_values[], subgroup_size               | X-bar/R차트, Cp/Cpk값, UCL/LCL, 이상패턴 경보                    |   차트+경보알림     |    상    |
|   REQ-036  |   품질   | CAPA 프로세스       | 시정조치(CA)/예방조치(PA) 등록, 워크플로우(발생→원인분석→조치→검증→완료) 관리, 이력 추적 | capa_type(CA/PA), issue_description, root_cause, action_plan, due_date, responsible | capa_id, 워크플로우 상태, 조치이력, 완료보고서                    | 폼+워크플로우차트   |    상    |
|   REQ-037  |   설비   | OEE 자동 계산       | 가용률x성능률x품질률 자동 계산, 설비별/라인별/기간별 OEE 대시보드, 6대 로스 분석        | equip_code, line_id, start_date, end_date                                           | OEE(%), 가용률/성능률/품질률(%), 6대로스 내역, 추이차트           | 대시보드+차트       |    상    |
|   REQ-038  |  시스템  | 실시간 알림         | WebSocket 기반 실시간 알림 (설비 고장, 품질 이상, 재고 부족, AI 경고), 알림 구독 설정    | user_id, subscribe_topics[], alert_rules{threshold, condition}                      | 실시간 알림팝업, 알림이력목록, 미확인건수 뱃지                    | 알림팝업+알림센터   |    상    |
|   REQ-039  |   재고   | LOT 추적 강화       | Forward/Backward 추적, 시각적 계보도(Genealogy Tree), 리콜 시뮬레이션                   | lot_no, trace_direction(forward/backward), recall_scope                             | LOT 계보도(트리), 영향범위 목록, 리콜 시뮬레이션 결과             | 트리뷰+시뮬레이션   |    상    |

---

## 신규 요구사항 — Phase 2: 고급 기능 추가 (REQ-040 ~ REQ-044, 6개월 내 구현)

| 요구사항ID |   모듈   |        기능명       |                                        상세설명                                       |                                       입력항목                                      |                              출력항목                             |       화면유형      | 우선순위 |
|:----------:|:--------:|:-------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:-----------------------------------------------------------------:|:-------------------:|:--------:|
|   REQ-040  |   설비   | CMMS 유지보수       | 예방보전(PM) 일정관리, 정비 작업지시, 정비 이력/비용 관리, 예비부품 재고 관리            | equip_code, pm_schedule{cycle, task_list}, work_type, parts_used[], cost            | 정비일정(캘린더), 작업지시서, 정비이력, 비용집계                  | 캘린더+폼+테이블    |    중    |
|   REQ-041  |   공정   | 레시피 관리         | ISA-88 기반 레시피 마스터 등록, 레시피 버전 관리, 공정 파라미터 설정값/실적값 비교 관리  | recipe_name, item_code, version, parameters[{name, set_value, unit, tolerance}]     | recipe_id, 버전이력, 설정값vs실적값 비교차트                      | 폼+버전비교뷰       |    중    |
|   REQ-042  |  데이터  | MQTT 데이터 수집    | MQTT 브로커 연동, 설비 센서 데이터 자동 수집, 수집 주기/토픽 설정, 수집 상태 모니터링    | broker_url, topic_list[], equip_mapping{topic, equip_code, tag}, collect_interval   | 수집현황 대시보드, 수집이력, 연결상태, 데이터 미수신 경보         | 대시보드+설정폼     |    중    |
|   REQ-043  |  시스템  | 문서 관리(DMS)      | 작업지시서/검사성적서/SOP 문서 등록/조회/버전관리, PDF 출력, 문서 승인 워크플로우        | doc_type, title, file, version, approval_line[], related_id                         | doc_id, 버전이력, 승인상태, PDF 다운로드                          | 테이블+뷰어+폼      |    중    |
|   REQ-044  | 생산실행 | 노동 관리           | 작업자 스킬 매트릭스 관리, 근태 연동, 공정별 작업자 배정 최적화, 교육 이력 관리          | worker_id, skills[{process_code, level}], attendance, training_records[]            | 스킬매트릭스표, 작업자배정현황, 교육이력, 근태현황                | 매트릭스+테이블+폼  |    중    |

---

## 신규 요구사항 — Phase 3: 엔터프라이즈 전환 (REQ-045 ~ REQ-049, 12개월 내 구현)

| 요구사항ID |   모듈   |        기능명       |                                        상세설명                                       |                                       입력항목                                      |                              출력항목                             |       화면유형      | 우선순위 |
|:----------:|:--------:|:-------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:-----------------------------------------------------------------:|:-------------------:|:--------:|
|   REQ-045  |  시스템  | ERP 연동            | SAP/Oracle 등 ERP 시스템과 데이터 연동 인터페이스 (주문, 재고, BOM 동기화)               | erp_type, connection_config, sync_targets[{entity, direction, schedule}]            | 연동상태 대시보드, 동기화 이력, 오류 로그, 데이터 매핑현황        | 대시보드+설정폼     |    하    |
|   REQ-046  |  데이터  | OPC-UA 연동         | OPC-UA 서버 연결, 설비 태그 매핑, 실시간 데이터 구독, 연결 상태 모니터링                 | opcua_server_url, node_list[], tag_mapping{node_id, equip_code, param}, subscribe  | 연결상태, 실시간 태그값, 수집이력, 통신 오류 경보                 | 대시보드+설정폼     |    하    |
|   REQ-047  |  시스템  | 다국어 지원         | i18n 프레임워크 적용, 한국어/영어 전환, 언어팩 관리                                     | locale(ko/en), translation_keys[]                                                  | 전환된 UI 텍스트, 언어팩 관리화면                                 | 설정폼+전체UI반영   |    하    |
|   REQ-048  | 모니터링 | 디지털 트윈         | 공장 3D 모델 연계, 실시간 설비 상태 시각화, 이상 설비 하이라이트, 클릭시 상세정보 표시   | factory_model_file, equip_positions[], real_time_data                               | 3D 공장뷰, 설비상태 오버레이, 이상 하이라이트, 상세팝업           | 3D뷰어+대시보드     |    하    |
|   REQ-049  |  시스템  | 감사 추적           | 모든 데이터 변경 이력 자동 기록, 21 CFR Part 11 대응, 전자서명, 변경사유 입력 필수       | (자동수집) user_id, action, entity, before_value, after_value, reason, e_signature  | 감사추적 로그 목록, 변경이력 상세, 기간별 감사리포트              | 테이블+상세뷰       |    하    |
|   REQ-050  | 생산계획 | 스케줄링 고도화     | 다목적 최적화(납기+비용+셋업), 실시간 리스케줄링(설비고장/긴급주문 시), What-If 시뮬레이션 | plan_ids[], objectives[{type, weight}], constraints[], disruption_event             | 최적 스케줄(다목적), 리스케줄 결과, 시뮬레이션 비교               | 간트차트+시뮬레이션 |    중    |
|   REQ-051  | 기준정보 | 자원 통합 관리      | 설비/작업자/금형/치공구/측정기를 통합 자원 풀로 관리, 자원-공정 M:N 매핑, 자원 가용성 캘린더 | resource_type, resource_code, capabilities[], calendar[], auto_assign_rules        | 통합 자원 현황, 자원 가용성 간트, 자동배정 결과                   | 대시보드+캘린더     |    중    |

---

## 비기능 요구사항 — Phase 1: 아키텍처 개선 (NFR-001 ~ NFR-005, 3개월 내 구현)

> **근거**: 아키텍처 성숙도 1.6/5.0 → 한계점 분석 TOP 10 중 #6~#10 대응

| 요구사항ID |     영역     |          항목          |                                           상세설명                                          |                         현재 상태                        |                        목표 상태                       | 우선순위 |
|:----------:|:------------:|:----------------------:|:-------------------------------------------------------------------------------------------:|:--------------------------------------------------------:|:------------------------------------------------------:|:--------:|
|  NFR-001   | 프론트엔드   | 컴포넌트 모듈화        | App.jsx(2,851줄) → 14개 페이지 컴포넌트 분리, React Router 도입, Lazy Loading, API 서비스 레이어 분리 | 단일 파일 God Component, 자체 라우팅, 인라인 API 호출    | 페이지별 컴포넌트, URL 기반 라우팅, 서비스 레이어 분리 |    상    |
|  NFR-002   | 인프라/배포  | Docker 이미지 빌드     | ConfigMap 소스 마운트 + pip install 제거, 멀티스테이지 Dockerfile, 이미지 레지스트리 관리     | 매 부팅시 pip install, ConfigMap 배포, replicas:1         | 이미지 빌드 배포, HPA 오토스케일링, 롤링 업데이트      |    상    |
|  NFR-003   | AI/ML        | 모델 캐싱/버전관리     | Prophet/XGBoost/IsolationForest 학습 모델 저장/재사용, 모델 버전관리, 재학습 주기 설정        | 매 API 요청시 재학습 (Prophet ~5초, XGBoost ~2초)        | 모델 캐싱 (응답 <200ms), 일/주 단위 자동 재학습       |    상    |
|  NFR-004   | 백엔드       | 인증 미들웨어 통합     | 43개 엔드포인트의 JWT 검증 보일러플레이트 제거, FastAPI Depends 기반 미들웨어로 통합           | 동일 인증 패턴 43회 반복, 수동 토큰 파싱                 | Depends(get_current_user) 단일 미들웨어                |    중    |
|  NFR-005   | 데이터베이스 | 마이그레이션 도구 도입 | Alembic 기반 스키마 버전관리, 마이그레이션 자동화, 롤백 지원                                  | init.sql 수동 관리, 스키마 변경 이력 없음                | Alembic 마이그레이션, CI/CD 연동 자동 적용             |    중    |

---

## 비기능 요구사항 — Phase 2: 운영 품질 강화 (NFR-006 ~ NFR-010, 6개월 내 구현)

| 요구사항ID |     영역     |          항목          |                                           상세설명                                          |                         현재 상태                        |                        목표 상태                       | 우선순위 |
|:----------:|:------------:|:----------------------:|:-------------------------------------------------------------------------------------------:|:--------------------------------------------------------:|:------------------------------------------------------:|:--------:|
|  NFR-006   | 데이터베이스 | 비동기 DB 드라이버     | psycopg2(동기) → asyncpg(비동기) 전환, 커넥션 풀링 최적화                                    | 동기 드라이버, FastAPI async와 불일치                    | asyncpg + 커넥션 풀(min:5, max:20)                     |    중    |
|  NFR-007   | 보안         | 보안 강화              | Rate Limiting (API별), JWT Secret 환경변수 관리, CORS 엄격화, SQL Injection 방어(Pydantic)    | Rate Limit 없음, JWT Secret 코드 내 하드코딩             | slowapi Rate Limit, 환경변수 Secret, Pydantic 검증     |    상    |
|  NFR-008   | 테스트       | 테스트 자동화          | pytest 기반 비즈니스 로직 단위테스트, API 통합테스트, 프론트엔드 컴포넌트 테스트               | 비즈니스 로직 테스트 0건, 프론트 테스트 0건               | 커버리지 70%+, CI/CD 연동 자동 실행                    |    중    |
|  NFR-009   | 성능         | 캐싱 레이어            | Redis 기반 API 응답 캐싱, 세션 캐싱, 자주 조회되는 마스터 데이터 캐싱                        | 캐싱 없음, 모든 요청 DB 직접 조회                        | Redis 캐싱, TTL 전략, 캐시 무효화 정책                 |    중    |
|  NFR-010   | 백엔드       | Router 모듈 분리       | app.py(728줄, 46개 엔드포인트) → 도메인별 APIRouter 분리, Pydantic 스키마 적용                | 단일 app.py에 모든 라우트, dict 기반 응답                | 도메인별 Router (auth, items, plans, quality, ...)     |    중    |

---

## 경쟁사/국제표준 갭 분석 기반 추가 요구사항

> **근거**: [갭 분석 보고서](Gap_Analysis_Report.md)
> **분석 대상**: ISA-95, ISA-88, FDA 21 CFR Part 11, IEC 62443, ISO 22400, ISO 9001/IATF 16949
> **비교 경쟁사**: Siemens Opcenter, Rockwell Plex, SAP DMC, Critical Manufacturing, MPDV HYDRA
> **추가 건수**: 기능 24건(REQ-052~075) + 비기능 10건(NFR-011~020) = **34건**

---

## 기능 요구사항 — Phase 1+: 경쟁사 필수 기능 보완 (REQ-052 ~ REQ-058, 3~6개월)

> **근거**: 전 경쟁사 기본 제공 기능 + ISO 9001/22400 필수 항목

| 요구사항ID |   모듈   |        기능명       |                                        상세설명                                       |                                       입력항목                                      |                              출력항목                             |       화면유형      | 우선순위 | 표준/경쟁사 근거 |
|:----------:|:--------:|:-------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:-----------------------------------------------------------------:|:-------------------:|:--------:|:----------------:|
|   REQ-052  |  시스템  | 바코드/QR/RFID 지원  | GS1-128/QR/DataMatrix 바코드 생성/인쇄, 스캐너 연동 API, RFID 미들웨어, LOT/시리얼/자재/설비 자동 인식, 작업 시작/완료/이동 스캔 기록 | barcode_type, entity_type(LOT/SERIAL/ITEM/EQUIP), entity_id, scanner_input          | 바코드 이미지, 스캔 이벤트 기록, 매핑 결과                        | 설정폼+스캔뷰어     |    상    | GS1, 전 경쟁사 |
|   REQ-053  | 생산실행 | 전자 작업지시서(e-WI) | 공정 단계별 작업 가이드(Step-by-Step), 이미지/동영상/PDF/CAD 첨부 및 인라인 뷰어, 단계별 체크포인트 작업자 서명, SOP 자동 연결, 열람 이력 기록 | wo_id, process_code, steps[{seq, instruction, media[], checkpoint, sign_required}]   | 전자 작업지시서 뷰, 단계별 완료 기록, 서명 이력                   | 스텝뷰어+서명폼     |    상    | Siemens/Rockwell/SAP, 21 CFR Part 11 |
|   REQ-054  |   품질   | 부적합품 관리(NCR)    | 부적합 발생 등록(자동/수동), 즉시 격리(Quarantine) 처리, MRB 심의 워크플로우(사용/재작업/폐기/특채 결정), 부적합 이력 통계, CAPA(REQ-036) 자동 연계 | ncr_type, item_code, lot_no, defect_description, qty, disposition_decision           | ncr_id, 격리 처리 결과, MRB 판정, CAPA 연결 결과                  | 폼+워크플로우       |    상    | ISO 9001 8.7, Rockwell Plex |
|   REQ-055  |   품질   | SPC 자동격리조치      | SPC 위반 시: 해당 LOT 자동 보류, 설비 자동 정지, CAPA 자동 트리거, 품질 엔지니어 알림. 위반 유형별 조치 규칙 설정 | violation_id, action_rules[{violation_type, auto_actions[]}]                         | 자동 격리 결과, 설비 상태 변경, CAPA 자동 생성, 알림 발송         | 규칙설정폼+알림     |    상    | Critical Manufacturing |
|   REQ-056  |   품질   | 제품출하판정          | 자재 상태 모델(AVAILABLE/HOLD/QUARANTINE/REJECTED), MRB 판정(사용/재작업/폐기/반품), 판정 이력 감사추적 | lot_no, disposition(USE_AS_IS/REWORK/SCRAP/RETURN), reviewer_ids[], reason           | 판정 결과, 상태 변경 이력, 감사 로그                              | 폼+워크플로우       |    상    | ISO 9001 8.6, FDA 21 CFR Part 820 |
|   REQ-057  |   KPI   | FPY 자동계산          | 공정단계별/품목별/라인별 FPY = (1차 양품수/투입수) 자동 계산, Rolled Throughput Yield(RTY) 전공정 산출, FPY 추이 분석 및 목표 관리 | item_code, process_code, start_date, end_date, target_fpy                            | FPY(%), RTY(%), 추이차트, 목표대비현황                            | 차트+테이블         |    상    | ISO 22400, Six Sigma |
|   REQ-058  |   설비   | 설비보전 KPI 자동계산  | equip_status_log + CMMS 데이터 기반: MTTF, MTTR, MTBF, PM 준수율(%), 시정보전/예방보전 비율 자동 계산 | equip_code, start_date, end_date                                                    | MTTF/MTTR/MTBF(시간), PM준수율(%), CM/PM비율, 추이차트            | 대시보드+차트       |    상    | ISO 22400, 전 경쟁사 CMMS |

---

## 기능 요구사항 — Phase 2+: 표준 준수 강화 (REQ-059 ~ REQ-070, 6~9개월)

| 요구사항ID |   모듈   |        기능명       |                                        상세설명                                       |                                       입력항목                                      |                              출력항목                             |       화면유형      | 우선순위 | 표준/경쟁사 근거 |
|:----------:|:--------:|:-------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:-----------------------------------------------------------------:|:-------------------:|:--------:|:----------------:|
|   REQ-059  |   품질   | MSA/Gage R&R        | Gage R&R 연구 관리(반복성/재현성), Type 1 연구, Bias/Linearity/Stability 분석, AIAG MSA 4th edition | study_type, gage_id, operators[], parts[], measurements[][]                          | %GRR, %EV, %AV, ndc, 판정(PASS/MARGINAL/FAIL), 차트              | 분석폼+차트         |    중    | IATF 16949 9.1.1.2 |
|   REQ-060  |   품질   | SPC 속성관리도        | p-chart(불량률), np-chart(불량수), c-chart(결점수), u-chart(단위당결점수). REQ-035 확장 | item_code, chart_type(P/NP/C/U), sample_data[]                                     | 관리도(UCL/LCL/CL), 위반 포인트, 추이 분석                       | 차트+경보알림       |    중    | ISO 7870-2, Siemens |
|   REQ-061  |   품질   | FMEA 관리            | PFMEA 등록/관리: 고장모드, 영향, 원인, S/O/D 점수, RPN 자동계산, 권장조치, 이행추적 | process_code, failure_modes[{mode, effect, cause, severity, occurrence, detection}]  | RPN 순위표, 권장조치목록, 이행현황                                | 테이블+폼           |    중    | IATF 16949 |
|   REQ-062  |   KPI   | ISO 22400 KPI 라이브러리 | Throughput Rate, Production Lead Time, Cycle Time, Setup Time, Worker Efficiency, Inventory Turns, Scrap/Rework Ratio 자동계산 + 벤치마킹 | kpi_type, target, period, group_by(equip/line/item)                                 | KPI 값, 목표대비현황, 기간별추이, 벤치마크비교                    | 대시보드+차트       |    중    | ISO 22400 |
|   REQ-063  |  시스템  | 에너지 관리           | 설비별/라인별/제품별 에너지 소비량 모니터링, 에너지 KPI(kWh/unit) 자동계산, 에너지 비용 분석, 피크 수요 알림 | equip_code, energy_type(ELEC/GAS/WATER), meter_reading, unit_cost                   | 에너지 소비현황, kWh/unit, 비용분석, 피크알림                     | 대시보드+차트       |    중    | ISO 50001, ESG |
|   REQ-064  |   설비   | 교정 관리             | 측정기/계측기별 교정 주기 관리, 교정 실행/성적서 관리, 만료 시 사용 자동 차단, 교정↔검사 연계 | gage_id, cal_schedule, cal_results[], certificate                                   | 교정일정(캘린더), 교정이력, 만료알림, 차단현황                    | 캘린더+폼+테이블    |    중    | ISO 9001 7.1.5, ISO/IEC 17025 |
|   REQ-065  |   품질   | 공급업체 품질 관리(SQM) | 공급업체별 품질(입고 불량률)/납기 실적 자동 집계, 스코어카드, SCAR 워크플로우, ASL 관리 | supplier_id, eval_period, scoring_criteria[]                                         | 공급업체 스코어카드, 실적추이, SCAR현황, ASL목록                  | 테이블+차트+폼      |    중    | ISO 9001 8.4, IATF 16949 |
|   REQ-066  | 생산실행 | 자동디스패칭/자재역산  | 스케줄링(REQ-050) 결과→작업지시 자동 생성, 작업 완료 시 BOM 기반 자재 소비 자동 역산(Backflush) | schedule_result_id, auto_dispatch_rules, backflush_config                            | 자동 생성된 작업지시, 자재 소비 전표                              | 설정폼+자동처리     |    중    | ISA-95, Siemens/SAP |
|   REQ-067  | 생산계획 | 셋업시간 매트릭스      | 제품간 전환 셋업시간 매트릭스, 순서 의존 셋업 모델링(REQ-050 연동), 계획 vs 실제 추적 | from_item, to_item, equip_code, setup_time_min                                      | 셋업시간 매트릭스표, 실적 대비 분석                               | 매트릭스테이블+차트 |    중    | ISA-95, MPDV HYDRA |
|   REQ-068  | 생산실행 | WO 원가추적           | 작업지시별 실제 원가: 노무비(시간×단가) + 자재비(실소비×단가) + 경비배부. 표준 vs 실제 차이분석 | wo_id, labor_hours, material_consumption[], overhead_rate                            | WO별 원가명세, 표준/실제 차이, 원가추이                           | 테이블+차트         |    중    | ISA-95 Performance |
|   REQ-069  |   통계   | 커스텀 대시보드 빌더   | 사용자별 위젯 드래그&드롭, KPI 게이지/차트/테이블 위젯 라이브러리, 역할별 프리셋, 공유/내보내기 | widget_type, data_source, layout[], preset_role                                     | 커스텀 대시보드 뷰, 위젯 목록, 프리셋                             | 대시보드빌더        |    중    | Rockwell/SAP/Siemens |
|   REQ-070  |   통계   | 리포트 빌더           | 사용자 정의 리포트 템플릿, 필드 배치/그룹/집계/필터/정렬, PDF/Excel/CSV Export, 정기 자동 생성/이메일 발송 | template_name, fields[], filters[], schedule                                        | 리포트 뷰, PDF/Excel/CSV 파일, 발송이력                           | 리포트디자이너      |    중    | Rockwell/SAP |

---

## 기능 요구사항 — Phase 3+: 엔터프라이즈 고급 기능 (REQ-071 ~ REQ-075, 9~12개월)

| 요구사항ID |   모듈   |        기능명       |                                        상세설명                                       |                                       입력항목                                      |                              출력항목                             |       화면유형      | 우선순위 | 표준/경쟁사 근거 |
|:----------:|:--------:|:-------------------:|:-------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------:|:-----------------------------------------------------------------:|:-------------------:|:--------:|:----------------:|
|   REQ-071  |   공정   | 배치실행엔진          | ISA-88 Batch State Machine(Idle/Running/Held/Complete/Stopped/Aborted), Procedure→Unit Procedure→Operation→Phase 실행 계층, 배치 예외 처리 | batch_id, recipe_id, state_command(START/HOLD/RESUME/ABORT), phase_params           | 배치 상태 뷰, 실행 로그, 예외 처리 이력                           | 상태뷰+제어패널     |    하    | ISA-88, 프로세스 산업 |
|   REQ-072  |   공정   | 전자배치기록(eBR)     | 배치 실행 중 모든 활동(파라미터/자재/작업자/시간) 자동기록→eBR 생성, 검토/승인 워크플로우, PDF 출력 | batch_id, review_decision(APPROVE/REJECT), reviewer_id                              | eBR 문서, 검토 이력, PDF 출력                                     | 뷰어+승인폼         |    하    | FDA 21 CFR Part 11, ISA-88 |
|   REQ-073  |  시스템  | 설계변경관리(ECM)     | ECR→ECN→ECO 워크플로우, BOM/라우팅/레시피 변경 영향분석, 변경이력 추적, 유효일자(Effectivity Date) 관리 | ecr_title, change_type, affected_items[], impact_analysis, effectivity_date          | ECR/ECN/ECO 문서, 영향범위, 변경이력                              | 폼+워크플로우       |    하    | IATF 16949, Siemens CMII |
|   REQ-074  | 생산실행 | 복합라우팅            | 재진입(동일 설비 다회 방문), 조건 분기(IF 검사PASS THEN 다음 ELSE 재작업), 병렬(분기/합류), 재작업 루프 | item_code, routing_type(LINEAR/REENTRANT/CONDITIONAL/PARALLEL), routing_graph        | 복합 라우팅 그래프 뷰, 실행 경로 추적                             | 그래프뷰+설정폼     |    하    | Critical Mfg, ISA-88 |
|   REQ-075  |  시스템  | 멀티사이트 관리       | Enterprise→Site→Area→Line 계층(ISA-95/ISA-88), 사이트별 독립 운영 + 본사 통합 가시성, 크로스사이트 자원/재고 공유, 글로벌 KPI 통합 | site_config, org_hierarchy, shared_master_data[], cross_site_rules                  | 글로벌 대시보드, 사이트별 뷰, 통합 KPI                            | 대시보드+설정폼     |    하    | ISA-95, Siemens/DELMIA |

---

## 비기능 요구사항 — Phase 1+: 보안/준수 강화 (NFR-011 ~ NFR-014, 3~6개월)

> **근거**: IEC 62443, FDA 21 CFR Part 11, 전 경쟁사 모바일 지원

| 요구사항ID |     영역     |          항목          |                                           상세설명                                          |                         현재 상태                        |                        목표 상태                       | 우선순위 |
|:----------:|:------------:|:----------------------:|:-------------------------------------------------------------------------------------------:|:--------------------------------------------------------:|:------------------------------------------------------:|:--------:|
|  NFR-011   | UI/UX        | 모바일/태블릿 반응형 UI | 현장 작업자용 PWA 또는 반응형 인터페이스, 작업지시/실적입력/품질검사/설비상태 터치 최적화, 오프라인 캐싱 | 데스크톱 전용 UI, 모바일 미지원                          | PWA 또는 반응형, 터치 최적화, 핵심 기능 모바일 지원    |    상    |
|  NFR-012   | 보안         | 데이터 암호화          | TLS 1.3 전 API 통신 필수, AES-256 민감 데이터 저장 암호화(PII/감사로그/전자서명), DB SSL       | HTTP 평문 통신 가능, 저장 데이터 암호화 없음             | TLS 1.3 필수, AES-256 at-rest, DB SSL 연결             |    상    |
|  NFR-013   | 보안         | 보안 이벤트 로깅       | 인증실패/권한위반/의심패턴 중앙 로깅, 5회 실패→15분 잠금, 세션 타임아웃 30분, 로그 보존 ≥1년   | 보안 이벤트 로깅 없음, 계정 잠금 없음                    | 중앙 보안 로그, 계정 잠금, 세션 관리, 1년 보존         |    상    |
|  NFR-014   | 준수         | 감사추적 불변성 보장   | REQ-049 감사추적 append-only(UPDATE/DELETE 불가), Hash chain 무결성 보장, 보존 정책(품질 3년/제약 7년) | 감사추적 UPDATE/DELETE 가능, 보존 정책 없음              | append-only + hash chain, 자동 보관, 보존 기간 강제    |    상    |

---

## 비기능 요구사항 — Phase 2+: 고급 인프라/준수 (NFR-015 ~ NFR-018, 6~9개월)

| 요구사항ID |     영역     |          항목          |                                           상세설명                                          |                         현재 상태                        |                        목표 상태                       | 우선순위 |
|:----------:|:------------:|:----------------------:|:-------------------------------------------------------------------------------------------:|:--------------------------------------------------------:|:------------------------------------------------------:|:--------:|
|  NFR-015   | 보안         | 네트워크 구역 분리     | IEC 62443 Zone/Conduit: IT Zone(Frontend/API), OT Zone(MQTT/OPC-UA), DMZ, DB Zone. Cilium NetworkPolicy 적용 | 구역 분리 없음, 단일 네트워크                            | 4개 보안 구역, NetworkPolicy 강제, Zone 간 Conduit 정의 |    중    |
|  NFR-016   | 성능         | 고주파 데이터 수집     | MQTT/OPC-UA ≥10,000 points/sec, 시계열 데이터 보존/다운샘플링, 메시지 큐 버퍼링(Redis Streams/Kafka) | 수동 API 호출만, 실시간 수집 미구현                      | 10K+ points/sec, 다운샘플링, 버스트 버퍼링             |    중    |
|  NFR-017   | 준수         | 전자서명 상세규격      | FDA 21 CFR Part 11: 최소 2개 식별요소(ID+PW), 서명 표시(서명자명+일시+의미), 서명-기록 암호화 연결, 재사용/양도 불가 | 단순 e_signature 필드만, 법적 요건 미충족                | 2요소 인증, 서명 표시 규격, 암호화 연결, 법적 유효     |    중    |
|  NFR-018   | 아키텍처     | API 버전관리           | REST /api/v1/ /api/v2/, 사용중단 정책(6개월 사전고지), OpenAPI 3.0 자동생성, Breaking change 관리 | API 버전관리 없음, 단일 경로                             | v1/v2 병렬 운영, OpenAPI 자동 문서, 사용중단 정책      |    중    |

---

## 비기능 요구사항 — Phase 3+: 엔터프라이즈 준수 (NFR-019 ~ NFR-020, 9~12개월)

| 요구사항ID |     영역     |          항목          |                                           상세설명                                          |                         현재 상태                        |                        목표 상태                       | 우선순위 |
|:----------:|:------------:|:----------------------:|:-------------------------------------------------------------------------------------------:|:--------------------------------------------------------:|:------------------------------------------------------:|:--------:|
|  NFR-019   | 안정성       | 오프라인/장애 대응     | MQTT 다운(로컬 큐), ERP 미접속(트랜잭션 버퍼), Redis 다운(DB 폴백), 프론트엔드 오프라인 모드  | 외부 서비스 장애 시 전체 중단                            | Graceful Degradation, 오프라인 모드, 자동 동기화       |    하    |
|  NFR-020   | 준수         | 시스템 밸리데이션      | GAMP 5 IQ/OQ/PQ 프로토콜, 밸리데이션 실행 기록/문서 자동 생성, 요구사항→설계→코드→테스트 Traceability Matrix | 밸리데이션 절차 없음                                     | GAMP 5 IQ/OQ/PQ, Traceability Matrix 자동 생성        |    하    |

---

## 요구사항 총괄 요약

| 구분 | 기존 (v4.0→v6.0) | 갭 분석 추가 | 합계 |
|---|:---:|:---:|:---:|
| 기능 요구사항 (REQ) | 51건 (001~051) | 24건 (052~075) | **75건** |
| 비기능 요구사항 (NFR) | 10건 (001~010) | 10건 (011~020) | **20건** |
| **총합** | **61건** | **34건** | **95건** |

### 모듈별 분포

| 모듈 | REQ 수 | 범위 |
|:----:|:------:|:----:|
| 시스템 | 8 | REQ-001~003, 038, 047, 049, 052, 075 |
| 기준정보 | 10 | REQ-004~012, 051 |
| 생산계획 | 6 | REQ-013~016, 050, 067 |
| 생산실행 | 9 | REQ-017~020, 044, 053, 066, 068, 074 |
| 품질 | 14 | REQ-021~024, 035~036, 054~056, 059~061, 065 |
| 재고 | 5 | REQ-025~028, 039 |
| 설비 | 5 | REQ-029~031, 037, 040 |
| 데이터 | 2 | REQ-042, 046 |
| 통계/KPI | 8 | REQ-032~034, 057~058, 062, 069~070 |
| 공정 | 3 | REQ-041, 071~072 |
| 모니터링 | 2 | REQ-048, 063 |
| 시스템(ECM) | 1 | REQ-073 |
| 시스템(멀티사이트) | 1 | REQ-075 |
| 복합라우팅 | 1 | REQ-074 |
