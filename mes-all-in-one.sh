#!/bin/bash
# =========================================================
# KNU Advanced MES: Frontend-Optimized Master Script (v30.0)
# =========================================================
set +e
PROJECT_DIR="$HOME/MES_PROJECT"
cd $PROJECT_DIR

echo "🔒 [1/6] 인프라 초기화..."
sudo swapoff -a
sudo mkdir -p /mnt/data && sudo chmod 777 /mnt/data
sudo systemctl restart containerd
sudo systemctl restart kubelet
sleep 5

REAL_IP=$(hostname -I | awk '{print $1}')
echo "📡 감지된 IP: $REAL_IP"

echo "📦 [2/6] DB 강제 복구 (PVC/PV 초기화)..."
kubectl delete deployment postgres pvc postgres-pvc pv postgres-pv --ignore-not-found --force --grace-period=0
cat <<PV_EOF > $PROJECT_DIR/postgres-pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: postgres-pv }
spec:
  storageClassName: manual
  capacity: { storage: 1Gi }
  accessModes: [ReadWriteOnce]
  hostPath: { path: "/mnt/data" }
PV_EOF
kubectl apply -f $PROJECT_DIR/postgres-pv.yaml
kubectl apply -f $PROJECT_DIR/postgres.yaml

echo "⚙️  [3/6] 프론트엔드 맞춤형 app.py 생성 및 통합..."
# 화면(Console)에서 요청하는 엔드포인트(/api/mes/data 등)에 맞춰 app.py를 재작성합니다.
cat <<APP_EOF > $PROJECT_DIR/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_modules import mes_dashboard, mes_inventory_status, sys_logic
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/mes/data")
async def get_mes_data(): return await mes_dashboard.get_production_dashboard_data()

@app.get("/api/network/flows")
async def get_flows(): return {"status": "success", "flows": []}

@app.get("/api/infra/status")
async def get_infra(): return {"cpu_load": 15, "memory_usage": 40}

@app.get("/api/k8s/pods")
async def get_pods(): return sys_logic.get_pods()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
APP_EOF

echo "⚙️  [4/6] 백엔드 배포..."
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/
kubectl delete deployment mes-api --ignore-not-found
cat <<'K8S' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata: { name: mes-api }
spec:
  replicas: 1
  selector: { matchLabels: { app: mes-api } }
  template:
    metadata: { labels: { app: mes-api } }
    spec:
      containers:
      - name: mes-api
        image: python:3.9-slim
        command: ["/bin/sh", "-c"]
        args:
        - |
          mkdir -p /app/api_modules
          cp /mnt/*.py /app/api_modules/
          mv /app/api_modules/app.py /app/app.py
          touch /app/api_modules/__init__.py
          pip install fastapi uvicorn psycopg2-binary kubernetes pydantic
          python /app/app.py
        volumeMounts: [{ name: code-volume, mountPath: /mnt }]
      volumes:
      - name: code-volume
        configMap: { name: api-code }
---
apiVersion: v1
kind: Service
metadata: { name: mes-api-service }
spec:
  type: NodePort
  selector: { app: mes-api }
  ports:
  - { port: 80, targetPort: 80, nodePort: 30461 }
K8S

echo "🎨 [5/6] 프론트엔드 빌드..."
sed -i "s|http://.*:30461|http://$REAL_IP:30461|g" $PROJECT_DIR/frontend/src/App.jsx
cd $PROJECT_DIR/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl apply -f $PROJECT_DIR/mes-final.yaml

echo "🛡️  [6/6] 최종 개방..."
sudo ufw allow 30000:32767/tcp
echo "🎯 모든 프로세스 완료! http://$REAL_IP:30173 접속 후 1분만 기다려주세요."
