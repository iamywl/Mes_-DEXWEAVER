-- =============================================================
-- MES Database Schema (v4.0) - Full System + Massive Seed Data
-- Requirements_Specification + DatabaseSchema.md 기반
-- =============================================================

-- ─── 1. 사용자 ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id    VARCHAR(50) PRIMARY KEY,
    password   VARCHAR(255) NOT NULL,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(200),
    role       VARCHAR(20) NOT NULL DEFAULT 'worker'
                   CHECK (role IN ('admin','manager','worker','viewer')),
    is_approved BOOLEAN NOT NULL DEFAULT TRUE,
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

ALTER TABLE processes DROP CONSTRAINT IF EXISTS fk_proc_equip;
ALTER TABLE processes ADD CONSTRAINT fk_proc_equip
    FOREIGN KEY (equip_code) REFERENCES equipments(equip_code);
ALTER TABLE equipments DROP CONSTRAINT IF EXISTS fk_equip_proc;
ALTER TABLE equipments ADD CONSTRAINT fk_equip_proc
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
-- ██  MASSIVE SEED DATA  ██
-- =============================================================

-- ── 사용자 (10명) ───────────────────────────────────────────
INSERT INTO users (user_id, password, name, email, role) VALUES
('admin',    '$2b$12$qFMMFhvNO90wit48INExI.uzSH2O3rYzQR.6FsXBaBQomXOssEzQm', '시스템관리자', 'admin@knu.ac.kr',   'admin'),
('mgr01',    '$2b$12$eOl2oHfSFzGPfcCjZyXiGuwQZahVWdel1V1swpFuRfGh1AByfu5LS', '김생산부장',   'mgr01@knu.ac.kr',   'admin'),
('mgr02',    '$2b$12$eOl2oHfSFzGPfcCjZyXiGuwQZahVWdel1V1swpFuRfGh1AByfu5LS', '이품질팀장',   'mgr02@knu.ac.kr',   'admin'),
('worker01', '$2b$12$15Guq.8IsiZLM4auWMkl1OwhsbDZGC32NXCDG4O6FOUsFyGJOq7A.', '박작업자',     'w01@knu.ac.kr',     'worker'),
('worker02', '$2b$12$15Guq.8IsiZLM4auWMkl1OwhsbDZGC32NXCDG4O6FOUsFyGJOq7A.', '최기술자',     'w02@knu.ac.kr',     'worker'),
('worker03', '$2b$12$15Guq.8IsiZLM4auWMkl1OwhsbDZGC32NXCDG4O6FOUsFyGJOq7A.', '정조립공',     'w03@knu.ac.kr',     'worker'),
('worker04', '$2b$12$15Guq.8IsiZLM4auWMkl1OwhsbDZGC32NXCDG4O6FOUsFyGJOq7A.', '한검사원',     'w04@knu.ac.kr',     'worker'),
('worker05', '$2b$12$15Guq.8IsiZLM4auWMkl1OwhsbDZGC32NXCDG4O6FOUsFyGJOq7A.', '강포장원',     'w05@knu.ac.kr',     'worker'),
('viewer01', '$2b$12$8uQqO4eDD6D.Qz4jS/PUZeYD3mDJKfN23rGkFVspNqwkEAgfQnj5S', '조회전용A',    'v01@knu.ac.kr',     'viewer'),
('viewer02', '$2b$12$8uQqO4eDD6D.Qz4jS/PUZeYD3mDJKfN23rGkFVspNqwkEAgfQnj5S', '조회전용B',    'v02@knu.ac.kr',     'viewer')
ON CONFLICT (user_id) DO UPDATE SET password = EXCLUDED.password;

INSERT INTO user_permissions (user_id, menu, can_read, can_write) VALUES
('admin',    'ALL',              TRUE, TRUE),
('mgr01',    'ALL',              TRUE, TRUE),
('mgr02',    'QUALITY',          TRUE, TRUE),
('mgr02',    'REPORTS',          TRUE, TRUE),
('mgr02',    'DASHBOARD',        TRUE, FALSE),
('worker01', 'PRODUCTION_PLAN',  TRUE, TRUE),
('worker01', 'WORK_ORDER',       TRUE, TRUE),
('worker01', 'INVENTORY',        TRUE, TRUE),
('worker02', 'WORK_ORDER',       TRUE, TRUE),
('worker02', 'EQUIPMENT',        TRUE, TRUE),
('worker03', 'WORK_ORDER',       TRUE, TRUE),
('worker03', 'QUALITY',          TRUE, FALSE),
('worker04', 'QUALITY',          TRUE, TRUE),
('worker04', 'WORK_ORDER',       TRUE, FALSE),
('worker05', 'INVENTORY',        TRUE, TRUE),
('worker05', 'WORK_ORDER',       TRUE, FALSE),
('viewer01', 'DASHBOARD',        TRUE, FALSE),
('viewer01', 'REPORTS',          TRUE, FALSE),
('viewer02', 'DASHBOARD',        TRUE, FALSE),
('viewer02', 'INVENTORY',        TRUE, FALSE)
ON CONFLICT (user_id, menu) DO NOTHING;

-- ── 품목 마스터 (20개) ──────────────────────────────────────
INSERT INTO items (item_code, name, category, unit, spec, safety_stock) VALUES
-- 원자재 (8개)
('ITEM001', '스테인리스강판',  'RAW',     'KG',  'SUS304 두께2mm',         500),
('ITEM002', '알루미늄봉',      'RAW',     'KG',  'AL6061 Φ10mm',          300),
('ITEM003', '구리와이어',      'RAW',     'M',   'Cu99.9% Φ0.5mm',       1000),
('ITEM004', '플라스틱펠릿',    'RAW',     'KG',  'ABS수지 내열80도',       200),
('ITEM005', '고무시트',        'RAW',     'M',   'NBR 두께3mm',           150),
('ITEM006', '전자부품A',       'RAW',     'EA',  'IC칩 STM32F103',        500),
('ITEM007', '볼트너트세트',    'RAW',     'SET', 'M6x20 SUS304',          800),
('ITEM008', '실리콘오링',      'RAW',     'EA',  'Φ15 내열200도',         600),
-- 반제품 (6개)
('ITEM009', '금속프레임',      'SEMI',    'EA',  '절단+벤딩 완료',         100),
('ITEM010', 'CNC가공부품',     'SEMI',    'EA',  '정밀가공 공차0.01mm',     80),
('ITEM011', '사출성형품',      'SEMI',    'EA',  'ABS케이스 250x150x50',   120),
('ITEM012', '와이어하네스',    'SEMI',    'EA',  '커넥터+케이블 조립',       60),
('ITEM013', '도금부품',        'SEMI',    'EA',  '니켈도금 0.01mm',         90),
('ITEM014', '프레스부품',      'SEMI',    'EA',  '프레스금형 스탬핑',       150),
-- 완제품 (6개)
('ITEM015', '전자제어장치',    'PRODUCT', 'EA',  'ECU 모델A v2.1',          30),
('ITEM016', '유압밸브어셈블리','PRODUCT', 'EA',  '4포트 24V',               25),
('ITEM017', '센서모듈',        'PRODUCT', 'EA',  '온도+압력 복합센서',       40),
('ITEM018', '모터드라이버',    'PRODUCT', 'EA',  'BLDC 48V 500W',           20),
('ITEM019', '산업용커넥터',    'PRODUCT', 'EA',  '방수IP67 12핀',           50),
('ITEM020', '제어패널',        'PRODUCT', 'EA',  'HMI 7인치 터치',          15)
ON CONFLICT (item_code) DO NOTHING;

-- ── 공정 (10개) ─────────────────────────────────────────────
INSERT INTO processes (process_code, name, std_time_min, description) VALUES
('PRC-001', '절단',     10, '원자재 절단 (레이저/워터젯/프레스)'),
('PRC-002', 'CNC가공',  25, 'CNC선반/밀링 정밀가공'),
('PRC-003', '프레스',    8, '프레스 금형 스탬핑'),
('PRC-004', '열처리',   45, '담금질/뜨임/어닐링'),
('PRC-005', '도금',     30, '전기도금 (니켈/크롬/아연)'),
('PRC-006', '사출성형', 12, '플라스틱 사출 성형'),
('PRC-007', '조립1',    20, '기계부품 조립'),
('PRC-008', '조립2',    35, '전자부품+기계부품 최종조립'),
('PRC-009', '검사',     15, 'QC 검사 (외관/치수/기능)'),
('PRC-010', '포장',      5, '출하 포장 및 라벨링')
ON CONFLICT (process_code) DO NOTHING;

-- ── 설비 (15개) ─────────────────────────────────────────────
INSERT INTO equipments (equip_code, name, process_code, capacity_per_hour, status, install_date) VALUES
('EQP-001', '레이저절단기A',    'PRC-001', 120, 'RUNNING', '2023-03-15'),
('EQP-002', '워터젯절단기B',    'PRC-001',  80, 'RUNNING', '2023-06-20'),
('EQP-003', 'CNC선반-001',      'PRC-002',  60, 'RUNNING', '2023-01-10'),
('EQP-004', 'CNC밀링-001',      'PRC-002',  50, 'RUNNING', '2023-04-15'),
('EQP-005', '유압프레스500T',   'PRC-003', 200, 'RUNNING', '2022-11-01'),
('EQP-006', '유압프레스200T',   'PRC-003', 300, 'RUNNING', '2023-08-20'),
('EQP-007', '열처리로A',        'PRC-004',  30, 'RUNNING', '2022-06-15'),
('EQP-008', '전기도금조A',      'PRC-005',  40, 'STOP',    '2023-02-28'),
('EQP-009', '사출기350T',       'PRC-006', 150, 'RUNNING', '2023-09-10'),
('EQP-010', '사출기180T',       'PRC-006', 200, 'RUNNING', '2024-01-15'),
('EQP-011', '조립라인A',        'PRC-007',  45, 'RUNNING', '2023-05-01'),
('EQP-012', '조립라인B',        'PRC-008',  30, 'RUNNING', '2023-07-20'),
('EQP-013', 'SMT라인',          'PRC-008',  80, 'DOWN',    '2024-03-01'),
('EQP-014', '3차원측정기',      'PRC-009', 100, 'RUNNING', '2023-10-15'),
('EQP-015', '자동포장기',       'PRC-010', 250, 'RUNNING', '2024-02-01')
ON CONFLICT (equip_code) DO NOTHING;

-- 공정-설비 FK 업데이트
UPDATE processes SET equip_code = 'EQP-001' WHERE process_code = 'PRC-001';
UPDATE processes SET equip_code = 'EQP-003' WHERE process_code = 'PRC-002';
UPDATE processes SET equip_code = 'EQP-005' WHERE process_code = 'PRC-003';
UPDATE processes SET equip_code = 'EQP-007' WHERE process_code = 'PRC-004';
UPDATE processes SET equip_code = 'EQP-008' WHERE process_code = 'PRC-005';
UPDATE processes SET equip_code = 'EQP-009' WHERE process_code = 'PRC-006';
UPDATE processes SET equip_code = 'EQP-011' WHERE process_code = 'PRC-007';
UPDATE processes SET equip_code = 'EQP-012' WHERE process_code = 'PRC-008';
UPDATE processes SET equip_code = 'EQP-014' WHERE process_code = 'PRC-009';
UPDATE processes SET equip_code = 'EQP-015' WHERE process_code = 'PRC-010';

-- ── BOM (20개) ──────────────────────────────────────────────
INSERT INTO bom (parent_item, child_item, qty_per_unit, loss_rate) VALUES
-- 금속프레임 = 스테인리스강판 2kg + 볼트너트 4set
('ITEM009', 'ITEM001', 2.0,  3.0),
('ITEM009', 'ITEM007', 4.0,  1.0),
-- CNC가공부품 = 알루미늄봉 1.5kg
('ITEM010', 'ITEM002', 1.5,  5.0),
-- 사출성형품 = 플라스틱펠릿 0.8kg
('ITEM011', 'ITEM004', 0.8,  2.0),
-- 와이어하네스 = 구리와이어 3m + 전자부품A 2ea
('ITEM012', 'ITEM003', 3.0,  1.5),
('ITEM012', 'ITEM006', 2.0,  0.5),
-- 도금부품 = 금속프레임 1ea
('ITEM013', 'ITEM009', 1.0,  2.0),
-- 프레스부품 = 스테인리스강판 0.5kg
('ITEM014', 'ITEM001', 0.5,  4.0),
-- 전자제어장치 = CNC가공부품1 + 사출성형품1 + 와이어하네스1 + 전자부품A 5ea + 볼트너트 8set
('ITEM015', 'ITEM010', 1.0,  1.0),
('ITEM015', 'ITEM011', 1.0,  0.5),
('ITEM015', 'ITEM012', 1.0,  1.0),
('ITEM015', 'ITEM006', 5.0,  0.5),
('ITEM015', 'ITEM007', 8.0,  1.0),
-- 유압밸브어셈블리 = 도금부품2 + 고무시트0.5m + 프레스부품3 + 볼트너트6
('ITEM016', 'ITEM013', 2.0,  1.5),
('ITEM016', 'ITEM005', 0.5,  3.0),
('ITEM016', 'ITEM014', 3.0,  2.0),
('ITEM016', 'ITEM007', 6.0,  1.0),
-- 센서모듈 = 전자부품A 3ea + 사출성형품1 + 실리콘오링2
('ITEM017', 'ITEM006', 3.0,  1.0),
('ITEM017', 'ITEM011', 1.0,  0.5),
('ITEM017', 'ITEM008', 2.0,  1.0)
ON CONFLICT (parent_item, child_item) DO NOTHING;

-- ── 라우팅 ──────────────────────────────────────────────────
INSERT INTO routings (item_code, seq, process_code, cycle_time) VALUES
-- 금속프레임: 절단 → 프레스 → 열처리
('ITEM009', 1, 'PRC-001', 10),
('ITEM009', 2, 'PRC-003',  8),
('ITEM009', 3, 'PRC-004', 45),
-- CNC가공부품: 절단 → CNC가공 → 검사
('ITEM010', 1, 'PRC-001',  8),
('ITEM010', 2, 'PRC-002', 25),
('ITEM010', 3, 'PRC-009', 10),
-- 사출성형품: 사출성형 → 검사
('ITEM011', 1, 'PRC-006', 12),
('ITEM011', 2, 'PRC-009',  5),
-- 와이어하네스: 절단 → 조립1 → 검사
('ITEM012', 1, 'PRC-001',  5),
('ITEM012', 2, 'PRC-007', 20),
('ITEM012', 3, 'PRC-009',  8),
-- 도금부품: 도금 → 검사
('ITEM013', 1, 'PRC-005', 30),
('ITEM013', 2, 'PRC-009', 10),
-- 프레스부품: 프레스 → 열처리 → 검사
('ITEM014', 1, 'PRC-003',  8),
('ITEM014', 2, 'PRC-004', 30),
('ITEM014', 3, 'PRC-009',  8),
-- 전자제어장치: 조립1 → 조립2(SMT) → 검사 → 포장
('ITEM015', 1, 'PRC-007', 20),
('ITEM015', 2, 'PRC-008', 35),
('ITEM015', 3, 'PRC-009', 15),
('ITEM015', 4, 'PRC-010',  5),
-- 유압밸브: 조립1 → 검사 → 포장
('ITEM016', 1, 'PRC-007', 25),
('ITEM016', 2, 'PRC-009', 15),
('ITEM016', 3, 'PRC-010',  5),
-- 센서모듈: 조립2 → 검사 → 포장
('ITEM017', 1, 'PRC-008', 30),
('ITEM017', 2, 'PRC-009', 12),
('ITEM017', 3, 'PRC-010',  5),
-- 모터드라이버: 조립1 → 조립2 → 검사 → 포장
('ITEM018', 1, 'PRC-007', 20),
('ITEM018', 2, 'PRC-008', 40),
('ITEM018', 3, 'PRC-009', 15),
('ITEM018', 4, 'PRC-010',  5),
-- 산업용커넥터: 사출 → 도금 → 조립2 → 검사 → 포장
('ITEM019', 1, 'PRC-006', 10),
('ITEM019', 2, 'PRC-005', 25),
('ITEM019', 3, 'PRC-008', 20),
('ITEM019', 4, 'PRC-009', 10),
('ITEM019', 5, 'PRC-010',  5),
-- 제어패널: 절단 → CNC가공 → 조립1 → 조립2 → 검사 → 포장
('ITEM020', 1, 'PRC-001', 12),
('ITEM020', 2, 'PRC-002', 30),
('ITEM020', 3, 'PRC-007', 25),
('ITEM020', 4, 'PRC-008', 45),
('ITEM020', 5, 'PRC-009', 20),
('ITEM020', 6, 'PRC-010',  5)
ON CONFLICT (item_code, seq) DO NOTHING;

-- ── 불량 코드 (8개) ─────────────────────────────────────────
INSERT INTO defect_codes (defect_code, name, description) VALUES
('DEF-VISUAL',   '외관불량',   '스크래치, 변색, 찍힘 등 외관 결함'),
('DEF-DIMEN',    '치수불량',   '규격 치수 이탈 (공차 초과)'),
('DEF-FUNC',     '기능불량',   '작동 불량, 성능 미달'),
('DEF-MATERIAL', '소재불량',   '원자재 자체 결함 (기포, 크랙)'),
('DEF-ASSEMBLY', '조립불량',   '부품 오조립, 나사 풀림, 갭 불량'),
('DEF-PLATING',  '도금불량',   '도금 박리, 얼룩, 두께 부족'),
('DEF-WELD',     '용접불량',   '용접 비드 불량, 기공, 언더컷'),
('DEF-ELEC',     '전기불량',   '단선, 합선, 절연저항 미달')
ON CONFLICT (defect_code) DO NOTHING;

-- ── 품질 검사 기준 (30개) ───────────────────────────────────
INSERT INTO quality_standards (item_code, check_name, check_type, std_value, min_value, max_value, unit) VALUES
('ITEM009', '프레임길이',   'NUMERIC',  300.0, 299.5, 300.5, 'mm'),
('ITEM009', '프레임폭',     'NUMERIC',  150.0, 149.5, 150.5, 'mm'),
('ITEM009', '외관검사',     'VISUAL',    NULL,  NULL,  NULL,  NULL),
('ITEM010', '외경',         'NUMERIC',   10.0,   9.99, 10.01, 'mm'),
('ITEM010', '표면조도',     'NUMERIC',    1.6,   0.0,   1.6,  'Ra'),
('ITEM010', '진원도',       'NUMERIC',    0.005, 0.0,   0.005,'mm'),
('ITEM011', '외관검사',     'VISUAL',    NULL,  NULL,  NULL,  NULL),
('ITEM011', '무게',         'NUMERIC',  120.0, 118.0, 122.0, 'g'),
('ITEM011', '두께',         'NUMERIC',    2.5,   2.3,   2.7, 'mm'),
('ITEM012', '저항',         'NUMERIC',    0.5,   0.0,   1.0, 'Ω'),
('ITEM012', '절연저항',     'NUMERIC',  500.0, 100.0,  NULL, 'MΩ'),
('ITEM013', '도금두께',     'NUMERIC',   10.0,   8.0,  12.0, 'μm'),
('ITEM013', '외관검사',     'VISUAL',    NULL,  NULL,  NULL,  NULL),
('ITEM014', '길이',         'NUMERIC',   50.0,  49.8,  50.2, 'mm'),
('ITEM014', '평탄도',       'NUMERIC',    0.1,   0.0,   0.1, 'mm'),
('ITEM015', '전압출력',     'NUMERIC',    5.0,   4.9,   5.1, 'V'),
('ITEM015', '소비전력',     'NUMERIC',   12.0,   0.0,  15.0, 'W'),
('ITEM015', '기능검사',     'FUNCTIONAL', NULL,  NULL,  NULL,  NULL),
('ITEM016', '내압시험',     'NUMERIC',   35.0,  30.0,   NULL, 'MPa'),
('ITEM016', '누설검사',     'NUMERIC',    0.0,   NULL,   0.1, 'cc/min'),
('ITEM016', '외관검사',     'VISUAL',    NULL,  NULL,  NULL,  NULL),
('ITEM017', '온도정확도',   'NUMERIC',    0.5,   0.0,   0.5, '℃'),
('ITEM017', '압력정확도',   'NUMERIC',    1.0,   0.0,   1.0, '%FS'),
('ITEM017', '기능검사',     'FUNCTIONAL', NULL,  NULL,  NULL,  NULL),
('ITEM018', '출력',         'NUMERIC',  500.0, 480.0, 520.0, 'W'),
('ITEM018', '효율',         'NUMERIC',   92.0,  90.0,  NULL, '%'),
('ITEM019', '삽발력',       'NUMERIC',    5.0,   3.0,   7.0, 'N'),
('ITEM019', '방수시험',     'FUNCTIONAL', NULL,  NULL,  NULL,  NULL),
('ITEM020', '화면밝기',     'NUMERIC',  400.0, 350.0,  NULL, 'cd/m2'),
('ITEM020', '터치응답',     'NUMERIC',   10.0,   0.0,  15.0, 'ms')
ON CONFLICT DO NOTHING;

-- ── 생산 계획 (25개) ────────────────────────────────────────
INSERT INTO production_plans (item_code, plan_qty, due_date, priority, status) VALUES
-- 2025-11 ~ 2025-12: 완료
('ITEM009', 500, '2025-11-15', 'HIGH', 'DONE'),
('ITEM010', 300, '2025-11-20', 'MID',  'DONE'),
('ITEM011', 400, '2025-11-25', 'HIGH', 'DONE'),
('ITEM015', 100, '2025-12-01', 'HIGH', 'DONE'),
('ITEM016',  80, '2025-12-10', 'MID',  'DONE'),
('ITEM017', 150, '2025-12-15', 'HIGH', 'DONE'),
('ITEM014', 600, '2025-12-20', 'MID',  'DONE'),
-- 2026-01: 완료
('ITEM009', 600, '2026-01-10', 'HIGH', 'DONE'),
('ITEM010', 400, '2026-01-15', 'HIGH', 'DONE'),
('ITEM011', 500, '2026-01-15', 'MID',  'DONE'),
('ITEM012', 200, '2026-01-20', 'MID',  'DONE'),
('ITEM015', 120, '2026-01-25', 'HIGH', 'DONE'),
('ITEM018',  60, '2026-01-28', 'HIGH', 'DONE'),
-- 2026-02: 진행중/대기
('ITEM009', 700, '2026-02-10', 'HIGH', 'DONE'),
('ITEM010', 350, '2026-02-12', 'HIGH', 'PROGRESS'),
('ITEM013', 250, '2026-02-14', 'MID',  'PROGRESS'),
('ITEM014', 800, '2026-02-15', 'HIGH', 'PROGRESS'),
('ITEM015', 150, '2026-02-20', 'HIGH', 'PROGRESS'),
('ITEM016', 100, '2026-02-22', 'MID',  'PROGRESS'),
('ITEM017', 200, '2026-02-25', 'HIGH', 'WAIT'),
('ITEM018',  80, '2026-02-28', 'MID',  'WAIT'),
('ITEM019', 300, '2026-02-28', 'LOW',  'WAIT'),
-- 2026-03: 대기
('ITEM015', 200, '2026-03-10', 'HIGH', 'WAIT'),
('ITEM020',  50, '2026-03-15', 'HIGH', 'WAIT'),
('ITEM016', 120, '2026-03-20', 'MID',  'WAIT')
ON CONFLICT DO NOTHING;

-- ── 작업 지시 (60개) ────────────────────────────────────────
INSERT INTO work_orders (wo_id, plan_id, item_code, work_date, equip_code, plan_qty, status) VALUES
-- 2025-11 계획들의 작업지시 (완료)
('WO-20251110-001', 1,  'ITEM009', '2025-11-10', 'EQP-001', 250, 'DONE'),
('WO-20251112-001', 1,  'ITEM009', '2025-11-12', 'EQP-002', 250, 'DONE'),
('WO-20251115-001', 2,  'ITEM010', '2025-11-15', 'EQP-003', 150, 'DONE'),
('WO-20251117-001', 2,  'ITEM010', '2025-11-17', 'EQP-004', 150, 'DONE'),
('WO-20251120-001', 3,  'ITEM011', '2025-11-20', 'EQP-009', 200, 'DONE'),
('WO-20251122-001', 3,  'ITEM011', '2025-11-22', 'EQP-010', 200, 'DONE'),
-- 2025-12 계획
('WO-20251125-001', 4,  'ITEM015', '2025-11-25', 'EQP-011',  50, 'DONE'),
('WO-20251128-001', 4,  'ITEM015', '2025-11-28', 'EQP-012',  50, 'DONE'),
('WO-20251201-001', 5,  'ITEM016', '2025-12-01', 'EQP-011',  40, 'DONE'),
('WO-20251203-001', 5,  'ITEM016', '2025-12-03', 'EQP-011',  40, 'DONE'),
('WO-20251205-001', 6,  'ITEM017', '2025-12-05', 'EQP-012',  75, 'DONE'),
('WO-20251208-001', 6,  'ITEM017', '2025-12-08', 'EQP-012',  75, 'DONE'),
('WO-20251210-001', 7,  'ITEM014', '2025-12-10', 'EQP-005', 300, 'DONE'),
('WO-20251215-001', 7,  'ITEM014', '2025-12-15', 'EQP-006', 300, 'DONE'),
-- 2026-01 계획
('WO-20260105-001', 8,  'ITEM009', '2026-01-05', 'EQP-001', 300, 'DONE'),
('WO-20260107-001', 8,  'ITEM009', '2026-01-07', 'EQP-002', 300, 'DONE'),
('WO-20260108-001', 9,  'ITEM010', '2026-01-08', 'EQP-003', 200, 'DONE'),
('WO-20260110-001', 9,  'ITEM010', '2026-01-10', 'EQP-004', 200, 'DONE'),
('WO-20260110-002', 10, 'ITEM011', '2026-01-10', 'EQP-009', 250, 'DONE'),
('WO-20260112-001', 10, 'ITEM011', '2026-01-12', 'EQP-010', 250, 'DONE'),
('WO-20260113-001', 11, 'ITEM012', '2026-01-13', 'EQP-011', 100, 'DONE'),
('WO-20260115-001', 11, 'ITEM012', '2026-01-15', 'EQP-011', 100, 'DONE'),
('WO-20260118-001', 12, 'ITEM015', '2026-01-18', 'EQP-012',  60, 'DONE'),
('WO-20260120-001', 12, 'ITEM015', '2026-01-20', 'EQP-012',  60, 'DONE'),
('WO-20260122-001', 13, 'ITEM018', '2026-01-22', 'EQP-011',  30, 'DONE'),
('WO-20260125-001', 13, 'ITEM018', '2026-01-25', 'EQP-012',  30, 'DONE'),
-- 2026-02 계획 (진행/대기)
('WO-20260203-001', 14, 'ITEM009', '2026-02-03', 'EQP-001', 350, 'DONE'),
('WO-20260205-001', 14, 'ITEM009', '2026-02-05', 'EQP-002', 350, 'DONE'),
('WO-20260206-001', 15, 'ITEM010', '2026-02-06', 'EQP-003', 175, 'DONE'),
('WO-20260208-001', 15, 'ITEM010', '2026-02-08', 'EQP-004', 175, 'WORKING'),
('WO-20260207-001', 16, 'ITEM013', '2026-02-07', 'EQP-008', 125, 'DONE'),
('WO-20260209-001', 16, 'ITEM013', '2026-02-09', 'EQP-008', 125, 'WORKING'),
('WO-20260205-002', 17, 'ITEM014', '2026-02-05', 'EQP-005', 400, 'DONE'),
('WO-20260208-002', 17, 'ITEM014', '2026-02-08', 'EQP-006', 400, 'WORKING'),
('WO-20260210-001', 18, 'ITEM015', '2026-02-10', 'EQP-011',  50, 'DONE'),
('WO-20260211-001', 18, 'ITEM015', '2026-02-11', 'EQP-012',  50, 'WORKING'),
('WO-20260212-001', 18, 'ITEM015', '2026-02-12', 'EQP-011',  50, 'WAIT'),
('WO-20260210-002', 19, 'ITEM016', '2026-02-10', 'EQP-011',  50, 'DONE'),
('WO-20260212-002', 19, 'ITEM016', '2026-02-12', 'EQP-011',  50, 'WORKING'),
-- 미래 작업 대기
('WO-20260215-001', 20, 'ITEM017', '2026-02-15', 'EQP-012', 100, 'WAIT'),
('WO-20260218-001', 20, 'ITEM017', '2026-02-18', 'EQP-012', 100, 'WAIT'),
('WO-20260220-001', 21, 'ITEM018', '2026-02-20', 'EQP-011',  40, 'WAIT'),
('WO-20260222-001', 21, 'ITEM018', '2026-02-22', 'EQP-012',  40, 'WAIT'),
('WO-20260225-001', 22, 'ITEM019', '2026-02-25', 'EQP-009', 150, 'WAIT'),
('WO-20260227-001', 22, 'ITEM019', '2026-02-27', 'EQP-010', 150, 'WAIT')
ON CONFLICT (wo_id) DO NOTHING;

-- ── 작업 실적 (75건) ────────────────────────────────────────
INSERT INTO work_results (wo_id, good_qty, defect_qty, defect_code, worker_id, start_time, end_time) VALUES
-- 2025-11 실적
('WO-20251110-001', 245,  5, 'DEF-VISUAL',   'worker01', '2025-11-10 08:00', '2025-11-10 17:00'),
('WO-20251112-001', 247,  3, 'DEF-DIMEN',    'worker02', '2025-11-12 08:00', '2025-11-12 17:00'),
('WO-20251115-001', 146,  4, 'DEF-DIMEN',    'worker02', '2025-11-15 08:00', '2025-11-15 17:00'),
('WO-20251117-001', 148,  2, NULL,            'worker02', '2025-11-17 08:00', '2025-11-17 17:00'),
('WO-20251120-001', 195,  5, 'DEF-MATERIAL', 'worker03', '2025-11-20 08:00', '2025-11-20 17:00'),
('WO-20251122-001', 198,  2, NULL,            'worker03', '2025-11-22 08:00', '2025-11-22 17:00'),
('WO-20251125-001',  48,  2, 'DEF-ASSEMBLY', 'worker03', '2025-11-25 08:00', '2025-11-25 17:00'),
('WO-20251128-001',  49,  1, NULL,            'worker03', '2025-11-28 08:00', '2025-11-28 17:00'),
-- 2025-12 실적
('WO-20251201-001',  38,  2, 'DEF-VISUAL',   'worker03', '2025-12-01 08:00', '2025-12-01 17:00'),
('WO-20251203-001',  39,  1, NULL,            'worker03', '2025-12-03 08:00', '2025-12-03 17:00'),
('WO-20251205-001',  72,  3, 'DEF-ELEC',     'worker04', '2025-12-05 08:00', '2025-12-05 17:00'),
('WO-20251208-001',  73,  2, 'DEF-FUNC',     'worker04', '2025-12-08 08:00', '2025-12-08 17:00'),
('WO-20251210-001', 290, 10, 'DEF-DIMEN',    'worker01', '2025-12-10 08:00', '2025-12-10 17:00'),
('WO-20251215-001', 294,  6, 'DEF-VISUAL',   'worker01', '2025-12-15 08:00', '2025-12-15 17:00'),
-- 2026-01 실적
('WO-20260105-001', 293,  7, 'DEF-VISUAL',   'worker01', '2026-01-05 08:00', '2026-01-05 17:00'),
('WO-20260107-001', 296,  4, 'DEF-DIMEN',    'worker02', '2026-01-07 08:00', '2026-01-07 17:00'),
('WO-20260108-001', 195,  5, 'DEF-DIMEN',    'worker02', '2026-01-08 08:00', '2026-01-08 17:00'),
('WO-20260110-001', 197,  3, NULL,            'worker02', '2026-01-10 08:00', '2026-01-10 17:00'),
('WO-20260110-002', 244,  6, 'DEF-MATERIAL', 'worker03', '2026-01-10 08:00', '2026-01-10 17:00'),
('WO-20260112-001', 248,  2, NULL,            'worker03', '2026-01-12 08:00', '2026-01-12 17:00'),
('WO-20260113-001',  96,  4, 'DEF-ASSEMBLY', 'worker03', '2026-01-13 08:00', '2026-01-13 17:00'),
('WO-20260115-001',  98,  2, NULL,            'worker03', '2026-01-15 08:00', '2026-01-15 17:00'),
('WO-20260118-001',  57,  3, 'DEF-ELEC',     'worker04', '2026-01-18 08:00', '2026-01-18 17:00'),
('WO-20260120-001',  58,  2, 'DEF-FUNC',     'worker04', '2026-01-20 08:00', '2026-01-20 17:00'),
('WO-20260122-001',  28,  2, 'DEF-ASSEMBLY', 'worker03', '2026-01-22 08:00', '2026-01-22 17:00'),
('WO-20260125-001',  29,  1, NULL,            'worker03', '2026-01-25 08:00', '2026-01-25 17:00'),
-- 2026-02 실적 (진행중 포함)
('WO-20260203-001', 340, 10, 'DEF-VISUAL',   'worker01', '2026-02-03 08:00', '2026-02-03 17:00'),
('WO-20260205-001', 343,  7, 'DEF-DIMEN',    'worker01', '2026-02-05 08:00', '2026-02-05 17:00'),
('WO-20260206-001', 170,  5, 'DEF-DIMEN',    'worker02', '2026-02-06 08:00', '2026-02-06 17:00'),
('WO-20260208-001', 100,  3, NULL,            'worker02', '2026-02-08 08:00', '2026-02-08 12:00'),
('WO-20260207-001', 120,  5, 'DEF-PLATING',  'worker04', '2026-02-07 08:00', '2026-02-07 17:00'),
('WO-20260209-001',  80,  3, 'DEF-PLATING',  'worker04', '2026-02-09 08:00', '2026-02-09 14:00'),
('WO-20260205-002', 388, 12, 'DEF-DIMEN',    'worker01', '2026-02-05 08:00', '2026-02-05 17:00'),
('WO-20260208-002', 250,  8, 'DEF-VISUAL',   'worker01', '2026-02-08 08:00', '2026-02-08 15:00'),
('WO-20260210-001',  48,  2, 'DEF-ELEC',     'worker03', '2026-02-10 08:00', '2026-02-10 17:00'),
('WO-20260211-001',  30,  1, NULL,            'worker03', '2026-02-11 08:00', '2026-02-11 14:00'),
('WO-20260210-002',  48,  2, 'DEF-ASSEMBLY', 'worker03', '2026-02-10 08:00', '2026-02-10 17:00'),
('WO-20260212-002',  25,  1, NULL,            'worker03', '2026-02-12 08:00', '2026-02-12 10:00'),
-- 추가 실적 (복수 실적/작업지시)
('WO-20251110-001',  48,  2, 'DEF-DIMEN',    'worker02', '2025-11-10 13:00', '2025-11-10 17:00'),
('WO-20251120-001',  96,  4, 'DEF-VISUAL',   'worker04', '2025-11-20 13:00', '2025-11-20 17:00'),
('WO-20251210-001', 145,  5, 'DEF-MATERIAL', 'worker02', '2025-12-11 08:00', '2025-12-11 17:00'),
('WO-20260105-001', 146,  4, 'DEF-WELD',     'worker02', '2026-01-06 08:00', '2026-01-06 17:00'),
('WO-20260110-002', 120,  5, 'DEF-VISUAL',   'worker04', '2026-01-11 08:00', '2026-01-11 17:00'),
('WO-20260203-001', 170,  5, 'DEF-DIMEN',    'worker02', '2026-02-04 08:00', '2026-02-04 17:00')
ON CONFLICT DO NOTHING;

-- ── 재고 (35개 로트) ────────────────────────────────────────
INSERT INTO inventory (item_code, lot_no, qty, warehouse, location) VALUES
-- 원자재
('ITEM001', 'LOT-20260101-001', 1200, 'WH01', 'A-01-01'),
('ITEM001', 'LOT-20260115-001',  800, 'WH01', 'A-01-02'),
('ITEM001', 'LOT-20260201-001',  500, 'WH01', 'A-01-03'),
('ITEM002', 'LOT-20260101-002',  600, 'WH01', 'A-02-01'),
('ITEM002', 'LOT-20260201-002',  400, 'WH01', 'A-02-02'),
('ITEM003', 'LOT-20260101-003', 2500, 'WH01', 'A-03-01'),
('ITEM003', 'LOT-20260201-003', 1500, 'WH01', 'A-03-02'),
('ITEM004', 'LOT-20260101-004',  350, 'WH01', 'A-04-01'),
('ITEM004', 'LOT-20260201-004',  250, 'WH01', 'A-04-02'),
('ITEM005', 'LOT-20260115-005',  300, 'WH01', 'A-05-01'),
('ITEM006', 'LOT-20260101-006', 1200, 'WH01', 'A-06-01'),
('ITEM006', 'LOT-20260201-006',  800, 'WH01', 'A-06-02'),
('ITEM007', 'LOT-20260101-007', 2000, 'WH01', 'A-07-01'),
('ITEM007', 'LOT-20260201-007', 1500, 'WH01', 'A-07-02'),
('ITEM008', 'LOT-20260115-008',  800, 'WH01', 'A-08-01'),
-- 반제품
('ITEM009', 'LOT-20260115-009',  180, 'WH02', 'B-01-01'),
('ITEM009', 'LOT-20260201-009',  250, 'WH02', 'B-01-02'),
('ITEM010', 'LOT-20260115-010',  120, 'WH02', 'B-02-01'),
('ITEM010', 'LOT-20260201-010',  200, 'WH02', 'B-02-02'),
('ITEM011', 'LOT-20260115-011',  150, 'WH02', 'B-03-01'),
('ITEM011', 'LOT-20260201-011',  280, 'WH02', 'B-03-02'),
('ITEM012', 'LOT-20260120-012',   90, 'WH02', 'B-04-01'),
('ITEM012', 'LOT-20260201-012',  100, 'WH02', 'B-04-02'),
('ITEM013', 'LOT-20260201-013',  180, 'WH02', 'B-05-01'),
('ITEM014', 'LOT-20260115-014',  200, 'WH02', 'B-06-01'),
('ITEM014', 'LOT-20260201-014',  350, 'WH02', 'B-06-02'),
-- 완제품
('ITEM015', 'LOT-20260120-015',   45, 'WH03', 'C-01-01'),
('ITEM015', 'LOT-20260201-015',   60, 'WH03', 'C-01-02'),
('ITEM016', 'LOT-20260120-016',   35, 'WH03', 'C-02-01'),
('ITEM016', 'LOT-20260201-016',   40, 'WH03', 'C-02-02'),
('ITEM017', 'LOT-20260120-017',   65, 'WH03', 'C-03-01'),
('ITEM017', 'LOT-20260201-017',   80, 'WH03', 'C-03-02'),
('ITEM018', 'LOT-20260125-018',   28, 'WH03', 'C-04-01'),
('ITEM019', 'LOT-20260115-019',   15, 'WH03', 'C-05-01'),
('ITEM020', 'LOT-20260115-020',    8, 'WH03', 'C-06-01')
ON CONFLICT (item_code, lot_no, warehouse) DO NOTHING;

-- ── 재고 이동 전표 (50건) ───────────────────────────────────
INSERT INTO inventory_transactions (slip_no, item_code, lot_no, qty, tx_type, warehouse, location, ref_id, supplier) VALUES
-- 입고
('IN-20260101-001', 'ITEM001', 'LOT-20260101-001', 1200, 'IN', 'WH01', 'A-01-01', NULL, '포스코'),
('IN-20260101-002', 'ITEM002', 'LOT-20260101-002',  600, 'IN', 'WH01', 'A-02-01', NULL, '노벨리스'),
('IN-20260101-003', 'ITEM003', 'LOT-20260101-003', 2500, 'IN', 'WH01', 'A-03-01', NULL, 'LS전선'),
('IN-20260101-004', 'ITEM004', 'LOT-20260101-004',  350, 'IN', 'WH01', 'A-04-01', NULL, 'LG화학'),
('IN-20260101-005', 'ITEM006', 'LOT-20260101-006', 1200, 'IN', 'WH01', 'A-06-01', NULL, 'ST마이크로'),
('IN-20260101-006', 'ITEM007', 'LOT-20260101-007', 2000, 'IN', 'WH01', 'A-07-01', NULL, '삼흥볼트'),
('IN-20260115-001', 'ITEM001', 'LOT-20260115-001',  800, 'IN', 'WH01', 'A-01-02', NULL, '포스코'),
('IN-20260115-002', 'ITEM005', 'LOT-20260115-005',  300, 'IN', 'WH01', 'A-05-01', NULL, '평화고무'),
('IN-20260115-003', 'ITEM008', 'LOT-20260115-008',  800, 'IN', 'WH01', 'A-08-01', NULL, '실리콘코리아'),
('IN-20260201-001', 'ITEM001', 'LOT-20260201-001',  500, 'IN', 'WH01', 'A-01-03', NULL, '포스코'),
('IN-20260201-002', 'ITEM002', 'LOT-20260201-002',  400, 'IN', 'WH01', 'A-02-02', NULL, '노벨리스'),
('IN-20260201-003', 'ITEM003', 'LOT-20260201-003', 1500, 'IN', 'WH01', 'A-03-02', NULL, 'LS전선'),
('IN-20260201-004', 'ITEM004', 'LOT-20260201-004',  250, 'IN', 'WH01', 'A-04-02', NULL, 'LG화학'),
('IN-20260201-005', 'ITEM006', 'LOT-20260201-006',  800, 'IN', 'WH01', 'A-06-02', NULL, 'ST마이크로'),
('IN-20260201-006', 'ITEM007', 'LOT-20260201-007', 1500, 'IN', 'WH01', 'A-07-02', NULL, '삼흥볼트'),
-- 반제품 입고 (생산 완료분)
('IN-20260115-010', 'ITEM009', 'LOT-20260115-009',  180, 'IN', 'WH02', 'B-01-01', 'WO-20260105-001', NULL),
('IN-20260115-011', 'ITEM010', 'LOT-20260115-010',  120, 'IN', 'WH02', 'B-02-01', 'WO-20260108-001', NULL),
('IN-20260115-012', 'ITEM011', 'LOT-20260115-011',  150, 'IN', 'WH02', 'B-03-01', 'WO-20260110-002', NULL),
('IN-20260120-010', 'ITEM012', 'LOT-20260120-012',   90, 'IN', 'WH02', 'B-04-01', 'WO-20260113-001', NULL),
('IN-20260201-010', 'ITEM009', 'LOT-20260201-009',  250, 'IN', 'WH02', 'B-01-02', 'WO-20260203-001', NULL),
('IN-20260201-011', 'ITEM010', 'LOT-20260201-010',  200, 'IN', 'WH02', 'B-02-02', 'WO-20260206-001', NULL),
('IN-20260201-012', 'ITEM011', 'LOT-20260201-011',  280, 'IN', 'WH02', 'B-03-02', 'WO-20260110-002', NULL),
('IN-20260201-013', 'ITEM012', 'LOT-20260201-012',  100, 'IN', 'WH02', 'B-04-02', 'WO-20260115-001', NULL),
('IN-20260201-014', 'ITEM013', 'LOT-20260201-013',  180, 'IN', 'WH02', 'B-05-01', 'WO-20260207-001', NULL),
('IN-20260201-015', 'ITEM014', 'LOT-20260201-014',  350, 'IN', 'WH02', 'B-06-02', 'WO-20260205-002', NULL),
-- 완제품 입고
('IN-20260120-020', 'ITEM015', 'LOT-20260120-015',   45, 'IN', 'WH03', 'C-01-01', 'WO-20260118-001', NULL),
('IN-20260120-021', 'ITEM016', 'LOT-20260120-016',   35, 'IN', 'WH03', 'C-02-01', 'WO-20251201-001', NULL),
('IN-20260120-022', 'ITEM017', 'LOT-20260120-017',   65, 'IN', 'WH03', 'C-03-01', 'WO-20251205-001', NULL),
('IN-20260125-020', 'ITEM018', 'LOT-20260125-018',   28, 'IN', 'WH03', 'C-04-01', 'WO-20260122-001', NULL),
('IN-20260201-020', 'ITEM015', 'LOT-20260201-015',   60, 'IN', 'WH03', 'C-01-02', 'WO-20260210-001', NULL),
('IN-20260201-021', 'ITEM016', 'LOT-20260201-016',   40, 'IN', 'WH03', 'C-02-02', 'WO-20260210-002', NULL),
('IN-20260201-022', 'ITEM017', 'LOT-20260201-017',   80, 'IN', 'WH03', 'C-03-02', 'WO-20260120-022', NULL),
-- 출고 (생산 투입)
('OUT-20260105-001', 'ITEM001', 'LOT-20260101-001',  600, 'OUT', 'WH01', 'A-01-01', 'WO-20260105-001', NULL),
('OUT-20260108-001', 'ITEM002', 'LOT-20260101-002',  300, 'OUT', 'WH01', 'A-02-01', 'WO-20260108-001', NULL),
('OUT-20260110-001', 'ITEM004', 'LOT-20260101-004',  200, 'OUT', 'WH01', 'A-04-01', 'WO-20260110-002', NULL),
('OUT-20260113-001', 'ITEM003', 'LOT-20260101-003',  300, 'OUT', 'WH01', 'A-03-01', 'WO-20260113-001', NULL),
('OUT-20260113-002', 'ITEM006', 'LOT-20260101-006',  200, 'OUT', 'WH01', 'A-06-01', 'WO-20260113-001', NULL),
('OUT-20260203-001', 'ITEM001', 'LOT-20260115-001',  700, 'OUT', 'WH01', 'A-01-02', 'WO-20260203-001', NULL),
('OUT-20260205-001', 'ITEM001', 'LOT-20260201-001',  400, 'OUT', 'WH01', 'A-01-03', 'WO-20260205-002', NULL),
-- 출하
('OUT-20260115-010', 'ITEM015', 'LOT-20260120-015',   20, 'OUT', 'WH03', 'C-01-01', 'SHIP-A', NULL),
('OUT-20260201-010', 'ITEM016', 'LOT-20260120-016',   15, 'OUT', 'WH03', 'C-02-01', 'SHIP-B', NULL),
('OUT-20260205-010', 'ITEM017', 'LOT-20260120-017',   30, 'OUT', 'WH03', 'C-03-01', 'SHIP-C', NULL),
('OUT-20260210-010', 'ITEM015', 'LOT-20260201-015',   25, 'OUT', 'WH03', 'C-01-02', 'SHIP-D', NULL),
-- 창고간이동
('MV-20260115-001', 'ITEM014', 'LOT-20260115-014',  100, 'MOVE', 'WH02', 'B-06-01', 'WH02→WH03', NULL),
('MV-20260201-001', 'ITEM009', 'LOT-20260115-009',   50, 'MOVE', 'WH02', 'B-01-01', 'WH02→WH03', NULL)
ON CONFLICT DO NOTHING;

-- ── 출하 이력 (24개월 x 6개 완제품 = 144건) ────────────────
INSERT INTO shipments (item_code, ship_date, qty, customer) VALUES
-- ITEM015 전자제어장치 (24개월)
('ITEM015', '2024-03-10',  40, '현대모비스'),   ('ITEM015', '2024-03-25',  35, '만도'),
('ITEM015', '2024-04-10',  45, '현대모비스'),   ('ITEM015', '2024-04-28',  38, 'LG전자'),
('ITEM015', '2024-05-12',  50, '현대모비스'),   ('ITEM015', '2024-05-27',  42, '만도'),
('ITEM015', '2024-06-10',  48, '현대모비스'),   ('ITEM015', '2024-06-25',  40, 'LG전자'),
('ITEM015', '2024-07-08',  55, '현대모비스'),   ('ITEM015', '2024-07-22',  45, '만도'),
('ITEM015', '2024-08-10',  52, '현대모비스'),   ('ITEM015', '2024-08-28',  48, 'LG전자'),
('ITEM015', '2024-09-10',  60, '현대모비스'),   ('ITEM015', '2024-09-25',  50, '만도'),
('ITEM015', '2024-10-10',  58, '현대모비스'),   ('ITEM015', '2024-10-28',  52, 'LG전자'),
('ITEM015', '2024-11-10',  65, '현대모비스'),   ('ITEM015', '2024-11-25',  55, '만도'),
('ITEM015', '2024-12-10',  62, '현대모비스'),   ('ITEM015', '2024-12-23',  58, 'LG전자'),
('ITEM015', '2025-01-10',  70, '현대모비스'),   ('ITEM015', '2025-01-27',  60, '만도'),
('ITEM015', '2025-02-10',  68, '현대모비스'),   ('ITEM015', '2025-02-25',  62, 'LG전자'),
('ITEM015', '2025-03-10',  75, '현대모비스'),   ('ITEM015', '2025-03-25',  65, '만도'),
('ITEM015', '2025-04-10',  72, '현대모비스'),   ('ITEM015', '2025-04-28',  68, 'LG전자'),
('ITEM015', '2025-05-12',  80, '현대모비스'),   ('ITEM015', '2025-05-27',  70, '만도'),
('ITEM015', '2025-06-10',  78, '현대모비스'),   ('ITEM015', '2025-06-25',  72, 'LG전자'),
('ITEM015', '2025-07-08',  85, '현대모비스'),   ('ITEM015', '2025-07-22',  75, '만도'),
('ITEM015', '2025-08-10',  82, '현대모비스'),   ('ITEM015', '2025-08-28',  78, 'LG전자'),
('ITEM015', '2025-09-10',  90, '현대모비스'),   ('ITEM015', '2025-09-25',  80, '만도'),
('ITEM015', '2025-10-10',  88, '현대모비스'),   ('ITEM015', '2025-10-28',  82, 'LG전자'),
('ITEM015', '2025-11-10',  95, '현대모비스'),   ('ITEM015', '2025-11-25',  85, '만도'),
('ITEM015', '2025-12-10',  92, '현대모비스'),   ('ITEM015', '2025-12-23',  88, 'LG전자'),
('ITEM015', '2026-01-10', 100, '현대모비스'),   ('ITEM015', '2026-01-27',  90, '만도'),
('ITEM015', '2026-02-10',  98, '현대모비스'),
-- ITEM016 유압밸브 (24개월)
('ITEM016', '2024-03-15',  30, '보쉬코리아'),   ('ITEM016', '2024-04-15',  35, '보쉬코리아'),
('ITEM016', '2024-05-15',  32, '파카하니핀'),   ('ITEM016', '2024-06-15',  38, '보쉬코리아'),
('ITEM016', '2024-07-15',  35, '파카하니핀'),   ('ITEM016', '2024-08-15',  40, '보쉬코리아'),
('ITEM016', '2024-09-15',  38, '파카하니핀'),   ('ITEM016', '2024-10-15',  42, '보쉬코리아'),
('ITEM016', '2024-11-15',  40, '파카하니핀'),   ('ITEM016', '2024-12-15',  45, '보쉬코리아'),
('ITEM016', '2025-01-15',  43, '파카하니핀'),   ('ITEM016', '2025-02-15',  48, '보쉬코리아'),
('ITEM016', '2025-03-15',  45, '파카하니핀'),   ('ITEM016', '2025-04-15',  50, '보쉬코리아'),
('ITEM016', '2025-05-15',  48, '파카하니핀'),   ('ITEM016', '2025-06-15',  52, '보쉬코리아'),
('ITEM016', '2025-07-15',  50, '파카하니핀'),   ('ITEM016', '2025-08-15',  55, '보쉬코리아'),
('ITEM016', '2025-09-15',  53, '파카하니핀'),   ('ITEM016', '2025-10-15',  58, '보쉬코리아'),
('ITEM016', '2025-11-15',  55, '파카하니핀'),   ('ITEM016', '2025-12-15',  60, '보쉬코리아'),
('ITEM016', '2026-01-15',  58, '파카하니핀'),   ('ITEM016', '2026-02-05',  62, '보쉬코리아'),
-- ITEM017 센서모듈 (24개월)
('ITEM017', '2024-03-20',  60, '삼성전자'),     ('ITEM017', '2024-04-20',  65, '삼성전자'),
('ITEM017', '2024-05-20',  62, 'LG이노텍'),     ('ITEM017', '2024-06-20',  70, '삼성전자'),
('ITEM017', '2024-07-20',  68, 'LG이노텍'),     ('ITEM017', '2024-08-20',  75, '삼성전자'),
('ITEM017', '2024-09-20',  72, 'LG이노텍'),     ('ITEM017', '2024-10-20',  78, '삼성전자'),
('ITEM017', '2024-11-20',  75, 'LG이노텍'),     ('ITEM017', '2024-12-20',  82, '삼성전자'),
('ITEM017', '2025-01-20',  80, 'LG이노텍'),     ('ITEM017', '2025-02-20',  85, '삼성전자'),
('ITEM017', '2025-03-20',  82, 'LG이노텍'),     ('ITEM017', '2025-04-20',  88, '삼성전자'),
('ITEM017', '2025-05-20',  85, 'LG이노텍'),     ('ITEM017', '2025-06-20',  92, '삼성전자'),
('ITEM017', '2025-07-20',  90, 'LG이노텍'),     ('ITEM017', '2025-08-20',  95, '삼성전자'),
('ITEM017', '2025-09-20',  92, 'LG이노텍'),     ('ITEM017', '2025-10-20',  98, '삼성전자'),
('ITEM017', '2025-11-20',  95, 'LG이노텍'),     ('ITEM017', '2025-12-20', 102, '삼성전자'),
('ITEM017', '2026-01-20', 100, 'LG이노텍'),     ('ITEM017', '2026-02-05', 105, '삼성전자'),
-- ITEM018 모터드라이버 (18개월)
('ITEM018', '2024-09-10',  20, '두산로보틱스'),  ('ITEM018', '2024-10-10',  22, '두산로보틱스'),
('ITEM018', '2024-11-10',  25, '현대로보틱스'),  ('ITEM018', '2024-12-10',  23, '두산로보틱스'),
('ITEM018', '2025-01-10',  28, '현대로보틱스'),  ('ITEM018', '2025-02-10',  26, '두산로보틱스'),
('ITEM018', '2025-03-10',  30, '현대로보틱스'),  ('ITEM018', '2025-04-10',  28, '두산로보틱스'),
('ITEM018', '2025-05-10',  32, '현대로보틱스'),  ('ITEM018', '2025-06-10',  30, '두산로보틱스'),
('ITEM018', '2025-07-10',  35, '현대로보틱스'),  ('ITEM018', '2025-08-10',  33, '두산로보틱스'),
('ITEM018', '2025-09-10',  38, '현대로보틱스'),  ('ITEM018', '2025-10-10',  36, '두산로보틱스'),
('ITEM018', '2025-11-10',  40, '현대로보틱스'),  ('ITEM018', '2025-12-10',  38, '두산로보틱스'),
('ITEM018', '2026-01-10',  42, '현대로보틱스'),  ('ITEM018', '2026-02-05',  40, '두산로보틱스'),
-- ITEM019 산업용커넥터 (12개월)
('ITEM019', '2025-03-05', 100, 'TE코리아'),      ('ITEM019', '2025-04-05', 110, 'TE코리아'),
('ITEM019', '2025-05-05', 105, '한국몰렉스'),    ('ITEM019', '2025-06-05', 115, 'TE코리아'),
('ITEM019', '2025-07-05', 120, '한국몰렉스'),    ('ITEM019', '2025-08-05', 118, 'TE코리아'),
('ITEM019', '2025-09-05', 125, '한국몰렉스'),    ('ITEM019', '2025-10-05', 122, 'TE코리아'),
('ITEM019', '2025-11-05', 130, '한국몰렉스'),    ('ITEM019', '2025-12-05', 128, 'TE코리아'),
('ITEM019', '2026-01-05', 135, '한국몰렉스'),    ('ITEM019', '2026-02-05', 132, 'TE코리아'),
-- ITEM020 제어패널 (12개월)
('ITEM020', '2025-03-25',  15, 'LS일렉트릭'),    ('ITEM020', '2025-04-25',  18, 'LS일렉트릭'),
('ITEM020', '2025-05-25',  16, '슈나이더코리아'), ('ITEM020', '2025-06-25',  20, 'LS일렉트릭'),
('ITEM020', '2025-07-25',  18, '슈나이더코리아'), ('ITEM020', '2025-08-25',  22, 'LS일렉트릭'),
('ITEM020', '2025-09-25',  20, '슈나이더코리아'), ('ITEM020', '2025-10-25',  24, 'LS일렉트릭'),
('ITEM020', '2025-11-25',  22, '슈나이더코리아'), ('ITEM020', '2025-12-25',  25, 'LS일렉트릭'),
('ITEM020', '2026-01-25',  24, '슈나이더코리아'), ('ITEM020', '2026-02-05',  26, 'LS일렉트릭')
ON CONFLICT DO NOTHING;

-- ── 불량 이력 (50건 - AI 학습용) ────────────────────────────
INSERT INTO defect_history (item_code, equip_code, recorded_at, temperature, pressure, speed, humidity, defect_count, total_count) VALUES
-- 정상 범위 데이터 (불량률 < 3%)
('ITEM009', 'EQP-001', '2025-11-10 09:00', 195.0, 10.0, 50.0, 55.0,  2, 250),
('ITEM009', 'EQP-001', '2025-11-12 09:00', 198.0,  9.8, 48.0, 58.0,  3, 250),
('ITEM010', 'EQP-003', '2025-11-15 09:00', 180.0,  8.5, 45.0, 52.0,  1, 150),
('ITEM010', 'EQP-004', '2025-11-17 09:00', 182.0,  8.8, 46.0, 54.0,  2, 150),
('ITEM011', 'EQP-009', '2025-11-20 09:00', 210.0, 12.0, 55.0, 60.0,  3, 200),
('ITEM011', 'EQP-010', '2025-11-22 09:00', 208.0, 11.5, 53.0, 58.0,  2, 200),
('ITEM014', 'EQP-005', '2025-12-10 09:00', 200.0, 10.5, 52.0, 57.0,  5, 300),
('ITEM014', 'EQP-006', '2025-12-15 09:00', 202.0, 10.2, 51.0, 56.0,  3, 300),
('ITEM009', 'EQP-001', '2026-01-05 09:00', 196.0,  9.9, 49.0, 56.0,  4, 300),
('ITEM009', 'EQP-002', '2026-01-07 09:00', 199.0, 10.1, 50.0, 57.0,  2, 300),
('ITEM010', 'EQP-003', '2026-01-08 09:00', 183.0,  8.7, 46.0, 53.0,  3, 200),
('ITEM010', 'EQP-004', '2026-01-10 09:00', 181.0,  8.6, 45.0, 52.0,  1, 200),
('ITEM011', 'EQP-009', '2026-01-10 14:00', 212.0, 12.2, 55.0, 61.0,  4, 250),
('ITEM011', 'EQP-010', '2026-01-12 09:00', 209.0, 11.8, 54.0, 59.0,  2, 250),
('ITEM012', 'EQP-011', '2026-01-13 09:00', 175.0,  7.5, 40.0, 48.0,  2, 100),
('ITEM012', 'EQP-011', '2026-01-15 09:00', 178.0,  7.8, 42.0, 50.0,  1, 100),
('ITEM009', 'EQP-001', '2026-02-03 09:00', 197.0, 10.0, 50.0, 56.0,  5, 350),
('ITEM009', 'EQP-002', '2026-02-05 09:00', 200.0, 10.2, 51.0, 58.0,  4, 350),
('ITEM010', 'EQP-003', '2026-02-06 09:00', 184.0,  8.8, 47.0, 54.0,  3, 175),
('ITEM014', 'EQP-005', '2026-02-05 09:00', 201.0, 10.3, 52.0, 57.0,  6, 400),
-- 이상 범위 데이터 (불량률 > 5% — 온도/습도/압력 높음)
('ITEM015', 'EQP-011', '2025-11-25 09:00', 230.0, 14.0, 58.0, 75.0,  8, 100),
('ITEM015', 'EQP-012', '2025-11-28 09:00', 235.0, 14.5, 60.0, 78.0, 10, 100),
('ITEM016', 'EQP-011', '2025-12-01 09:00', 228.0, 13.5, 57.0, 73.0,  7, 100),
('ITEM017', 'EQP-012', '2025-12-05 09:00', 232.0, 14.2, 59.0, 76.0,  9, 100),
('ITEM017', 'EQP-012', '2025-12-08 09:00', 225.0, 13.0, 56.0, 72.0,  6, 100),
('ITEM015', 'EQP-012', '2026-01-18 09:00', 238.0, 15.0, 62.0, 80.0, 12, 100),
('ITEM015', 'EQP-012', '2026-01-20 09:00', 240.0, 15.5, 63.0, 82.0, 15, 100),
('ITEM018', 'EQP-011', '2026-01-22 09:00', 227.0, 13.8, 58.0, 74.0,  8, 100),
('ITEM018', 'EQP-012', '2026-01-25 09:00', 233.0, 14.3, 60.0, 77.0, 10, 100),
('ITEM013', 'EQP-008', '2026-02-07 09:00', 245.0, 16.0, 65.0, 85.0, 18, 125),
('ITEM013', 'EQP-008', '2026-02-09 09:00', 242.0, 15.8, 64.0, 83.0, 15, 125),
('ITEM015', 'EQP-011', '2026-02-10 09:00', 229.0, 13.6, 57.0, 73.0,  7, 100),
('ITEM015', 'EQP-012', '2026-02-11 09:00', 234.0, 14.4, 60.0, 77.0, 10, 100),
('ITEM016', 'EQP-011', '2026-02-10 14:00', 231.0, 14.1, 59.0, 76.0,  8, 100),
('ITEM014', 'EQP-006', '2026-02-08 09:00', 236.0, 14.8, 61.0, 79.0, 12, 400),
-- 경계 데이터 (불량률 3~5%)
('ITEM009', 'EQP-001', '2026-01-20 09:00', 215.0, 11.5, 53.0, 65.0,  8, 200),
('ITEM010', 'EQP-003', '2026-01-25 09:00', 205.0, 10.0, 50.0, 62.0,  6, 150),
('ITEM011', 'EQP-009', '2026-02-01 09:00', 218.0, 12.5, 55.0, 67.0,  9, 250),
('ITEM014', 'EQP-005', '2026-02-01 09:00', 210.0, 11.0, 53.0, 63.0,  7, 200),
('ITEM012', 'EQP-011', '2026-02-01 09:00', 190.0,  9.0, 47.0, 60.0,  4, 100),
-- 추가 정상 데이터
('ITEM009', 'EQP-002', '2025-12-01 09:00', 194.0,  9.7, 48.0, 54.0,  1, 200),
('ITEM010', 'EQP-004', '2025-12-15 09:00', 179.0,  8.4, 44.0, 51.0,  2, 200),
('ITEM011', 'EQP-010', '2025-12-20 09:00', 207.0, 11.3, 52.0, 57.0,  1, 150),
('ITEM014', 'EQP-006', '2026-01-05 09:00', 198.0, 10.0, 50.0, 55.0,  3, 250),
('ITEM009', 'EQP-001', '2026-02-10 09:00', 196.0,  9.9, 49.0, 56.0,  2, 200),
('ITEM011', 'EQP-009', '2026-02-08 09:00', 211.0, 12.1, 54.0, 60.0,  3, 200),
('ITEM014', 'EQP-005', '2026-02-10 09:00', 199.0, 10.1, 51.0, 56.0,  4, 300),
('ITEM010', 'EQP-003', '2026-02-10 09:00', 182.0,  8.6, 46.0, 53.0,  2, 175),
('ITEM012', 'EQP-011', '2026-02-05 09:00', 176.0,  7.6, 41.0, 49.0,  1, 120),
('ITEM015', 'EQP-012', '2026-02-08 09:00', 220.0, 12.8, 55.0, 70.0,  5, 100)
ON CONFLICT DO NOTHING;

-- ── 설비 센서 데이터 (100건+) ───────────────────────────────
INSERT INTO equip_sensors (equip_code, vibration, temperature, current_amp, recorded_at) VALUES
-- EQP-001 레이저절단기 (정상 → 경고)
('EQP-001', 0.8, 38.0, 10.5, '2026-02-03 08:00'),
('EQP-001', 0.9, 39.0, 10.8, '2026-02-03 09:00'),
('EQP-001', 1.0, 40.0, 11.0, '2026-02-03 10:00'),
('EQP-001', 1.1, 41.0, 11.2, '2026-02-03 11:00'),
('EQP-001', 0.9, 39.5, 10.9, '2026-02-03 12:00'),
('EQP-001', 1.0, 40.5, 11.1, '2026-02-03 13:00'),
('EQP-001', 1.2, 42.0, 11.5, '2026-02-03 14:00'),
('EQP-001', 1.1, 41.5, 11.3, '2026-02-03 15:00'),
('EQP-001', 1.0, 41.0, 11.2, '2026-02-04 08:00'),
('EQP-001', 1.1, 42.0, 11.4, '2026-02-04 09:00'),
('EQP-001', 1.3, 43.0, 11.8, '2026-02-04 10:00'),
('EQP-001', 1.5, 45.0, 12.2, '2026-02-04 11:00'),
('EQP-001', 1.4, 44.0, 12.0, '2026-02-04 12:00'),
('EQP-001', 1.6, 46.0, 12.5, '2026-02-05 08:00'),
('EQP-001', 1.8, 48.0, 13.0, '2026-02-05 09:00'),
('EQP-001', 2.0, 50.0, 13.5, '2026-02-05 10:00'),
('EQP-001', 2.2, 52.0, 13.8, '2026-02-05 11:00'),
('EQP-001', 2.1, 51.0, 13.6, '2026-02-05 12:00'),
('EQP-001', 1.9, 49.0, 13.2, '2026-02-06 08:00'),
('EQP-001', 1.8, 48.0, 13.0, '2026-02-06 09:00'),
-- EQP-003 CNC선반 (안정)
('EQP-003', 0.5, 35.0,  9.0, '2026-02-03 08:00'),
('EQP-003', 0.6, 36.0,  9.2, '2026-02-03 09:00'),
('EQP-003', 0.5, 35.5,  9.1, '2026-02-03 10:00'),
('EQP-003', 0.6, 36.5,  9.3, '2026-02-03 11:00'),
('EQP-003', 0.5, 35.0,  9.0, '2026-02-04 08:00'),
('EQP-003', 0.5, 35.5,  9.1, '2026-02-04 09:00'),
('EQP-003', 0.6, 36.0,  9.2, '2026-02-04 10:00'),
('EQP-003', 0.5, 35.0,  9.0, '2026-02-05 08:00'),
('EQP-003', 0.6, 36.0,  9.2, '2026-02-05 09:00'),
('EQP-003', 0.5, 35.5,  9.1, '2026-02-06 08:00'),
('EQP-003', 0.6, 36.0,  9.2, '2026-02-06 09:00'),
('EQP-003', 0.5, 35.5,  9.1, '2026-02-06 10:00'),
-- EQP-005 유압프레스 (서서히 악화)
('EQP-005', 1.0, 42.0, 12.0, '2026-02-03 08:00'),
('EQP-005', 1.1, 43.0, 12.3, '2026-02-03 10:00'),
('EQP-005', 1.2, 44.0, 12.5, '2026-02-03 14:00'),
('EQP-005', 1.5, 47.0, 13.0, '2026-02-04 08:00'),
('EQP-005', 1.8, 50.0, 13.5, '2026-02-04 10:00'),
('EQP-005', 2.0, 52.0, 14.0, '2026-02-04 14:00'),
('EQP-005', 2.3, 55.0, 14.5, '2026-02-05 08:00'),
('EQP-005', 2.5, 57.0, 14.8, '2026-02-05 10:00'),
('EQP-005', 2.8, 58.0, 15.0, '2026-02-05 14:00'),
('EQP-005', 3.0, 60.0, 15.5, '2026-02-06 08:00'),
('EQP-005', 3.2, 62.0, 15.8, '2026-02-06 10:00'),
('EQP-005', 3.5, 65.0, 16.2, '2026-02-06 14:00'),
('EQP-005', 3.8, 67.0, 16.5, '2026-02-07 08:00'),
('EQP-005', 3.5, 64.0, 16.0, '2026-02-07 10:00'),
('EQP-005', 3.2, 62.0, 15.8, '2026-02-08 08:00'),
-- EQP-009 사출기 (안정)
('EQP-009', 0.7, 38.0, 10.0, '2026-02-03 08:00'),
('EQP-009', 0.8, 39.0, 10.2, '2026-02-03 10:00'),
('EQP-009', 0.7, 38.5, 10.1, '2026-02-04 08:00'),
('EQP-009', 0.8, 39.0, 10.2, '2026-02-04 10:00'),
('EQP-009', 0.7, 38.0, 10.0, '2026-02-05 08:00'),
('EQP-009', 0.8, 39.0, 10.2, '2026-02-05 10:00'),
('EQP-009', 0.7, 38.0, 10.0, '2026-02-06 08:00'),
('EQP-009', 0.8, 39.5, 10.3, '2026-02-06 10:00'),
-- EQP-011 조립라인A (간헐적 이상)
('EQP-011', 1.0, 40.0, 11.0, '2026-02-03 08:00'),
('EQP-011', 1.2, 42.0, 11.5, '2026-02-03 10:00'),
('EQP-011', 1.5, 45.0, 12.0, '2026-02-03 14:00'),
('EQP-011', 1.0, 40.0, 11.0, '2026-02-04 08:00'),
('EQP-011', 1.1, 41.0, 11.2, '2026-02-04 10:00'),
('EQP-011', 2.5, 55.0, 14.0, '2026-02-04 14:00'),
('EQP-011', 1.2, 42.0, 11.5, '2026-02-05 08:00'),
('EQP-011', 1.0, 40.0, 11.0, '2026-02-05 10:00'),
('EQP-011', 2.8, 58.0, 14.5, '2026-02-05 14:00'),
('EQP-011', 1.1, 41.0, 11.2, '2026-02-06 08:00'),
('EQP-011', 1.3, 43.0, 11.8, '2026-02-06 10:00'),
('EQP-011', 3.0, 60.0, 15.0, '2026-02-06 14:00'),
-- EQP-012 조립라인B (정상)
('EQP-012', 0.8, 38.0, 10.5, '2026-02-03 08:00'),
('EQP-012', 0.9, 39.0, 10.8, '2026-02-03 10:00'),
('EQP-012', 0.8, 38.5, 10.6, '2026-02-04 08:00'),
('EQP-012', 0.9, 39.5, 10.9, '2026-02-04 10:00'),
('EQP-012', 0.8, 38.0, 10.5, '2026-02-05 08:00'),
('EQP-012', 0.9, 39.0, 10.8, '2026-02-05 10:00'),
('EQP-012', 0.8, 38.5, 10.6, '2026-02-06 08:00'),
('EQP-012', 0.9, 39.0, 10.7, '2026-02-06 10:00'),
-- EQP-013 SMT라인 (고장 상태 — 마지막 센서 데이터)
('EQP-013', 4.2, 72.0, 18.5, '2026-02-01 08:00'),
('EQP-013', 4.8, 78.0, 19.2, '2026-02-01 09:00'),
('EQP-013', 5.5, 85.0, 21.0, '2026-02-01 10:00'),
('EQP-013', 6.0, 90.0, 22.5, '2026-02-01 10:30'),
-- EQP-014 3차원측정기 (안정)
('EQP-014', 0.2, 22.0,  5.0, '2026-02-03 08:00'),
('EQP-014', 0.2, 22.5,  5.1, '2026-02-03 10:00'),
('EQP-014', 0.3, 23.0,  5.2, '2026-02-04 08:00'),
('EQP-014', 0.2, 22.0,  5.0, '2026-02-05 08:00'),
('EQP-014', 0.2, 22.5,  5.1, '2026-02-06 08:00'),
-- EQP-008 전기도금조 (정비중)
('EQP-008', 1.5, 55.0, 14.0, '2026-02-06 08:00'),
('EQP-008', 1.8, 58.0, 14.5, '2026-02-06 10:00'),
('EQP-008', 2.0, 60.0, 15.0, '2026-02-07 08:00'),
('EQP-008', 1.5, 52.0, 13.5, '2026-02-09 08:00'),
('EQP-008', 1.3, 50.0, 13.0, '2026-02-09 10:00')
ON CONFLICT DO NOTHING;

-- ── 설비 상태 이력 (25건) ───────────────────────────────────
INSERT INTO equip_status_log (equip_code, status, reason, worker_id, changed_at) VALUES
('EQP-001', 'RUNNING', '정상 가동 시작',              'worker01', '2025-11-10 07:50'),
('EQP-001', 'STOP',    '정기 점검',                   'worker01', '2025-12-01 17:00'),
('EQP-001', 'RUNNING', '점검 완료 재가동',            'worker01', '2025-12-02 08:00'),
('EQP-003', 'RUNNING', '정상 가동',                   'worker02', '2025-11-15 07:50'),
('EQP-003', 'STOP',    '툴 교체',                     'worker02', '2025-12-20 12:00'),
('EQP-003', 'RUNNING', '툴 교체 완료',                'worker02', '2025-12-20 14:00'),
('EQP-005', 'RUNNING', '정상 가동',                   'worker01', '2025-12-10 07:50'),
('EQP-005', 'STOP',    '유압오일 교체',               'worker01', '2026-01-15 17:00'),
('EQP-005', 'RUNNING', '오일 교체 완료',              'worker01', '2026-01-16 08:00'),
('EQP-008', 'RUNNING', '정상 가동',                   'worker04', '2026-01-05 08:00'),
('EQP-008', 'DOWN',    '도금액 농도 이상',            'worker04', '2026-02-06 15:00'),
('EQP-008', 'STOP',    '도금액 교체 중 (정비)',       'worker04', '2026-02-07 08:00'),
('EQP-009', 'RUNNING', '정상 가동',                   'worker03', '2025-11-20 07:50'),
('EQP-011', 'RUNNING', '정상 가동',                   'worker03', '2025-11-25 07:50'),
('EQP-011', 'DOWN',    '컨베이어 벨트 파손',          'worker03', '2026-01-30 14:30'),
('EQP-011', 'STOP',    '벨트 교체 중',                'worker03', '2026-01-30 15:00'),
('EQP-011', 'RUNNING', '벨트 교체 완료, 재가동',      'worker03', '2026-01-31 08:00'),
('EQP-012', 'RUNNING', '정상 가동',                   'worker03', '2025-11-28 07:50'),
('EQP-013', 'RUNNING', '정상 가동',                   'worker04', '2026-01-18 07:50'),
('EQP-013', 'DOWN',    'SMT 노즐 고장 + PCB피더 이상','worker04', '2026-02-01 10:30'),
('EQP-014', 'RUNNING', '정상 가동',                   'worker04', '2025-12-05 07:50'),
('EQP-015', 'RUNNING', '정상 가동',                   'worker05', '2025-12-10 07:50'),
('EQP-002', 'RUNNING', '정상 가동',                   'worker01', '2025-11-12 07:50'),
('EQP-006', 'RUNNING', '정상 가동',                   'worker01', '2025-12-15 07:50'),
('EQP-010', 'RUNNING', '정상 가동',                   'worker03', '2025-11-22 07:50')
ON CONFLICT DO NOTHING;

-- ── 품질 검사 결과 (30건) ───────────────────────────────────
INSERT INTO inspections (inspect_type, item_code, lot_no, judgment, inspected_at, inspector_id) VALUES
('INCOMING', 'ITEM001', 'LOT-20260101-001', 'PASS', '2026-01-01 10:00', 'worker04'),
('INCOMING', 'ITEM002', 'LOT-20260101-002', 'PASS', '2026-01-01 11:00', 'worker04'),
('INCOMING', 'ITEM003', 'LOT-20260101-003', 'PASS', '2026-01-01 14:00', 'worker04'),
('INCOMING', 'ITEM004', 'LOT-20260101-004', 'PASS', '2026-01-01 15:00', 'worker04'),
('INCOMING', 'ITEM006', 'LOT-20260101-006', 'PASS', '2026-01-02 09:00', 'worker04'),
('INCOMING', 'ITEM001', 'LOT-20260115-001', 'PASS', '2026-01-15 10:00', 'worker04'),
('INCOMING', 'ITEM001', 'LOT-20260201-001', 'FAIL', '2026-02-01 10:00', 'worker04'),
('INCOMING', 'ITEM002', 'LOT-20260201-002', 'PASS', '2026-02-01 11:00', 'worker04'),
('PROCESS',  'ITEM009', 'LOT-20260115-009', 'PASS', '2026-01-06 16:00', 'worker04'),
('PROCESS',  'ITEM010', 'LOT-20260115-010', 'PASS', '2026-01-09 16:00', 'worker04'),
('PROCESS',  'ITEM011', 'LOT-20260115-011', 'PASS', '2026-01-11 16:00', 'worker04'),
('PROCESS',  'ITEM012', 'LOT-20260120-012', 'PASS', '2026-01-14 16:00', 'worker04'),
('PROCESS',  'ITEM009', 'LOT-20260201-009', 'PASS', '2026-02-04 16:00', 'worker04'),
('PROCESS',  'ITEM010', 'LOT-20260201-010', 'PASS', '2026-02-07 16:00', 'worker04'),
('PROCESS',  'ITEM013', 'LOT-20260201-013', 'FAIL', '2026-02-08 16:00', 'worker04'),
('PROCESS',  'ITEM014', 'LOT-20260201-014', 'PASS', '2026-02-06 16:00', 'worker04'),
('OUTGOING', 'ITEM015', 'LOT-20260120-015', 'PASS', '2026-01-19 10:00', 'worker04'),
('OUTGOING', 'ITEM016', 'LOT-20260120-016', 'PASS', '2026-01-19 14:00', 'worker04'),
('OUTGOING', 'ITEM017', 'LOT-20260120-017', 'PASS', '2026-01-19 16:00', 'worker04'),
('OUTGOING', 'ITEM018', 'LOT-20260125-018', 'PASS', '2026-01-26 10:00', 'worker04'),
('OUTGOING', 'ITEM015', 'LOT-20260201-015', 'PASS', '2026-02-10 16:00', 'worker04'),
('OUTGOING', 'ITEM016', 'LOT-20260201-016', 'PASS', '2026-02-11 10:00', 'worker04'),
('OUTGOING', 'ITEM017', 'LOT-20260201-017', 'FAIL', '2026-02-11 14:00', 'worker04'),
('INCOMING', 'ITEM005', 'LOT-20260115-005', 'PASS', '2026-01-15 14:00', 'worker04'),
('INCOMING', 'ITEM007', 'LOT-20260101-007', 'PASS', '2026-01-02 10:00', 'worker04'),
('INCOMING', 'ITEM008', 'LOT-20260115-008', 'PASS', '2026-01-15 16:00', 'worker04'),
('PROCESS',  'ITEM011', 'LOT-20260201-011', 'PASS', '2026-02-09 10:00', 'worker04'),
('PROCESS',  'ITEM014', 'LOT-20260115-014', 'PASS', '2026-01-16 10:00', 'worker04'),
('OUTGOING', 'ITEM015', 'LOT-20260120-015', 'PASS', '2026-01-20 10:00', 'worker04'),
('OUTGOING', 'ITEM017', 'LOT-20260120-017', 'PASS', '2026-01-20 14:00', 'worker04')
ON CONFLICT DO NOTHING;

-- 검사 상세 (입고/공정 검사에 대한 측정값)
INSERT INTO inspection_details (inspection_id, check_name, measured_value, judgment) VALUES
(7,  '두께', 1.95, 'FAIL'),
(7,  '경도', 180.0, 'PASS'),
(9,  '프레임길이', 300.1, 'PASS'),
(9,  '프레임폭',   150.0, 'PASS'),
(9,  '외관검사',   NULL,  'PASS'),
(10, '외경', 10.005, 'PASS'),
(10, '표면조도', 1.2, 'PASS'),
(10, '진원도', 0.003, 'PASS'),
(11, '외관검사', NULL, 'PASS'),
(11, '무게', 120.5, 'PASS'),
(11, '두께', 2.5, 'PASS'),
(13, '프레임길이', 299.8, 'PASS'),
(13, '프레임폭', 150.2, 'PASS'),
(14, '외경', 10.008, 'PASS'),
(14, '표면조도', 1.4, 'PASS'),
(15, '도금두께', 7.5, 'FAIL'),
(15, '외관검사', NULL, 'FAIL'),
(17, '전압출력', 5.02, 'PASS'),
(17, '소비전력', 11.8, 'PASS'),
(17, '기능검사', NULL, 'PASS'),
(18, '내압시험', 36.0, 'PASS'),
(18, '누설검사', 0.02, 'PASS'),
(19, '온도정확도', 0.3, 'PASS'),
(19, '압력정확도', 0.8, 'PASS'),
(20, '출력', 498.0, 'PASS'),
(20, '효율', 91.5, 'PASS'),
(21, '전압출력', 5.05, 'PASS'),
(21, '소비전력', 12.1, 'PASS'),
(23, '온도정확도', 0.6, 'FAIL'),
(23, '압력정확도', 1.2, 'FAIL')
ON CONFLICT DO NOTHING;
