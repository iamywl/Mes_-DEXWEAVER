# DEXWEAVER MES v4.0 — 데이터베이스 스키마

> **버전**: v4.0 (총 21개 테이블)
> **작성일**: 2025-12-01
> **데이터베이스**: PostgreSQL 15
> **설명**: 초기 MES 시스템 데이터베이스 스키마

---

## 테이블 목록

| # | 테이블명 | 설명 | 주요 FK |
|:-:|:--------:|:----:|:-------:|
| 1 | users | 사용자 | - |
| 2 | user_permissions | 사용자 권한 | users |
| 3 | items | 품목 마스터 | - |
| 4 | bom | 자재명세서 | items |
| 5 | processes | 공정 | equipments |
| 6 | equipments | 설비 | processes |
| 7 | routings | 라우팅 | items, processes |
| 8 | equip_status_log | 설비 상태 이력 | equipments |
| 9 | production_plans | 생산 계획 | items |
| 10 | work_orders | 작업 지시 | production_plans, items, equipments |
| 11 | work_results | 작업 실적 | work_orders |
| 12 | quality_standards | 품질 검사 기준 | items |
| 13 | inspections | 품질 검사 결과 | items |
| 14 | inspection_details | 검사 상세 | inspections |
| 15 | defect_codes | 불량 코드 | - |
| 16 | inventory | 재고 | items |
| 17 | inventory_transactions | 재고 이동 전표 | items |
| 18 | shipments | 출하 이력 | items |
| 19 | defect_history | 불량 이력 | items, equipments |
| 20 | equip_sensors | 설비 센서 데이터 | equipments |
| 21 | ai_forecasts | AI 예측 결과 | - |

---

## 테이블 상세

### 1. users (사용자)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| user_id | VARCHAR(50) | O | | N | 사용자ID |
| password | VARCHAR(255) | | | N | 암호화된 비밀번호 |
| name | VARCHAR(100) | | | N | 이름 |
| email | VARCHAR(200) | | | Y | 이메일 |
| role | VARCHAR(20) | | | N | admin/manager/worker/viewer |
| is_approved | BOOLEAN | | | N | 승인 여부 (DEFAULT TRUE) |
| created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 2. user_permissions (사용자 권한)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| id | SERIAL | O | | N | 권한ID (AUTO) |
| user_id | VARCHAR(50) | | users | N | 사용자ID |
| menu | VARCHAR(100) | | | N | 메뉴명 |
| can_read | BOOLEAN | | | Y | 읽기 권한 (DEFAULT TRUE) |
| can_write | BOOLEAN | | | Y | 쓰기 권한 (DEFAULT FALSE) |

> **제약**: UNIQUE(user_id, menu), ON DELETE CASCADE

### 3. items (품목 마스터)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| item_code | VARCHAR(20) | O | | N | 품목코드 |
| name | VARCHAR(200) | | | N | 품목명 |
| category | VARCHAR(20) | | | N | RAW/SEMI/PRODUCT |
| unit | VARCHAR(10) | | | N | 단위 (EA/KG/M 등, DEFAULT 'EA') |
| spec | VARCHAR(500) | | | Y | 규격 |
| safety_stock | INTEGER | | | N | 안전재고 (DEFAULT 0) |
| created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 4. bom (BOM — 자재명세서)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| bom_id | SERIAL | O | | N | BOM ID (AUTO) |
| parent_item | VARCHAR(20) | | items | N | 모품목 |
| child_item | VARCHAR(20) | | items | N | 자품목 |
| qty_per_unit | DECIMAL(10,4) | | | N | 소요량 (DEFAULT 1) |
| loss_rate | DECIMAL(5,2) | | | N | 로스율(%) (DEFAULT 0) |

> **제약**: UNIQUE(parent_item, child_item)

### 5. processes (공정)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| process_code | VARCHAR(20) | O | | N | 공정코드 |
| name | VARCHAR(100) | | | N | 공정명 |
| std_time_min | INTEGER | | | N | 표준작업시간(분) (DEFAULT 0) |
| description | TEXT | | | Y | 공정 설명 |
| equip_code | VARCHAR(20) | | equipments | Y | 기본설비 |

### 6. equipments (설비)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| equip_code | VARCHAR(20) | O | | N | 설비코드 |
| name | VARCHAR(100) | | | N | 설비명 |
| process_code | VARCHAR(20) | | processes | Y | 담당공정 |
| capacity_per_hour | INTEGER | | | N | 시간당 생산능력 (DEFAULT 100) |
| status | VARCHAR(20) | | | N | RUNNING/STOP/DOWN (DEFAULT 'STOP') |
| install_date | DATE | | | Y | 설치일 |

### 7. routings (라우팅)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| routing_id | SERIAL | O | | N | 라우팅ID (AUTO) |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| seq | INTEGER | | | N | 공정순서 |
| process_code | VARCHAR(20) | | processes | N | 공정코드 |
| cycle_time | INTEGER | | | N | 사이클타임(분) (DEFAULT 0) |

> **제약**: UNIQUE(item_code, seq)

### 8. equip_status_log (설비 상태 이력)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| log_id | SERIAL | O | | N | 로그ID (AUTO) |
| equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| status | VARCHAR(20) | | | N | RUNNING/STOP/DOWN |
| reason | TEXT | | | Y | 사유 |
| worker_id | VARCHAR(50) | | | Y | 작업자ID |
| changed_at | TIMESTAMP | | | Y | 변경일시 (DEFAULT NOW()) |

### 9. production_plans (생산 계획)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| plan_id | SERIAL | O | | N | 계획ID (AUTO) |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| plan_qty | INTEGER | | | N | 계획수량 |
| due_date | DATE | | | N | 납기일 |
| priority | VARCHAR(10) | | | Y | HIGH/MID/LOW (DEFAULT 'MID') |
| status | VARCHAR(20) | | | Y | WAIT/PROGRESS/DONE (DEFAULT 'WAIT') |
| created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 10. work_orders (작업 지시)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| wo_id | VARCHAR(30) | O | | N | 작업지시번호 |
| plan_id | INTEGER | | production_plans | N | 생산계획ID |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| work_date | DATE | | | N | 작업일 |
| equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| plan_qty | INTEGER | | | N | 지시수량 |
| status | VARCHAR(20) | | | Y | WAIT/WORKING/DONE (DEFAULT 'WAIT') |

### 11. work_results (작업 실적)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| result_id | SERIAL | O | | N | 실적ID (AUTO) |
| wo_id | VARCHAR(30) | | work_orders | N | 작업지시번호 |
| good_qty | INTEGER | | | N | 양품수량 (DEFAULT 0) |
| defect_qty | INTEGER | | | N | 불량수량 (DEFAULT 0) |
| defect_code | VARCHAR(50) | | | Y | 불량코드 |
| worker_id | VARCHAR(50) | | | Y | 작업자ID |
| start_time | TIMESTAMP | | | Y | 시작시간 |
| end_time | TIMESTAMP | | | Y | 종료시간 |

### 12. quality_standards (품질 검사 기준)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| standard_id | SERIAL | O | | N | 기준ID (AUTO) |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| check_name | VARCHAR(100) | | | N | 검사항목명 |
| check_type | VARCHAR(20) | | | Y | NUMERIC/VISUAL/FUNCTIONAL (DEFAULT 'NUMERIC') |
| std_value | DECIMAL(10,4) | | | Y | 기준값 |
| min_value | DECIMAL(10,4) | | | Y | 최소값 |
| max_value | DECIMAL(10,4) | | | Y | 최대값 |
| unit | VARCHAR(20) | | | Y | 단위 |

### 13. inspections (품질 검사 결과)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| inspection_id | SERIAL | O | | N | 검사ID (AUTO) |
| inspect_type | VARCHAR(20) | | | N | INCOMING/PROCESS/OUTGOING |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| lot_no | VARCHAR(50) | | | Y | 로트번호 |
| judgment | VARCHAR(10) | | | Y | PASS/FAIL (DEFAULT 'PASS') |
| inspected_at | TIMESTAMP | | | Y | 검사일시 (DEFAULT NOW()) |
| inspector_id | VARCHAR(50) | | | Y | 검사자ID |

### 14. inspection_details (검사 상세)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| detail_id | SERIAL | O | | N | 상세ID (AUTO) |
| inspection_id | INTEGER | | inspections | N | 검사ID |
| check_name | VARCHAR(100) | | | N | 검사항목명 |
| measured_value | DECIMAL(10,4) | | | Y | 측정값 |
| judgment | VARCHAR(10) | | | Y | PASS/FAIL (DEFAULT 'PASS') |

> **제약**: ON DELETE CASCADE (inspections 삭제 시 연쇄 삭제)

### 15. defect_codes (불량 코드)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| defect_code | VARCHAR(50) | O | | N | 불량코드 |
| name | VARCHAR(100) | | | N | 불량명 |
| description | TEXT | | | Y | 설명 |

### 16. inventory (재고)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| inv_id | SERIAL | O | | N | 재고ID (AUTO) |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| lot_no | VARCHAR(50) | | | N | 로트번호 |
| qty | INTEGER | | | N | 수량 (DEFAULT 0) |
| warehouse | VARCHAR(10) | | | N | 창고 |
| location | VARCHAR(20) | | | Y | 위치 (A-01-01) |
| created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

> **제약**: UNIQUE(item_code, lot_no, warehouse)

### 17. inventory_transactions (재고 이동 전표)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| tx_id | SERIAL | O | | N | 전표ID (AUTO) |
| slip_no | VARCHAR(30) | | | N | 전표번호 |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| lot_no | VARCHAR(50) | | | Y | 로트번호 |
| qty | INTEGER | | | N | 수량 |
| tx_type | VARCHAR(10) | | | N | IN/OUT/MOVE |
| warehouse | VARCHAR(10) | | | Y | 창고 |
| location | VARCHAR(20) | | | Y | 위치 |
| ref_id | VARCHAR(50) | | | Y | 참조ID |
| supplier | VARCHAR(100) | | | Y | 공급업체 |
| created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

### 18. shipments (출하 이력)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| shipment_id | SERIAL | O | | N | 출하ID (AUTO) |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| ship_date | DATE | | | N | 출하일 |
| qty | INTEGER | | | N | 출하수량 |
| customer | VARCHAR(255) | | | Y | 고객사 |

### 19. defect_history (불량 이력 — 불량 예측용)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| defect_id | SERIAL | O | | N | 불량이력ID (AUTO) |
| item_code | VARCHAR(20) | | items | N | 품목코드 |
| equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| recorded_at | TIMESTAMP | | | Y | 기록일시 (DEFAULT NOW()) |
| temperature | NUMERIC(6,2) | | | Y | 온도 |
| pressure | NUMERIC(6,2) | | | Y | 압력 |
| speed | NUMERIC(6,2) | | | Y | 속도 |
| humidity | NUMERIC(6,2) | | | Y | 습도 |
| defect_count | INTEGER | | | Y | 불량 수 (DEFAULT 0) |
| total_count | INTEGER | | | Y | 전체 수 (DEFAULT 0) |

### 20. equip_sensors (설비 센서 데이터 — AI 고장 예측용)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| sensor_id | SERIAL | O | | N | 센서ID (AUTO) |
| equip_code | VARCHAR(20) | | equipments | N | 설비코드 |
| vibration | DECIMAL(8,4) | | | Y | 진동 |
| temperature | DECIMAL(8,4) | | | Y | 온도 |
| current_amp | DECIMAL(8,4) | | | Y | 전류(A) |
| recorded_at | TIMESTAMP | | | Y | 기록일시 (DEFAULT NOW()) |

### 21. ai_forecasts (AI 예측 결과)

| 컬럼명 | 타입 | PK | FK | NULL | 설명 |
|:------:|:----:|:--:|:--:|:----:|:----:|
| forecast_id | SERIAL | O | | N | 예측ID (AUTO) |
| model_type | VARCHAR(50) | | | N | 모델 유형 |
| item_code | VARCHAR(20) | | | Y | 품목코드 |
| equip_code | VARCHAR(20) | | | Y | 설비코드 |
| result_json | JSONB | | | Y | 예측 결과 (JSON) |
| created_at | TIMESTAMP | | | Y | 생성일시 (DEFAULT NOW()) |

---

## ER 다이어그램 요약 (주요 FK 관계)

```
users ──── user_permissions

items ──┬── bom (parent_item, child_item)
        ├── routings
        ├── production_plans
        ├── work_orders
        ├── quality_standards
        ├── inspections
        ├── inventory
        ├── inventory_transactions
        ├── shipments
        └── defect_history

equipments ──┬── processes (상호 참조)
             ├── work_orders
             ├── equip_status_log
             ├── defect_history
             └── equip_sensors

processes ──┬── equipments (상호 참조)
            └── routings

inspections ──── inspection_details (ON DELETE CASCADE)
production_plans ──── work_orders
work_orders ──── work_results
```

---

## 알려진 한계점

> 이 버전(v4.0)의 한계점은 [한계점 분석 보고서](../../../research/limitations/00_종합_한계점_요약.md)에서 상세히 다루고 있습니다.

- 인덱스 미설계 (21개 테이블에 인덱스 0개)
- DB 마이그레이션 도구 미사용 (init.sql 수동 관리)
- 동기 드라이버 사용 (psycopg2, 비동기 asyncpg 미적용)
- 파티셔닝 미적용 (시계열 데이터 증가 시 성능 저하 예상)
