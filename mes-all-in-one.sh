#!/bin/bash
# =========================================================
# KNU Advanced MES: Master Deployment Script (v31.0)
# =========================================================
set +e
PROJECT_DIR="$HOME/MES_PROJECT"
cd $PROJECT_DIR

echo "🔒 [1/7] 인프라 초기화..."
sudo swapoff -a
sudo mkdir -p /mnt/data && sudo chmod 777 /mnt/data
sudo systemctl restart containerd
sudo systemctl restart kubelet
sleep 5

REAL_IP=$(hostname -I | awk '{print $1}')
echo "📡 감지된 IP: $REAL_IP"

echo "📦 [2/7] DB 강제 복구 (PVC/PV 초기화)..."
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

echo "🔑 [3/7] K8s Secret 생성..."
kubectl delete secret db-credentials --ignore-not-found
kubectl create secret generic db-credentials \
  --from-literal=DATABASE_URL="postgresql://postgres:mes1234@postgres:5432/mes_db"

echo "⚙️  [4/7] 백엔드 배포..."
kubectl delete configmap api-code --ignore-not-found
kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/
kubectl delete deployment mes-api --ignore-not-found
cat <<K8S | kubectl apply -f -
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
          mkdir -p /app/api_modules &&
          cp /mnt/*.py /app/api_modules/ &&
          mv /app/api_modules/app.py /app/app.py &&
          touch /app/api_modules/__init__.py &&
          pip install --no-cache-dir fastapi uvicorn psycopg2-binary kubernetes pydantic psutil &&
          python /app/app.py
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: DATABASE_URL
        - name: CORS_ORIGINS
          value: "http://${REAL_IP}:30173,http://localhost:30173,http://localhost:3000"
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

echo "🎨 [5/7] 프론트엔드 빌드..."
cd $PROJECT_DIR/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl apply -f $PROJECT_DIR/mes-final.yaml

echo "🛡️  [6/7] 최종 개방..."
sudo ufw allow 30000:32767/tcp

echo "✅ [7/7] 배포 검증..."
sleep 10
echo "Backend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:30461/api/infra/status)"
echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:30173)"
echo "🎯 모든 프로세스 완료! http://$REAL_IP:30173 접속 후 1분만 기다려주세요."
