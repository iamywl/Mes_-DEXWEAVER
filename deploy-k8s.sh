#!/bin/bash
# =========================================================
# KNU MES: K8s Deployment Script (CD Stage)
# =========================================================
set +e
PROJECT_DIR="$HOME/MES_PROJECT"
cd $PROJECT_DIR

# 1. 최신 이미지 태그 읽기
if [ ! -f "$PROJECT_DIR/.last_image_tag" ]; then
    echo "❌ 에러: 빌드된 이미지가 없습니다. ./build-image.sh를 먼저 실행하세요."
    exit 1
fi
IMAGE_NAME=$(cat $PROJECT_DIR/.last_image_tag)
REAL_IP=$(hostname -I | awk '{print $1}')

echo "🚀 [DEPLOY] 배포 시작 (이미지: $IMAGE_NAME)"

echo "📦 [1/4] 인프라 자가 복구 (PV/DB)..."
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

echo "⚙️  [2/4] 백엔드 API 서버 배포..."
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
        image: $IMAGE_NAME
        imagePullPolicy: Never
        ports: [{ containerPort: 80 }]
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

echo "🎨 [3/4] 프론트엔드 빌드 및 배포..."
sed -i "s|http://.*:30461|http://$REAL_IP:30461|g" $PROJECT_DIR/frontend/src/App.jsx
cd $PROJECT_DIR/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl apply -f $PROJECT_DIR/mes-final.yaml

echo "--------------------------------------------------------"
echo "🎯 배포 완료! 주소: http://$REAL_IP:30173"
echo "--------------------------------------------------------"
