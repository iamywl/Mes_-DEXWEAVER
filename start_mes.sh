#!/bin/bash

# 프로젝트 폴더로 이동
cd ~/MES_PROJECT

echo "🌟 [iamywl] MES 통합 가동 및 DB 자동 빌드를 시작합니다..."

# 1. K8s 엔진 강제 복구 (Swap 끄기 및 서비스 재시작)
sudo swapoff -a
sudo systemctl restart containerd
sudo systemctl restart kubelet

# 2. 쿠버네티스 API 서버 응답 대기
echo "⏳ 쿠버네티스 엔진이 준비될 때까지 기다립니다..."
until kubectl get nodes &> /dev/null; do
    echo "   (로딩 중...)"
    sleep 5
done
echo "✅ 쿠버네티스 준비 완료!"

# 3. 인프라 설정 적용 (Postgres, App)
kubectl apply -f postgres.yaml
kubectl apply -f mes-final.yaml

# 4. DB 컨테이너가 준비될 때까지 대기
echo "⏳ 데이터베이스 컨테이너 가동 대기 중..."
until kubectl get pod -l app=postgres | grep -q "1/1"; do
    echo "   (DB 확인 중...)"
    sleep 3
done

# 5. DB 테이블 생성 및 기초 데이터 입력 (핵심 추가 파트)
echo "📂 DB 테이블 및 기초 데이터 생성 중..."
POSTGRES_POD=$(kubectl get pod -l app=postgres -o jsonpath='{.items[0].metadata.name}')

kubectl exec -i $POSTGRES_POD -- psql -U postgres -d mes_db <<SQL_EOF
-- 테이블 생성
CREATE TABLE IF NOT EXISTS items (
    item_code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(20),
    spec VARCHAR(100),
    unit VARCHAR(10),
    safe_stock INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS production_plans (
    plan_id SERIAL PRIMARY KEY,
    item_code VARCHAR(20) REFERENCES items(item_code),
    target_qty INT NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'WAIT'
);

CREATE TABLE IF NOT EXISTS processes (
    proc_id SERIAL PRIMARY KEY,
    proc_name VARCHAR(50),
    description TEXT
);

CREATE TABLE IF NOT EXISTS equipments (
    eq_id SERIAL PRIMARY KEY,
    eq_name VARCHAR(50),
    status VARCHAR(20) DEFAULT 'IDLE'
);

-- 기초 데이터 (이미 있으면 무시)
INSERT INTO items (item_code, name, category, unit) VALUES ('ITM-001', '전기차 배터리', 'PRODUCT', 'EA') ON CONFLICT DO NOTHING;
INSERT INTO items (item_code, name, category, unit) VALUES ('MAT-001', '리튬 이온 셀', 'RAW', 'EA') ON CONFLICT DO NOTHING;
INSERT INTO processes (proc_name, description) VALUES ('조립공정', '배터리 팩 조립 라인') ON CONFLICT DO NOTHING;
INSERT INTO equipments (eq_name, status) VALUES ('조립 로봇 A', 'RUNNING') ON CONFLICT DO NOTHING;
SQL_EOF

echo "✅ DB 빌드 완료!"

# 6. 최신 파이썬 코드 주입 및 서버 재시작
kubectl delete configmap mes-code --ignore-not-found
kubectl create configmap mes-code --from-literal=main.py="$(cat app.py)"
kubectl rollout restart deployment/mes-web

echo "⏳ 최종 서비스 안정화 중..."
sleep 10
kubectl get pods

echo "------------------------------------------------"
echo "🎉 모든 서비스와 DB가 준비되었습니다!"
echo "주소: http://192.168.64.5:30461"
echo "------------------------------------------------"
