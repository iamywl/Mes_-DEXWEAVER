-- 1. ENUM 타입 정의 (계획서 규격 반영)
CREATE TYPE user_role AS ENUM ('admin', 'worker', 'viewer');
CREATE TYPE item_category AS ENUM ('RAW', 'SEMI', 'PRODUCT');
CREATE TYPE equip_status AS ENUM ('RUNNING', 'STOP', 'DOWN');
CREATE TYPE plan_status AS ENUM ('WAIT', 'PROGRESS', 'DONE');
CREATE TYPE wo_status AS ENUM ('WAIT', 'WORKING', 'DONE');

-- 2. 사용자 관리 (Users)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role user_role NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. 사용자 권한 관리 (기능명세서 FN-003 대응)
CREATE TABLE IF NOT EXISTS user_permissions (
    perm_id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) REFERENCES users(user_id) ON DELETE CASCADE, -- 사용자 ID
    menu_name VARCHAR(50) NOT NULL,                                  -- 메뉴명 (예: 품목관리, 생산계획 등)
    can_read BOOLEAN DEFAULT TRUE,                                   -- 조회 권한
    can_write BOOLEAN DEFAULT FALSE,                                 -- 수정/삭제 권한
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                   -- 권한 부여 일시
);

-- 초기 권한 데이터 예시 (관리자용)
INSERT INTO user_permissions (user_id, menu_name, can_read, can_write) VALUES 
('admin', '기준정보', TRUE, TRUE),
('admin', '생산관리', TRUE, TRUE),
('admin', '품질재고', TRUE, TRUE),
('admin', '시스템관리', TRUE, TRUE);

-- 3. 품목 관리 (Items)
CREATE TABLE IF NOT EXISTS items (
    item_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category item_category NOT NULL,
    unit VARCHAR(10) NOT NULL,
    spec VARCHAR(500),
    safety_stock INT NOT NULL DEFAULT 0
);

-- 4. 공정 관리 (Processes)
CREATE TABLE IF NOT EXISTS processes (
    process_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    std_time_min INT NOT NULL,
    equip_code VARCHAR(20)  -- FK는 나중에 추가
);


-- 5. 설비 관리 (Equipments)
CREATE TABLE IF NOT EXISTS equipments (
    equip_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    process_code VARCHAR(20) NOT NULL,
    capacity_per_hour INT NOT NULL,
    status equip_status NOT NULL,
    FOREIGN KEY (process_code) REFERENCES processes(process_code)
);

ALTER TABLE processes
ADD CONSTRAINT fk_process_default_equip
FOREIGN KEY (equip_code) REFERENCES equipments(equip_code);


-- 6. BOM (Bill of Materials)
CREATE TABLE IF NOT EXISTS bom (
    bom_id SERIAL PRIMARY KEY,
    parent_item VARCHAR(20) NOT NULL,
    child_item VARCHAR(20) NOT NULL,
    qty_per_unit DECIMAL(10,4) NOT NULL,
    loss_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (parent_item) REFERENCES items(item_code),
    FOREIGN KEY (child_item) REFERENCES items(item_code)
);

-- 7. 생산 계획 (Production Plans)
CREATE TABLE IF NOT EXISTS production_plans (
    plan_id SERIAL PRIMARY KEY,
    item_code VARCHAR(20) NOT NULL,
    plan_qty INT NOT NULL,
    due_date DATE NOT NULL,
    status plan_status NOT NULL,
    FOREIGN KEY (item_code) REFERENCES items(item_code)
);

-- 8. 작업 지시 (Work Orders) - 수정본
CREATE TABLE IF NOT EXISTS work_orders (
    wo_id VARCHAR(20) PRIMARY KEY,
    plan_id INT NOT NULL,
    work_date DATE NOT NULL,
    equip_code VARCHAR(20) NOT NULL,
    plan_qty INT NOT NULL,
    status wo_status NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES production_plans(plan_id),
    FOREIGN KEY (equip_code) REFERENCES equipments(equip_code)
);


-- 9. 작업 실적 (Work Results)
CREATE TABLE IF NOT EXISTS work_results (
    result_id SERIAL PRIMARY KEY,
    wo_id VARCHAR(20) NOT NULL,
    good_qty INT NOT NULL,
    defect_qty INT NOT NULL,
    worker_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    FOREIGN KEY (wo_id) REFERENCES work_orders(wo_id),
    FOREIGN KEY (worker_id) REFERENCES users(user_id)
);


-- 10. 재고 관리 (Inventory)
CREATE TABLE IF NOT EXISTS inventory (
    inv_id SERIAL PRIMARY KEY,
    item_code VARCHAR(20) NOT NULL,
    lot_no VARCHAR(30) NOT NULL,
    qty INT NOT NULL,
    warehouse VARCHAR(10) NOT NULL,
    location VARCHAR(20),
    FOREIGN KEY (item_code) REFERENCES items(item_code)
);


-- 8. 초기 데이터 삽입 (테스트용)
INSERT INTO users (user_id, password, name, role)
VALUES ('admin', '1234', '관리자', 'admin');

INSERT INTO items (item_code, name, category, unit)
VALUES ('ITM-001', 'ADAS 센서', 'PRODUCT', 'EA');

INSERT INTO user_permissions (user_id, menu_name, can_read, can_write) VALUES 
('admin', '기준정보', TRUE, TRUE),
('admin', '생산관리', TRUE, TRUE),
('admin', '품질재고', TRUE, TRUE),
('admin', '시스템관리', TRUE, TRUE);
