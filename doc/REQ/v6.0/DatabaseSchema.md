# DEXWEAVER MES v6.0 — 데이터베이스 스키마

> **버전**: v6.0 (기존 21개 테이블 + 신규 19개 테이블, 총 40개)
> **작성 근거**: 한계점 분석 보고서 (research/limitations/)
> **작성일**: 2026-03-03
>
> | Phase | 신규 테이블 | 설명 |
> |-------|-------------|------|
> | 기존 v4.0 | 21개 | users~ai_forecasts |
> | Phase 1 | 7개 | spc_rules, spc_violations, capa, capa_actions, oee_daily, notifications, notification_settings |
> | Phase 2 | 8개 | maintenance_plans, maintenance_orders, recipes, recipe_parameters, mqtt_config, sensor_data, documents, worker_skills |
> | Phase 3 | 4개 | erp_sync_config, erp_sync_log, opcua_config, audit_trail |

---

## 기존 테이블 (v4.0 — 21개)

### 1. users (사용자)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| users | user_id | VARCHAR(50) | O | | N | 사용자ID |
| users | password | VARCHAR(255) | | | N | 암호화된 비밀번호 |
| users | name | VARCHAR(100) | | | N | 이름 |
| users | email | VARCHAR(200) | | | Y | 이메일 |
| users | role | VARCHAR(20) | | | N | admin/manager/worker/viewer |
| users | is_approved | BOOLEAN | | | N | 승인 여부 (DEFAULT TRUE) |
| users | created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 2. user_permissions (사용자 권한)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| user_permissions | id | SERIAL | O | | N | 권한ID (AUTO) |
| user_permissions | user_id | VARCHAR(50) | | users | N | 사용자ID |
| user_permissions | menu | VARCHAR(100) | | | N | 메뉴명 |
| user_permissions | can_read | BOOLEAN | | | Y | 읽기 권한 (DEFAULT TRUE) |
| user_permissions | can_write | BOOLEAN | | | Y | 쓰기 권한 (DEFAULT FALSE) |

> **제약**: UNIQUE(user_id, menu), ON DELETE CASCADE

### 3. items (품목 마스터)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| items | item_code | VARCHAR(20) | O | | N | 품목코드 |
| items | name | VARCHAR(200) | | | N | 품목명 |
| items | category | VARCHAR(20) | | | N | RAW/SEMI/PRODUCT |
| items | unit | VARCHAR(10) | | | N | 단위 (EA/KG/M 등, DEFAULT 'EA') |
| items | spec | VARCHAR(500) | | | Y | 규격 |
| items | safety_stock | INTEGER | | | N | 안전재고 (DEFAULT 0) |
| items | created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 4. bom (BOM — 자재명세서)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| bom | bom_id | SERIAL | O | | N | BOM ID (AUTO) |
| bom | parent_item | VARCHAR(20) | | items | N | 모품목 |
| bom | child_item | VARCHAR(20) | | items | N | 자품목 |
| bom | qty_per_unit | DECIMAL(10,4) | | | N | 소요량 (DEFAULT 1) |
| bom | loss_rate | DECIMAL(5,2) | | | N | 로스율(%) (DEFAULT 0) |

> **제약**: UNIQUE(parent_item, child_item)

### 5. processes (공정)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| processes | process_code | VARCHAR(20) | O | | N | 공정코드 |
| processes | name | VARCHAR(100) | | | N | 공정명 |
| processes | std_time_min | INTEGER | | | N | 표준작업시간(분) (DEFAULT 0) |
| processes | description | TEXT | | | Y | 공정 설명 |
| processes | equip_code | VARCHAR(20) | | equipments | Y | 기본설비 |

### 6. equipments (설비)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| equipments | equip_code | VARCHAR(20) | O | | N | 설비코드 |
| equipments | name | VARCHAR(100) | | | N | 설비명 |
| equipments | process_code | VARCHAR(20) | | processes | Y | 담당공정 |
| equipments | capacity_per_hour | INTEGER | | | N | 시간당 생산능력 (DEFAULT 100) |
| equipments | status | VARCHAR(20) | | | N | RUNNING/STOP/DOWN (DEFAULT 'STOP') |
| equipments | install_date | DATE | | | Y | 설치일 |

### 7. routings (라우팅)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| routings | routing_id | SERIAL | O | | N | 라우팅ID (AUTO) |
| routings | item_code | VARCHAR(20) | | items | N | 품목코드 |
| routings | seq | INTEGER | | | N | 공정순서 |
| routings | process_code | VARCHAR(20) | | processes | N | 공정코드 |
| routings | cycle_time | INTEGER | | | N | 사이클타임(분) (DEFAULT 0) |

> **제약**: UNIQUE(item_code, seq)

### 8. equip_status_log (설비 상태 이력)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| equip_status_log | log_id | SERIAL | O | | N | 로그ID (AUTO) |
| equip_status_log | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| equip_status_log | status | VARCHAR(20) | | | N | RUNNING/STOP/DOWN |
| equip_status_log | reason | TEXT | | | Y | 사유 |
| equip_status_log | worker_id | VARCHAR(50) | | | Y | 작업자ID |
| equip_status_log | changed_at | TIMESTAMP | | | Y | 변경일시 (DEFAULT NOW()) |

### 9. production_plans (생산 계획)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| production_plans | plan_id | SERIAL | O | | N | 계획ID (AUTO) |
| production_plans | item_code | VARCHAR(20) | | items | N | 품목코드 |
| production_plans | plan_qty | INTEGER | | | N | 계획수량 |
| production_plans | due_date | DATE | | | N | 납기일 |
| production_plans | priority | VARCHAR(10) | | | Y | HIGH/MID/LOW (DEFAULT 'MID') |
| production_plans | status | VARCHAR(20) | | | Y | WAIT/PROGRESS/DONE (DEFAULT 'WAIT') |
| production_plans | created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 10. work_orders (작업 지시)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| work_orders | wo_id | VARCHAR(30) | O | | N | 작업지시번호 |
| work_orders | plan_id | INTEGER | | production_plans | N | 생산계획ID |
| work_orders | item_code | VARCHAR(20) | | items | N | 품목코드 |
| work_orders | work_date | DATE | | | N | 작업일 |
| work_orders | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| work_orders | plan_qty | INTEGER | | | N | 지시수량 |
| work_orders | status | VARCHAR(20) | | | Y | WAIT/WORKING/DONE (DEFAULT 'WAIT') |

### 11. work_results (작업 실적)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| work_results | result_id | SERIAL | O | | N | 실적ID (AUTO) |
| work_results | wo_id | VARCHAR(30) | | work_orders | N | 작업지시번호 |
| work_results | good_qty | INTEGER | | | N | 양품수량 (DEFAULT 0) |
| work_results | defect_qty | INTEGER | | | N | 불량수량 (DEFAULT 0) |
| work_results | defect_code | VARCHAR(50) | | | Y | 불량코드 |
| work_results | worker_id | VARCHAR(50) | | | Y | 작업자ID |
| work_results | start_time | TIMESTAMP | | | Y | 시작시간 |
| work_results | end_time | TIMESTAMP | | | Y | 종료시간 |

### 12. quality_standards (품질 검사 기준)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| quality_standards | standard_id | SERIAL | O | | N | 기준ID (AUTO) |
| quality_standards | item_code | VARCHAR(20) | | items | N | 품목코드 |
| quality_standards | check_name | VARCHAR(100) | | | N | 검사항목명 |
| quality_standards | check_type | VARCHAR(20) | | | Y | NUMERIC/VISUAL/FUNCTIONAL (DEFAULT 'NUMERIC') |
| quality_standards | std_value | DECIMAL(10,4) | | | Y | 기준값 |
| quality_standards | min_value | DECIMAL(10,4) | | | Y | 최소값 |
| quality_standards | max_value | DECIMAL(10,4) | | | Y | 최대값 |
| quality_standards | unit | VARCHAR(20) | | | Y | 단위 |

### 13. inspections (품질 검사 결과)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| inspections | inspection_id | SERIAL | O | | N | 검사ID (AUTO) |
| inspections | inspect_type | VARCHAR(20) | | | N | INCOMING/PROCESS/OUTGOING |
| inspections | item_code | VARCHAR(20) | | items | N | 품목코드 |
| inspections | lot_no | VARCHAR(50) | | | Y | 로트번호 |
| inspections | judgment | VARCHAR(10) | | | Y | PASS/FAIL (DEFAULT 'PASS') |
| inspections | inspected_at | TIMESTAMP | | | Y | 검사일시 (DEFAULT NOW()) |
| inspections | inspector_id | VARCHAR(50) | | | Y | 검사자ID |

### 14. inspection_details (검사 상세)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| inspection_details | detail_id | SERIAL | O | | N | 상세ID (AUTO) |
| inspection_details | inspection_id | INTEGER | | inspections | N | 검사ID |
| inspection_details | check_name | VARCHAR(100) | | | N | 검사항목명 |
| inspection_details | measured_value | DECIMAL(10,4) | | | Y | 측정값 |
| inspection_details | judgment | VARCHAR(10) | | | Y | PASS/FAIL (DEFAULT 'PASS') |

> **제약**: ON DELETE CASCADE (inspections 삭제 시 연쇄 삭제)

### 15. defect_codes (불량 코드)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| defect_codes | defect_code | VARCHAR(50) | O | | N | 불량코드 |
| defect_codes | name | VARCHAR(100) | | | N | 불량명 |
| defect_codes | description | TEXT | | | Y | 설명 |

### 16. inventory (재고)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| inventory | inv_id | SERIAL | O | | N | 재고ID (AUTO) |
| inventory | item_code | VARCHAR(20) | | items | N | 품목코드 |
| inventory | lot_no | VARCHAR(50) | | | N | 로트번호 |
| inventory | qty | INTEGER | | | N | 수량 (DEFAULT 0) |
| inventory | warehouse | VARCHAR(10) | | | N | 창고 |
| inventory | location | VARCHAR(20) | | | Y | 위치 (A-01-01) |
| inventory | created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

> **제약**: UNIQUE(item_code, lot_no, warehouse)

### 17. inventory_transactions (재고 이동 전표)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| inventory_transactions | tx_id | SERIAL | O | | N | 전표ID (AUTO) |
| inventory_transactions | slip_no | VARCHAR(30) | | | N | 전표번호 |
| inventory_transactions | item_code | VARCHAR(20) | | items | N | 품목코드 |
| inventory_transactions | lot_no | VARCHAR(50) | | | Y | 로트번호 |
| inventory_transactions | qty | INTEGER | | | N | 수량 |
| inventory_transactions | tx_type | VARCHAR(10) | | | N | IN/OUT/MOVE |
| inventory_transactions | warehouse | VARCHAR(10) | | | Y | 창고 |
| inventory_transactions | location | VARCHAR(20) | | | Y | 위치 |
| inventory_transactions | ref_id | VARCHAR(50) | | | Y | 참조ID |
| inventory_transactions | supplier | VARCHAR(100) | | | Y | 공급업체 |
| inventory_transactions | created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 18. shipments (출하 이력)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| shipments | shipment_id | SERIAL | O | | N | 출하ID (AUTO) |
| shipments | item_code | VARCHAR(20) | | items | N | 품목코드 |
| shipments | ship_date | DATE | | | N | 출하일 |
| shipments | qty | INTEGER | | | N | 출하수량 |
| shipments | customer | VARCHAR(255) | | | Y | 고객사 |

### 19. defect_history (불량 이력 — 불량 예측용)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| defect_history | defect_id | SERIAL | O | | N | 불량이력ID (AUTO) |
| defect_history | item_code | VARCHAR(20) | | items | N | 품목코드 |
| defect_history | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| defect_history | recorded_at | TIMESTAMP | | | Y | 기록일시 (DEFAULT NOW()) |
| defect_history | temperature | NUMERIC(6,2) | | | Y | 온도 |
| defect_history | pressure | NUMERIC(6,2) | | | Y | 압력 |
| defect_history | speed | NUMERIC(6,2) | | | Y | 속도 |
| defect_history | humidity | NUMERIC(6,2) | | | Y | 습도 |
| defect_history | defect_count | INTEGER | | | Y | 불량 수 (DEFAULT 0) |
| defect_history | total_count | INTEGER | | | Y | 전체 수 (DEFAULT 0) |

### 20. equip_sensors (설비 센서 데이터 — AI 고장 예측용)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| equip_sensors | sensor_id | SERIAL | O | | N | 센서ID (AUTO) |
| equip_sensors | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| equip_sensors | vibration | DECIMAL(8,4) | | | Y | 진동 |
| equip_sensors | temperature | DECIMAL(8,4) | | | Y | 온도 |
| equip_sensors | current_amp | DECIMAL(8,4) | | | Y | 전류(A) |
| equip_sensors | recorded_at | TIMESTAMP | | | Y | 기록일시 (DEFAULT NOW()) |

### 21. ai_forecasts (AI 예측 결과)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| ai_forecasts | forecast_id | SERIAL | O | | N | 예측ID (AUTO) |
| ai_forecasts | model_type | VARCHAR(50) | | | N | 모델 유형 |
| ai_forecasts | item_code | VARCHAR(20) | | | Y | 품목코드 |
| ai_forecasts | equip_code | VARCHAR(20) | | | Y | 설비코드 |
| ai_forecasts | result_json | JSONB | | | Y | 예측 결과 (JSON) |
| ai_forecasts | created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

---

## Phase 1 — 신규 테이블 (7개)

### 22. spc_rules (SPC 관리 규칙)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| spc_rules | rule_id | SERIAL | O | | N | 규칙ID (AUTO) |
| spc_rules | item_code | VARCHAR(20) | | items | N | 품목코드 |
| spc_rules | check_name | VARCHAR(100) | | | N | 검사항목명 |
| spc_rules | rule_type | VARCHAR(30) | | | N | WESTERN_ELECTRIC/NELSON/CUSTOM |
| spc_rules | sample_size | INT | | | N | 서브그룹 크기 (DEFAULT 5) |
| spc_rules | ucl | DECIMAL(10,4) | | | Y | 상한관리한계선 |
| spc_rules | lcl | DECIMAL(10,4) | | | Y | 하한관리한계선 |
| spc_rules | target | DECIMAL(10,4) | | | Y | 중심선(목표값) |
| spc_rules | is_active | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |
| spc_rules | created_at | TIMESTAMP | | | Y | 생성일시 |

### 23. spc_violations (SPC 위반 이력)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| spc_violations | violation_id | SERIAL | O | | N | 위반ID (AUTO) |
| spc_violations | rule_id | INT | | spc_rules | N | SPC 규칙ID |
| spc_violations | inspection_id | INT | | inspections | N | 검사ID |
| spc_violations | violation_type | VARCHAR(50) | | | N | 위반 규칙 유형 |
| spc_violations | measured_value | DECIMAL(10,4) | | | Y | 측정값 |
| spc_violations | detected_at | TIMESTAMP | | | Y | 탐지일시 |
| spc_violations | resolved | BOOLEAN | | | N | 해결 여부 (DEFAULT FALSE) |
| spc_violations | resolved_by | VARCHAR(50) | | users | Y | 해결자 |

### 24. capa (시정/예방 조치)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| capa | capa_id | SERIAL | O | | N | CAPA ID (AUTO) |
| capa | capa_type | VARCHAR(5) | | | N | CA(시정조치)/PA(예방조치) |
| capa | title | VARCHAR(200) | | | N | 제목 |
| capa | description | TEXT | | | Y | 상세 설명 |
| capa | source_type | VARCHAR(30) | | | N | QUALITY_ISSUE/CUSTOMER_COMPLAINT/AUDIT/SPC_VIOLATION |
| capa | source_ref | VARCHAR(50) | | | Y | 관련 ID (inspection_id, violation_id 등) |
| capa | status | VARCHAR(20) | | | N | OPEN/INVESTIGATION/ACTION/VERIFICATION/CLOSED |
| capa | priority | VARCHAR(10) | | | N | HIGH/MID/LOW |
| capa | assigned_to | VARCHAR(50) | | users | N | 담당자 |
| capa | due_date | DATE | | | N | 기한 |
| capa | created_by | VARCHAR(50) | | users | N | 생성자 |
| capa | created_at | TIMESTAMP | | | Y | 생성일시 |
| capa | closed_at | TIMESTAMP | | | Y | 종료일시 |

### 25. capa_actions (CAPA 조치 이력)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| capa_actions | action_id | SERIAL | O | | N | 조치ID (AUTO) |
| capa_actions | capa_id | INT | | capa | N | CAPA ID |
| capa_actions | action_type | VARCHAR(30) | | | N | ROOT_CAUSE/CORRECTIVE/PREVENTIVE/VERIFICATION |
| capa_actions | description | TEXT | | | N | 조치 내용 |
| capa_actions | result | TEXT | | | Y | 조치 결과 |
| capa_actions | performed_by | VARCHAR(50) | | users | N | 수행자 |
| capa_actions | performed_at | TIMESTAMP | | | Y | 수행일시 |

### 26. oee_daily (OEE 일일 집계)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| oee_daily | oee_id | SERIAL | O | | N | OEE ID (AUTO) |
| oee_daily | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| oee_daily | calc_date | DATE | | | N | 산출일자 |
| oee_daily | availability | DECIMAL(5,4) | | | Y | 가용률 |
| oee_daily | performance | DECIMAL(5,4) | | | Y | 성능률 |
| oee_daily | quality_rate | DECIMAL(5,4) | | | Y | 품질률 |
| oee_daily | oee | DECIMAL(5,4) | | | Y | OEE (A x P x Q) |
| oee_daily | planned_time_min | INT | | | Y | 계획가동시간(분) |
| oee_daily | actual_run_min | INT | | | Y | 실제가동시간(분) |
| oee_daily | ideal_cycle_min | DECIMAL(8,2) | | | Y | 이상 사이클타임(분) |
| oee_daily | total_produced | INT | | | Y | 총 생산수량 |
| oee_daily | good_produced | INT | | | Y | 양품수량 |
| oee_daily | created_at | TIMESTAMP | | | Y | 생성일시 |

> **제약**: UNIQUE(equip_code, calc_date)

### 27. notifications (알림)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| notifications | notification_id | SERIAL | O | | N | 알림ID (AUTO) |
| notifications | user_id | VARCHAR(50) | | users | Y | 사용자ID (NULL이면 전체 알림) |
| notifications | type | VARCHAR(30) | | | N | EQUIP_DOWN/SPC_VIOLATION/INVENTORY_LOW/AI_WARNING/CAPA_DUE |
| notifications | title | VARCHAR(200) | | | N | 알림 제목 |
| notifications | message | TEXT | | | Y | 알림 내용 |
| notifications | severity | VARCHAR(10) | | | N | CRITICAL/WARNING/INFO |
| notifications | source_type | VARCHAR(30) | | | Y | 발생 모듈 |
| notifications | source_ref | VARCHAR(50) | | | Y | 관련 ID |
| notifications | is_read | BOOLEAN | | | N | 읽음 여부 (DEFAULT FALSE) |
| notifications | created_at | TIMESTAMP | | | Y | 생성일시 |

### 28. notification_settings (알림 설정)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| notification_settings | setting_id | SERIAL | O | | N | 설정ID (AUTO) |
| notification_settings | user_id | VARCHAR(50) | | users | N | 사용자ID |
| notification_settings | notification_type | VARCHAR(30) | | | N | 알림 유형 |
| notification_settings | channel | VARCHAR(20) | | | N | WEBSOCKET/EMAIL |
| notification_settings | is_enabled | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |

> **제약**: UNIQUE(user_id, notification_type, channel)

---

## Phase 2 — 신규 테이블 (8개)

### 29. maintenance_plans (예방보전 계획)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| maintenance_plans | pm_id | SERIAL | O | | N | PM ID (AUTO) |
| maintenance_plans | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| maintenance_plans | pm_type | VARCHAR(20) | | | N | TIME_BASED/USAGE_BASED/CONDITION_BASED |
| maintenance_plans | interval_days | INT | | | Y | 주기(일) |
| maintenance_plans | interval_hours | INT | | | Y | 주기(시간) |
| maintenance_plans | checklist | JSONB | | | Y | 점검항목 배열 |
| maintenance_plans | last_performed | TIMESTAMP | | | Y | 최근 수행일시 |
| maintenance_plans | next_due | DATE | | | N | 다음 예정일 |
| maintenance_plans | is_active | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |

### 30. maintenance_orders (정비 작업지시)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| maintenance_orders | mo_id | VARCHAR(30) | O | | N | 정비지시번호 (MO-날짜-순번) |
| maintenance_orders | pm_id | INT | | maintenance_plans | Y | PM 계획 ID (PM 기반이면 연결) |
| maintenance_orders | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| maintenance_orders | mo_type | VARCHAR(10) | | | N | PM(예방)/CM(사후)/BM(고장) |
| maintenance_orders | description | TEXT | | | Y | 작업 내용 |
| maintenance_orders | assigned_to | VARCHAR(50) | | users | N | 담당자 |
| maintenance_orders | status | VARCHAR(20) | | | N | PLANNED/IN_PROGRESS/COMPLETED/CANCELLED |
| maintenance_orders | start_time | TIMESTAMP | | | Y | 시작시간 |
| maintenance_orders | end_time | TIMESTAMP | | | Y | 종료시간 |
| maintenance_orders | cost | DECIMAL(12,2) | | | Y | 비용 |
| maintenance_orders | parts_used | JSONB | | | Y | 사용 부품 |
| maintenance_orders | created_at | TIMESTAMP | | | Y | 생성일시 |

### 31. recipes (레시피 마스터)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| recipes | recipe_id | SERIAL | O | | N | 레시피ID (AUTO) |
| recipes | recipe_code | VARCHAR(30) | | | N | 레시피코드 (UNIQUE) |
| recipes | item_code | VARCHAR(20) | | items | N | 품목코드 |
| recipes | process_code | VARCHAR(20) | | processes | N | 공정코드 |
| recipes | version | INT | | | N | 버전 (DEFAULT 1) |
| recipes | status | VARCHAR(20) | | | N | DRAFT/APPROVED/ACTIVE/OBSOLETE |
| recipes | description | TEXT | | | Y | 설명 |
| recipes | approved_by | VARCHAR(50) | | users | Y | 승인자 |
| recipes | created_at | TIMESTAMP | | | Y | 생성일시 |

> **제약**: UNIQUE(recipe_code, version)

### 32. recipe_parameters (레시피 파라미터)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| recipe_parameters | param_id | SERIAL | O | | N | 파라미터ID (AUTO) |
| recipe_parameters | recipe_id | INT | | recipes | N | 레시피ID |
| recipe_parameters | param_name | VARCHAR(100) | | | N | 파라미터명 (온도, 압력, 속도 등) |
| recipe_parameters | param_type | VARCHAR(20) | | | N | NUMERIC/TEXT/BOOLEAN |
| recipe_parameters | target_value | DECIMAL(10,4) | | | Y | 목표값 |
| recipe_parameters | min_value | DECIMAL(10,4) | | | Y | 최소값 |
| recipe_parameters | max_value | DECIMAL(10,4) | | | Y | 최대값 |
| recipe_parameters | unit | VARCHAR(20) | | | Y | 단위 |

### 33. mqtt_config (MQTT 수집 설정)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| mqtt_config | config_id | SERIAL | O | | N | 설정ID (AUTO) |
| mqtt_config | broker_url | VARCHAR(500) | | | N | MQTT 브로커 URL |
| mqtt_config | topic_pattern | VARCHAR(200) | | | N | 토픽 패턴 |
| mqtt_config | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| mqtt_config | sensor_type | VARCHAR(50) | | | N | 센서 유형 |
| mqtt_config | collect_interval_sec | INT | | | N | 수집 주기(초) (DEFAULT 10) |
| mqtt_config | is_active | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |

### 34. sensor_data (센서 수집 데이터 — 시계열)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| sensor_data | data_id | BIGSERIAL | O | | N | 데이터ID (AUTO) |
| sensor_data | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| sensor_data | sensor_type | VARCHAR(50) | | | N | 센서 유형 |
| sensor_data | value | DECIMAL(12,4) | | | N | 측정값 |
| sensor_data | collected_at | TIMESTAMP | | | N | 수집일시 |
| sensor_data | source | VARCHAR(20) | | | N | MQTT/OPCUA/MANUAL |

### 35. documents (문서 관리)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| documents | doc_id | SERIAL | O | | N | 문서ID (AUTO) |
| documents | doc_type | VARCHAR(20) | | | N | SOP/WI/QC_REPORT/SPEC/MANUAL |
| documents | title | VARCHAR(200) | | | N | 문서 제목 |
| documents | file_path | VARCHAR(500) | | | N | 파일 경로 |
| documents | file_size | INT | | | N | 파일 크기(byte) |
| documents | version | INT | | | N | 버전 (DEFAULT 1) |
| documents | item_code | VARCHAR(20) | | items | Y | 관련 품목코드 |
| documents | process_code | VARCHAR(20) | | processes | Y | 관련 공정코드 |
| documents | uploaded_by | VARCHAR(50) | | users | N | 업로더 |
| documents | created_at | TIMESTAMP | | | Y | 생성일시 |
| documents | is_active | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |

### 36. worker_skills (작업자 스킬매트릭스)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| worker_skills | skill_id | SERIAL | O | | N | 스킬ID (AUTO) |
| worker_skills | user_id | VARCHAR(50) | | users | N | 사용자ID |
| worker_skills | process_code | VARCHAR(20) | | processes | N | 공정코드 |
| worker_skills | skill_level | VARCHAR(10) | | | N | BEGINNER/INTERMEDIATE/ADVANCED/EXPERT |
| worker_skills | certified | BOOLEAN | | | N | 인증 여부 (DEFAULT FALSE) |
| worker_skills | cert_expiry | DATE | | | Y | 인증 만료일 |
| worker_skills | updated_at | TIMESTAMP | | | Y | 수정일시 |

> **제약**: UNIQUE(user_id, process_code)

---

## Phase 3 — 신규 테이블 (4개)

### 37. erp_sync_config (ERP 연동 설정)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| erp_sync_config | sync_id | SERIAL | O | | N | 동기화설정ID (AUTO) |
| erp_sync_config | erp_type | VARCHAR(30) | | | N | SAP/ORACLE/ETC |
| erp_sync_config | connection_url | VARCHAR(500) | | | N | 연결 URL |
| erp_sync_config | sync_direction | VARCHAR(10) | | | N | INBOUND/OUTBOUND/BIDIRECTIONAL |
| erp_sync_config | entity_type | VARCHAR(30) | | | N | ORDER/INVENTORY/BOM/ITEM |
| erp_sync_config | mapping_config | JSONB | | | Y | 매핑 설정 (JSON) |
| erp_sync_config | sync_interval_min | INT | | | N | 동기화 주기(분) |
| erp_sync_config | is_active | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |

### 38. erp_sync_log (ERP 동기화 이력)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| erp_sync_log | log_id | SERIAL | O | | N | 로그ID (AUTO) |
| erp_sync_log | sync_id | INT | | erp_sync_config | N | 동기화설정ID |
| erp_sync_log | direction | VARCHAR(10) | | | N | INBOUND/OUTBOUND |
| erp_sync_log | entity_type | VARCHAR(30) | | | N | 엔티티 유형 |
| erp_sync_log | records_processed | INT | | | N | 처리 건수 |
| erp_sync_log | records_success | INT | | | N | 성공 건수 |
| erp_sync_log | records_failed | INT | | | N | 실패 건수 |
| erp_sync_log | error_detail | TEXT | | | Y | 오류 상세 |
| erp_sync_log | synced_at | TIMESTAMP | | | Y | 동기화 일시 |

### 39. opcua_config (OPC-UA 설정)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| opcua_config | config_id | SERIAL | O | | N | 설정ID (AUTO) |
| opcua_config | server_url | VARCHAR(500) | | | N | OPC-UA 서버 URL |
| opcua_config | equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| opcua_config | node_id | VARCHAR(200) | | | N | OPC-UA 노드 ID |
| opcua_config | sensor_type | VARCHAR(50) | | | N | 센서 유형 |
| opcua_config | subscribe_interval_ms | INT | | | N | 구독 주기(ms) (DEFAULT 1000) |
| opcua_config | is_active | BOOLEAN | | | N | 활성 여부 (DEFAULT TRUE) |

### 40. audit_trail (감사 추적)

| 테이블명 | 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:--------:|:------:|:----:|:--:|:--:|:----:|:----:|
| audit_trail | audit_id | BIGSERIAL | O | | N | 감사ID (AUTO) |
| audit_trail | table_name | VARCHAR(50) | | | N | 대상 테이블명 |
| audit_trail | record_id | VARCHAR(100) | | | N | 대상 레코드 ID |
| audit_trail | action | VARCHAR(10) | | | N | INSERT/UPDATE/DELETE |
| audit_trail | old_value | JSONB | | | Y | 변경 전 값 |
| audit_trail | new_value | JSONB | | | Y | 변경 후 값 |
| audit_trail | changed_by | VARCHAR(50) | | | N | 변경자 |
| audit_trail | changed_at | TIMESTAMP | | | N | 변경일시 (DEFAULT NOW()) |
| audit_trail | ip_address | VARCHAR(45) | | | Y | IP 주소 |

---

## 인덱스 설계

> 한계점 분석에서 인덱스 부재가 지적됨. 아래는 주요 조회 패턴에 따른 권장 인덱스 목록.

### 기존 테이블 인덱스

| 대상 테이블 | 인덱스명 | 컬럼 | 유형 | 사유 |
|:-----------:|:--------:|:----:|:----:|:----:|
| users | idx_users_role | role | B-TREE | 역할별 사용자 조회 |
| items | idx_items_category | category | B-TREE | 카테고리별 품목 조회 |
| bom | idx_bom_parent | parent_item | B-TREE | 모품목 기준 BOM 전개 |
| bom | idx_bom_child | child_item | B-TREE | 역전개(Where-Used) |
| routings | idx_routings_item | item_code | B-TREE | 품목별 라우팅 조회 |
| equip_status_log | idx_equip_log_equip | equip_code | B-TREE | 설비별 상태 이력 조회 |
| equip_status_log | idx_equip_log_time | changed_at | B-TREE | 시간순 이력 조회 |
| production_plans | idx_plans_status | status | B-TREE | 상태별 계획 필터링 |
| production_plans | idx_plans_due | due_date | B-TREE | 납기일 기준 정렬 |
| work_orders | idx_wo_plan | plan_id | B-TREE | 계획별 작업지시 조회 |
| work_orders | idx_wo_date | work_date | B-TREE | 날짜별 작업지시 조회 |
| work_orders | idx_wo_status | status | B-TREE | 상태별 필터링 |
| work_results | idx_wr_wo | wo_id | B-TREE | 작업지시별 실적 조회 |
| work_results | idx_wr_worker | worker_id | B-TREE | 작업자별 실적 조회 |
| inspections | idx_insp_item | item_code | B-TREE | 품목별 검사 조회 |
| inspections | idx_insp_lot | lot_no | B-TREE | 로트별 검사 조회 |
| inspections | idx_insp_time | inspected_at | B-TREE | 시간순 검사 이력 |
| inspection_details | idx_insp_det_insp | inspection_id | B-TREE | 검사별 상세 조회 |
| inventory | idx_inv_item | item_code | B-TREE | 품목별 재고 조회 |
| inventory | idx_inv_wh | warehouse | B-TREE | 창고별 재고 조회 |
| inventory_transactions | idx_inv_tx_item | item_code | B-TREE | 품목별 이동 이력 |
| inventory_transactions | idx_inv_tx_slip | slip_no | B-TREE | 전표번호 조회 |
| inventory_transactions | idx_inv_tx_time | created_at | B-TREE | 시간순 이동 이력 |
| shipments | idx_ship_item | item_code | B-TREE | 품목별 출하 조회 |
| shipments | idx_ship_date | ship_date | B-TREE | 날짜별 출하 조회 |
| defect_history | idx_defect_hist_item | item_code | B-TREE | 품목별 불량 이력 |
| defect_history | idx_defect_hist_equip | equip_code | B-TREE | 설비별 불량 이력 |
| defect_history | idx_defect_hist_time | recorded_at | B-TREE | 시간순 불량 이력 |
| equip_sensors | idx_eq_sensor_equip | equip_code | B-TREE | 설비별 센서 데이터 |
| equip_sensors | idx_eq_sensor_time | recorded_at | B-TREE | 시간순 센서 데이터 |
| ai_forecasts | idx_ai_model | model_type | B-TREE | 모델별 예측 결과 |
| ai_forecasts | idx_ai_time | created_at | B-TREE | 최신 예측 결과 조회 |

### Phase 1 신규 테이블 인덱스

| 대상 테이블 | 인덱스명 | 컬럼 | 유형 | 사유 |
|:-----------:|:--------:|:----:|:----:|:----:|
| spc_rules | idx_spc_rules_item | item_code | B-TREE | 품목별 SPC 규칙 조회 |
| spc_rules | idx_spc_rules_active | is_active | B-TREE | 활성 규칙 필터링 |
| spc_violations | idx_spc_viol_rule | rule_id | B-TREE | 규칙별 위반 이력 |
| spc_violations | idx_spc_viol_time | detected_at | B-TREE | 시간순 위반 이력 |
| spc_violations | idx_spc_viol_resolved | resolved | B-TREE | 미해결 위반 필터링 |
| capa | idx_capa_status | status | B-TREE | 상태별 CAPA 조회 |
| capa | idx_capa_assigned | assigned_to | B-TREE | 담당자별 CAPA 조회 |
| capa | idx_capa_due | due_date | B-TREE | 기한 임박 CAPA 조회 |
| capa_actions | idx_capa_act_capa | capa_id | B-TREE | CAPA별 조치 이력 |
| oee_daily | idx_oee_equip | equip_code | B-TREE | 설비별 OEE 조회 |
| oee_daily | idx_oee_date | calc_date | B-TREE | 날짜별 OEE 조회 |
| notifications | idx_noti_user | user_id | B-TREE | 사용자별 알림 조회 |
| notifications | idx_noti_read | is_read | B-TREE | 미읽음 알림 필터링 |
| notifications | idx_noti_time | created_at | B-TREE | 최신 알림 정렬 |
| notification_settings | idx_noti_set_user | user_id | B-TREE | 사용자별 설정 조회 |

### Phase 2 신규 테이블 인덱스

| 대상 테이블 | 인덱스명 | 컬럼 | 유형 | 사유 |
|:-----------:|:--------:|:----:|:----:|:----:|
| maintenance_plans | idx_mp_equip | equip_code | B-TREE | 설비별 보전 계획 |
| maintenance_plans | idx_mp_next_due | next_due | B-TREE | 예정일 기준 정렬 |
| maintenance_orders | idx_mo_equip | equip_code | B-TREE | 설비별 정비 이력 |
| maintenance_orders | idx_mo_status | status | B-TREE | 상태별 정비 조회 |
| maintenance_orders | idx_mo_assigned | assigned_to | B-TREE | 담당자별 정비 조회 |
| recipes | idx_recipe_item | item_code | B-TREE | 품목별 레시피 조회 |
| recipes | idx_recipe_process | process_code | B-TREE | 공정별 레시피 조회 |
| recipes | idx_recipe_status | status | B-TREE | 상태별 레시피 필터링 |
| recipe_parameters | idx_rparam_recipe | recipe_id | B-TREE | 레시피별 파라미터 조회 |
| mqtt_config | idx_mqtt_equip | equip_code | B-TREE | 설비별 MQTT 설정 |
| sensor_data | idx_sensor_equip | equip_code | B-TREE | 설비별 센서 데이터 |
| sensor_data | idx_sensor_time | collected_at | B-TREE | 시간순 센서 데이터 |
| sensor_data | idx_sensor_equip_time | (equip_code, collected_at) | B-TREE (복합) | 설비+시간 범위 조회 (시계열 핵심) |
| documents | idx_doc_type | doc_type | B-TREE | 문서유형별 조회 |
| documents | idx_doc_item | item_code | B-TREE | 품목별 문서 조회 |
| documents | idx_doc_uploaded | uploaded_by | B-TREE | 업로더별 문서 조회 |
| worker_skills | idx_ws_user | user_id | B-TREE | 사용자별 스킬 조회 |
| worker_skills | idx_ws_process | process_code | B-TREE | 공정별 가용 작업자 조회 |

### Phase 3 신규 테이블 인덱스

| 대상 테이블 | 인덱스명 | 컬럼 | 유형 | 사유 |
|:-----------:|:--------:|:----:|:----:|:----:|
| erp_sync_config | idx_erp_cfg_active | is_active | B-TREE | 활성 동기화 설정 |
| erp_sync_log | idx_erp_log_sync | sync_id | B-TREE | 설정별 동기화 이력 |
| erp_sync_log | idx_erp_log_time | synced_at | B-TREE | 시간순 동기화 이력 |
| opcua_config | idx_opcua_equip | equip_code | B-TREE | 설비별 OPC-UA 설정 |
| audit_trail | idx_audit_table | table_name | B-TREE | 테이블별 감사 이력 |
| audit_trail | idx_audit_record | (table_name, record_id) | B-TREE (복합) | 특정 레코드 변경 이력 |
| audit_trail | idx_audit_time | changed_at | B-TREE | 시간순 감사 이력 |
| audit_trail | idx_audit_user | changed_by | B-TREE | 사용자별 변경 이력 |

---

## ER 다이어그램 요약 (주요 FK 관계)

```
users ──┬── user_permissions
        ├── capa (assigned_to, created_by)
        ├── capa_actions (performed_by)
        ├── spc_violations (resolved_by)
        ├── maintenance_orders (assigned_to)
        ├── recipes (approved_by)
        ├── documents (uploaded_by)
        ├── worker_skills
        ├── notifications
        └── notification_settings

items ──┬── bom (parent_item, child_item)
        ├── routings
        ├── production_plans
        ├── work_orders
        ├── quality_standards
        ├── inspections
        ├── inventory
        ├── inventory_transactions
        ├── shipments
        ├── defect_history
        ├── spc_rules
        ├── recipes
        └── documents

equipments ──┬── processes (상호 참조)
             ├── work_orders
             ├── equip_status_log
             ├── defect_history
             ├── equip_sensors
             ├── oee_daily
             ├── maintenance_plans
             ├── maintenance_orders
             ├── mqtt_config
             ├── sensor_data
             └── opcua_config

processes ──┬── equipments (상호 참조)
            ├── routings
            ├── recipes
            ├── documents
            └── worker_skills

inspections ──── inspection_details (ON DELETE CASCADE)
             └── spc_violations

spc_rules ──── spc_violations
capa ──── capa_actions
recipes ──── recipe_parameters
maintenance_plans ──── maintenance_orders
erp_sync_config ──── erp_sync_log
production_plans ──── work_orders
work_orders ──── work_results
```

---

## 테이블 파티셔닝 권장 사항

> 시계열 데이터가 대량으로 축적되는 테이블은 파티셔닝을 권장합니다.

| 테이블 | 파티션 기준 | 전략 | 비고 |
|:------:|:----------:|:----:|:----:|
| sensor_data | collected_at | RANGE (월별) | 시계열 센서 데이터, 가장 빠른 성장 예상 |
| audit_trail | changed_at | RANGE (월별) | 모든 변경 이력 축적 |
| equip_sensors | recorded_at | RANGE (월별) | 기존 센서 데이터 |
| defect_history | recorded_at | RANGE (분기별) | 불량 이력 누적 |
| notifications | created_at | RANGE (월별) | 알림 이력 누적 |
| inventory_transactions | created_at | RANGE (분기별) | 재고 이동 이력 |

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|:----:|:----:|:---------:|
| v4.0 | 2025-12 | 초기 스키마 (9개 테이블: users, items, bom, processes, equipments, production_plans, work_orders, work_results, inventory) |
| v4.0+ | 2026-01 | 실 구현 확장 (21개 테이블: user_permissions, routings, equip_status_log, quality_standards, inspections, inspection_details, defect_codes, inventory_transactions, shipments, defect_history, equip_sensors, ai_forecasts 추가) |
| v6.0 | 2026-03-03 | 한계점 분석 기반 신규 19개 테이블 추가 (SPC, CAPA, OEE, 알림, 보전, 레시피, MQTT, 센서, 문서, 스킬, ERP, OPC-UA, 감사) + 인덱스 설계 |
