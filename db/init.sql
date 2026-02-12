-- =============================================================
-- MES Database Schema (v3.0) - Full System
-- Requirements_Specification + DatabaseSchema.md 기반
-- =============================================================

-- ─── 1. 사용자 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id    VARCHAR(50) PRIMARY KEY,
    password   VARCHAR(255) NOT NULL,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(200),
    role       VARCHAR(20) NOT NULL DEFAULT 'worker'
                   CHECK (role IN ('admin','worker','viewer')),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_permissions (
    id       SERIAL PRIMARY KEY,
    user_id  VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE,
    menu     VARCHAR(100) NOT NULL,
    can_read  BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, menu)
);

-- ─── 2. 품목 마스터 ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS items (
    item_code    VARCHAR(20) PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    category     VARCHAR(20) NOT NULL DEFAULT 'RAW'
                     CHECK (category IN ('RAW','SEMI','PRODUCT')),
    unit         VARCHAR(10) NOT NULL DEFAULT 'EA',
    spec         VARCHAR(500),
    safety_stock INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMP DEFAULT NOW()
);

-- ─── 3. BOM ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bom (
    bom_id       SERIAL PRIMARY KEY,
    parent_item  VARCHAR(20) REFERENCES items(item_code),
    child_item   VARCHAR(20) REFERENCES items(item_code),
    qty_per_unit DECIMAL(10,4) NOT NULL DEFAULT 1,
    loss_rate    DECIMAL(5,2) NOT NULL DEFAULT 0,
    UNIQUE(parent_item, child_item)
);

-- ─── 4. 공정 ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS processes (
    process_code VARCHAR(20) PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    std_time_min INTEGER NOT NULL DEFAULT 0,
    description  TEXT,
    equip_code   VARCHAR(20)
);

-- ─── 5. 설비 ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS equipments (
    equip_code        VARCHAR(20) PRIMARY KEY,
    name              VARCHAR(100) NOT NULL,
    process_code      VARCHAR(20),
    capacity_per_hour INTEGER NOT NULL DEFAULT 100,
    status            VARCHAR(20) NOT NULL DEFAULT 'STOP'
                          CHECK (status IN ('RUNNING','STOP','DOWN')),
    install_date      DATE
);

-- processes.equip_code FK (deferred because of circular dependency)
ALTER TABLE processes
    DROP CONSTRAINT IF EXISTS fk_proc_equip;
ALTER TABLE processes
    ADD CONSTRAINT fk_proc_equip
    FOREIGN KEY (equip_code) REFERENCES equipments(equip_code);

ALTER TABLE equipments
    DROP CONSTRAINT IF EXISTS fk_equip_proc;
ALTER TABLE equipments
    ADD CONSTRAINT fk_equip_proc
    FOREIGN KEY (process_code) REFERENCES processes(process_code);

-- ─── 6. 라우팅 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS routings (
    routing_id   SERIAL PRIMARY KEY,
    item_code    VARCHAR(20) REFERENCES items(item_code),
    seq          INTEGER NOT NULL,
    process_code VARCHAR(20) REFERENCES processes(process_code),
    cycle_time   INTEGER NOT NULL DEFAULT 0,
    UNIQUE(item_code, seq)
);

-- ─── 7. 설비 상태 이력 ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS equip_status_log (
    log_id     SERIAL PRIMARY KEY,
    equip_code VARCHAR(20) REFERENCES equipments(equip_code),
    status     VARCHAR(20) NOT NULL
                   CHECK (status IN ('RUNNING','STOP','DOWN')),
    reason     TEXT,
    worker_id  VARCHAR(50),
    changed_at TIMESTAMP DEFAULT NOW()
);

-- ─── 8. 생산 계획 ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS production_plans (
    plan_id    SERIAL PRIMARY KEY,
    item_code  VARCHAR(20) REFERENCES items(item_code),
    plan_qty   INTEGER NOT NULL,
    due_date   DATE NOT NULL,
    priority   VARCHAR(10) DEFAULT 'MID'
                   CHECK (priority IN ('HIGH','MID','LOW')),
    status     VARCHAR(20) DEFAULT 'WAIT'
                   CHECK (status IN ('WAIT','PROGRESS','DONE')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─── 9. 작업 지시 ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS work_orders (
    wo_id      VARCHAR(30) PRIMARY KEY,
    plan_id    INTEGER REFERENCES production_plans(plan_id),
    item_code  VARCHAR(20) REFERENCES items(item_code),
    work_date  DATE NOT NULL,
    equip_code VARCHAR(20) REFERENCES equipments(equip_code),
    plan_qty   INTEGER NOT NULL,
    status     VARCHAR(20) DEFAULT 'WAIT'
                   CHECK (status IN ('WAIT','WORKING','DONE'))
);

-- ─── 10. 작업 실적 ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS work_results (
    result_id  SERIAL PRIMARY KEY,
    wo_id      VARCHAR(30) REFERENCES work_orders(wo_id),
    good_qty   INTEGER NOT NULL DEFAULT 0,
    defect_qty INTEGER NOT NULL DEFAULT 0,
    defect_code VARCHAR(50),
    worker_id  VARCHAR(50),
    start_time TIMESTAMP,
    end_time   TIMESTAMP
);

-- ─── 11. 품질 검사 기준 ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS quality_standards (
    standard_id SERIAL PRIMARY KEY,
    item_code   VARCHAR(20) REFERENCES items(item_code),
    check_name  VARCHAR(100) NOT NULL,
    check_type  VARCHAR(20) DEFAULT 'NUMERIC'
                    CHECK (check_type IN ('NUMERIC','VISUAL','FUNCTIONAL')),
    std_value   DECIMAL(10,4),
    min_value   DECIMAL(10,4),
    max_value   DECIMAL(10,4),
    unit        VARCHAR(20)
);

-- ─── 12. 품질 검사 결과 ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id SERIAL PRIMARY KEY,
    inspect_type  VARCHAR(20) NOT NULL
                      CHECK (inspect_type IN ('INCOMING','PROCESS','OUTGOING')),
    item_code     VARCHAR(20) REFERENCES items(item_code),
    lot_no        VARCHAR(50),
    judgment      VARCHAR(10) DEFAULT 'PASS'
                      CHECK (judgment IN ('PASS','FAIL')),
    inspected_at  TIMESTAMP DEFAULT NOW(),
    inspector_id  VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS inspection_details (
    detail_id     SERIAL PRIMARY KEY,
    inspection_id INTEGER REFERENCES inspections(inspection_id) ON DELETE CASCADE,
    check_name    VARCHAR(100) NOT NULL,
    measured_value DECIMAL(10,4),
    judgment      VARCHAR(10) DEFAULT 'PASS'
                      CHECK (judgment IN ('PASS','FAIL'))
);

-- ─── 13. 불량 코드 ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS defect_codes (
    defect_code VARCHAR(50) PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT
);

-- ─── 14. 재고 ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory (
    inv_id    SERIAL PRIMARY KEY,
    item_code VARCHAR(20) REFERENCES items(item_code),
    lot_no    VARCHAR(50) NOT NULL,
    qty       INTEGER NOT NULL DEFAULT 0,
    warehouse VARCHAR(10) NOT NULL,
    location  VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(item_code, lot_no, warehouse)
);

-- ─── 15. 재고 이동 전표 ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS inventory_transactions (
    tx_id      SERIAL PRIMARY KEY,
    slip_no    VARCHAR(30) NOT NULL,
    item_code  VARCHAR(20) REFERENCES items(item_code),
    lot_no     VARCHAR(50),
    qty        INTEGER NOT NULL,
    tx_type    VARCHAR(10) NOT NULL
                   CHECK (tx_type IN ('IN','OUT','MOVE')),
    warehouse  VARCHAR(10),
    location   VARCHAR(20),
    ref_id     VARCHAR(50),
    supplier   VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─── 16. 출하 이력 (수요 예측용) ────────────────────────────
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id SERIAL PRIMARY KEY,
    item_code   VARCHAR(20) REFERENCES items(item_code),
    ship_date   DATE NOT NULL,
    qty         INTEGER NOT NULL,
    customer    VARCHAR(255)
);

-- ─── 17. 불량 이력 (불량 예측용) ────────────────────────────
CREATE TABLE IF NOT EXISTS defect_history (
    defect_id    SERIAL PRIMARY KEY,
    item_code    VARCHAR(20) REFERENCES items(item_code),
    equip_code   VARCHAR(20) REFERENCES equipments(equip_code),
    recorded_at  TIMESTAMP DEFAULT NOW(),
    temperature  NUMERIC(6,2),
    pressure     NUMERIC(6,2),
    speed        NUMERIC(6,2),
    humidity     NUMERIC(6,2),
    defect_count INTEGER DEFAULT 0,
    total_count  INTEGER DEFAULT 0
);

-- ─── 18. 설비 센서 데이터 (AI 고장 예측용) ──────────────────
CREATE TABLE IF NOT EXISTS equip_sensors (
    sensor_id   SERIAL PRIMARY KEY,
    equip_code  VARCHAR(20) REFERENCES equipments(equip_code),
    vibration   DECIMAL(8,4),
    temperature DECIMAL(8,4),
    current_amp DECIMAL(8,4),
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- ─── 19. AI 예측 결과 저장 ──────────────────────────────────
CREATE TABLE IF NOT EXISTS ai_forecasts (
    forecast_id SERIAL PRIMARY KEY,
    model_type  VARCHAR(50) NOT NULL,
    item_code   VARCHAR(20),
    equip_code  VARCHAR(20),
    result_json JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);


-- =============================================================
-- Seed Data
-- =============================================================

-- 사용자 (bcrypt hash of 'admin123' and 'worker123')
INSERT INTO users (user_id, password, name, email, role) VALUES
('admin',   '$2b$12$LJ3m4ys4Dz8Xw4Q5E9r7/.dummy.hash.for.seed', '관리자', 'admin@knu.ac.kr', 'admin'),
('worker01','$2b$12$LJ3m4ys4Dz8Xw4Q5E9r7/.dummy.hash.for.seed', '작업자1', 'w1@knu.ac.kr',   'worker'),
('viewer01','$2b$12$LJ3m4ys4Dz8Xw4Q5E9r7/.dummy.hash.for.seed', '조회자1', 'v1@knu.ac.kr',   'viewer')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_permissions (user_id, menu, can_read, can_write) VALUES
('admin',   'ALL',             TRUE, TRUE),
('worker01','PRODUCTION_PLAN', TRUE, TRUE),
('worker01','WORK_ORDER',      TRUE, TRUE),
('worker01','INVENTORY',       TRUE, TRUE),
('viewer01','DASHBOARD',       TRUE, FALSE),
('viewer01','REPORTS',         TRUE, FALSE)
ON CONFLICT (user_id, menu) DO NOTHING;

-- 품목 마스터
INSERT INTO items (item_code, name, category, unit, spec, safety_stock) VALUES
('ITEM001', '원자재A',    'RAW',     'KG', 'SUS304 Φ10',       100),
('ITEM002', '반제품B',    'SEMI',    'EA', '가공부품 L=50mm',    50),
('ITEM003', '완제품C',    'PRODUCT', 'EA', '조립완료품',         30),
('ITEM004', '중간부품D',  'SEMI',    'EA', '프레스부품',         40),
('ITEM005', '최종제품E',  'PRODUCT', 'EA', '최종조립품',         20)
ON CONFLICT (item_code) DO NOTHING;

-- 공정
INSERT INTO processes (process_code, name, std_time_min, description) VALUES
('PRC-001', '절단',   10, '원자재 절단 공정'),
('PRC-002', '가공',   20, 'CNC 가공 공정'),
('PRC-003', '조립',   30, '부품 조립 공정'),
('PRC-004', '검사',   15, '완제품 검사 공정'),
('PRC-005', '포장',    5, '출하 포장 공정')
ON CONFLICT (process_code) DO NOTHING;

-- 설비
INSERT INTO equipments (equip_code, name, process_code, capacity_per_hour, status, install_date) VALUES
('EQP-001', '절단기A',   'PRC-001', 120, 'RUNNING', '2024-01-15'),
('EQP-002', 'CNC선반B',  'PRC-002',  80, 'RUNNING', '2024-03-20'),
('EQP-003', '조립라인C', 'PRC-003',  60, 'STOP',    '2024-06-01'),
('EQP-004', '검사장비D', 'PRC-004', 200, 'RUNNING', '2024-07-10'),
('EQP-005', '포장기E',   'PRC-005', 150, 'RUNNING', '2024-09-01')
ON CONFLICT (equip_code) DO NOTHING;

-- 공정-설비 FK 업데이트
UPDATE processes SET equip_code = 'EQP-001' WHERE process_code = 'PRC-001';
UPDATE processes SET equip_code = 'EQP-002' WHERE process_code = 'PRC-002';
UPDATE processes SET equip_code = 'EQP-003' WHERE process_code = 'PRC-003';
UPDATE processes SET equip_code = 'EQP-004' WHERE process_code = 'PRC-004';
UPDATE processes SET equip_code = 'EQP-005' WHERE process_code = 'PRC-005';

-- BOM (완제품C: 원자재A 3개 + 반제품B 2개)
INSERT INTO bom (parent_item, child_item, qty_per_unit, loss_rate) VALUES
('ITEM003', 'ITEM001', 3.0, 2.0),
('ITEM003', 'ITEM002', 2.0, 1.5),
('ITEM005', 'ITEM003', 2.0, 1.0),
('ITEM005', 'ITEM004', 1.0, 0.5)
ON CONFLICT (parent_item, child_item) DO NOTHING;

-- 라우팅 (ITEM003: 절단→가공→조립→검사)
INSERT INTO routings (item_code, seq, process_code, cycle_time) VALUES
('ITEM003', 1, 'PRC-001', 10),
('ITEM003', 2, 'PRC-002', 20),
('ITEM003', 3, 'PRC-003', 30),
('ITEM003', 4, 'PRC-004', 15),
('ITEM005', 1, 'PRC-003', 25),
('ITEM005', 2, 'PRC-004', 15),
('ITEM005', 3, 'PRC-005',  5)
ON CONFLICT (item_code, seq) DO NOTHING;

-- 생산 계획
INSERT INTO production_plans (item_code, plan_qty, due_date, priority, status) VALUES
('ITEM003', 100, '2026-02-01', 'HIGH', 'DONE'),
('ITEM005', 200, '2026-02-15', 'HIGH', 'PROGRESS'),
('ITEM003', 150, '2026-03-01', 'MID',  'WAIT'),
('ITEM005', 100, '2026-03-15', 'LOW',  'WAIT')
ON CONFLICT DO NOTHING;

-- 작업 지시
INSERT INTO work_orders (wo_id, plan_id, item_code, work_date, equip_code, plan_qty, status) VALUES
('WO-20260201-001', 1, 'ITEM003', '2026-02-01', 'EQP-001', 100, 'DONE'),
('WO-20260210-001', 2, 'ITEM005', '2026-02-10', 'EQP-003', 200, 'WORKING'),
('WO-20260210-002', 2, 'ITEM005', '2026-02-11', 'EQP-003', 100, 'WAIT')
ON CONFLICT (wo_id) DO NOTHING;

-- 작업 실적
INSERT INTO work_results (wo_id, good_qty, defect_qty, defect_code, worker_id, start_time, end_time) VALUES
('WO-20260201-001', 95, 5, 'DEF-VISUAL', 'worker01', '2026-02-01 08:00:00', '2026-02-01 17:00:00'),
('WO-20260210-001', 80, 3, NULL,          'worker01', '2026-02-10 08:00:00', '2026-02-10 12:00:00')
ON CONFLICT DO NOTHING;

-- 불량 코드
INSERT INTO defect_codes (defect_code, name, description) VALUES
('DEF-VISUAL',  '외관불량', '스크래치, 변색 등 외관 결함'),
('DEF-DIMEN',   '치수불량', '규격 치수 이탈'),
('DEF-FUNC',    '기능불량', '작동 불량'),
('DEF-MATERIAL','소재불량', '원자재 자체 결함')
ON CONFLICT (defect_code) DO NOTHING;

-- 품질 검사 기준 (ITEM003)
INSERT INTO quality_standards (item_code, check_name, check_type, std_value, min_value, max_value, unit) VALUES
('ITEM003', '외관검사',   'VISUAL',    NULL,  NULL,  NULL,  NULL),
('ITEM003', '길이',       'NUMERIC',   50.0,  49.5,  50.5,  'mm'),
('ITEM003', '무게',       'NUMERIC',  120.0, 118.0, 122.0,  'g'),
('ITEM005', '외관검사',   'VISUAL',    NULL,  NULL,  NULL,  NULL),
('ITEM005', '조립정밀도', 'NUMERIC',   10.0,   9.8,  10.2,  'mm')
ON CONFLICT DO NOTHING;

-- 재고
INSERT INTO inventory (item_code, lot_no, qty, warehouse, location) VALUES
('ITEM001', 'LOT-20260101-001', 500, 'WH01', 'A-01-01'),
('ITEM002', 'LOT-20260115-001', 200, 'WH01', 'B-01-01'),
('ITEM003', 'LOT-20260201-001',  95, 'WH02', 'C-01-01'),
('ITEM004', 'LOT-20260115-002', 150, 'WH01', 'B-02-01'),
('ITEM005', 'LOT-20260210-001',  80, 'WH02', 'C-02-01')
ON CONFLICT (item_code, lot_no, warehouse) DO NOTHING;

-- 출하 이력 (12개월 x 2개 품목)
INSERT INTO shipments (item_code, ship_date, qty, customer) VALUES
('ITEM003', '2025-02-15', 80,  'CustomerA'),
('ITEM003', '2025-03-15', 90,  'CustomerA'),
('ITEM003', '2025-04-15', 85,  'CustomerB'),
('ITEM003', '2025-05-15', 100, 'CustomerA'),
('ITEM003', '2025-06-15', 95,  'CustomerB'),
('ITEM003', '2025-07-15', 110, 'CustomerA'),
('ITEM003', '2025-08-15', 105, 'CustomerB'),
('ITEM003', '2025-09-15', 120, 'CustomerA'),
('ITEM003', '2025-10-15', 115, 'CustomerB'),
('ITEM003', '2025-11-15', 130, 'CustomerA'),
('ITEM003', '2025-12-15', 125, 'CustomerB'),
('ITEM003', '2026-01-15', 140, 'CustomerA'),
('ITEM005', '2025-02-15', 150, 'CustomerC'),
('ITEM005', '2025-03-15', 160, 'CustomerC'),
('ITEM005', '2025-04-15', 155, 'CustomerD'),
('ITEM005', '2025-05-15', 170, 'CustomerC'),
('ITEM005', '2025-06-15', 165, 'CustomerD'),
('ITEM005', '2025-07-15', 180, 'CustomerC'),
('ITEM005', '2025-08-15', 175, 'CustomerD'),
('ITEM005', '2025-09-15', 190, 'CustomerC'),
('ITEM005', '2025-10-15', 185, 'CustomerD'),
('ITEM005', '2025-11-15', 200, 'CustomerC'),
('ITEM005', '2025-12-15', 195, 'CustomerD'),
('ITEM005', '2026-01-15', 210, 'CustomerC')
ON CONFLICT DO NOTHING;

-- 불량 이력 (불량 예측 학습 데이터)
INSERT INTO defect_history (item_code, equip_code, recorded_at, temperature, pressure, speed, humidity, defect_count, total_count) VALUES
('ITEM003', 'EQP-001', '2026-01-15 10:00:00', 200.0, 10.0, 50.0, 60.0, 2,  100),
('ITEM003', 'EQP-001', '2026-01-16 10:00:00', 225.0, 10.5, 50.0, 65.0, 8,  100),
('ITEM003', 'EQP-001', '2026-01-17 10:00:00', 195.0, 9.5,  48.0, 55.0, 1,  100),
('ITEM003', 'EQP-001', '2026-01-18 10:00:00', 230.0, 13.0, 58.0, 75.0, 15, 100),
('ITEM005', 'EQP-002', '2026-01-15 10:00:00', 210.0, 11.0, 52.0, 62.0, 3,  100),
('ITEM005', 'EQP-002', '2026-01-16 10:00:00', 205.0, 10.0, 50.0, 58.0, 2,  100),
('ITEM005', 'EQP-002', '2026-01-17 10:00:00', 240.0, 14.0, 60.0, 80.0, 20, 100),
('ITEM005', 'EQP-002', '2026-01-18 10:00:00', 198.0, 9.8,  49.0, 57.0, 1,  100)
ON CONFLICT DO NOTHING;

-- 설비 센서 데이터 (AI 고장 예측용)
INSERT INTO equip_sensors (equip_code, vibration, temperature, current_amp, recorded_at) VALUES
('EQP-001', 1.2, 45.0, 12.5, '2026-02-10 08:00:00'),
('EQP-001', 1.3, 46.0, 12.8, '2026-02-10 09:00:00'),
('EQP-001', 2.1, 55.0, 14.2, '2026-02-10 10:00:00'),
('EQP-001', 3.5, 68.0, 16.0, '2026-02-10 11:00:00'),
('EQP-002', 0.8, 40.0, 10.0, '2026-02-10 08:00:00'),
('EQP-002', 0.9, 41.0, 10.2, '2026-02-10 09:00:00'),
('EQP-002', 1.0, 42.0, 10.5, '2026-02-10 10:00:00'),
('EQP-003', 4.2, 72.0, 18.5, '2026-02-10 08:00:00'),
('EQP-003', 4.8, 78.0, 19.2, '2026-02-10 09:00:00'),
('EQP-003', 5.5, 85.0, 21.0, '2026-02-10 10:00:00')
ON CONFLICT DO NOTHING;

-- 설비 상태 이력
INSERT INTO equip_status_log (equip_code, status, reason, worker_id, changed_at) VALUES
('EQP-001', 'RUNNING', '정상 가동',        'worker01', '2026-02-10 08:00:00'),
('EQP-003', 'DOWN',    '모터 과열 고장',   'worker01', '2026-02-10 10:30:00'),
('EQP-003', 'STOP',    '정비 후 대기',     'worker01', '2026-02-10 14:00:00')
ON CONFLICT DO NOTHING;
