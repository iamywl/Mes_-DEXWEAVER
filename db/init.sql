CREATE TABLE IF NOT EXISTS items (
    item_code VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- e.g., '원자재', '반제품', '완제품'
    unit VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS production_plans (
    plan_id SERIAL PRIMARY KEY,
    item_code VARCHAR(255) REFERENCES items(item_code),
    quantity INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' -- e.g., 'pending', 'in_progress', 'completed'
);

CREATE TABLE IF NOT EXISTS equipments (
    equipment_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'IDLE' -- e.g., 'RUN', 'IDLE'
);

CREATE TABLE IF NOT EXISTS bom (
    product_item_code VARCHAR(255) REFERENCES items(item_code),
    component_item_code VARCHAR(255) REFERENCES items(item_code),
    quantity INTEGER NOT NULL,
    PRIMARY KEY (product_item_code, component_item_code)
);

-- Optional: Add some initial data for testing
INSERT INTO items (item_code, name, type, unit) VALUES
('ITEM001', '원자재A', '원자재', 'EA') ON CONFLICT (item_code) DO NOTHING,
('ITEM002', '반제품B', '반제품', 'EA') ON CONFLICT (item_code) DO NOTHING,
('ITEM003', '완제품C', '완제품', 'EA') ON CONFLICT (item_code) DO NOTHING,
('ITEM004', '중간부품D', '반제품', 'EA') ON CONFLICT (item_code) DO NOTHING,
('ITEM005', '최종제품E', '완제품', 'EA') ON CONFLICT (item_code) DO NOTHING;

INSERT INTO equipments (equipment_id, name, status) VALUES
('EQP001', '설비A', 'IDLE') ON CONFLICT (equipment_id) DO NOTHING,
('EQP002', '설비B', 'RUN') ON CONFLICT (equipment_id) DO NOTHING;

-- Example BOM entries
INSERT INTO bom (product_item_code, component_item_code, quantity) VALUES
('ITEM005', 'ITEM003', 2) ON CONFLICT (product_item_code, component_item_code) DO NOTHING,
('ITEM005', 'ITEM004', 1) ON CONFLICT (product_item_code, component_item_code) DO NOTHING;