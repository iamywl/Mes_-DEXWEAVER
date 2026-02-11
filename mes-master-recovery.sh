#!/bin/bash
# =========================================================
# KNU MES Project: Ultimate Self-Healing Script (v33.1)
# =========================================================
set +e 
PROJECT_DIR="$HOME/MES_PROJECT"
cd "$PROJECT_DIR"

echo "🔒 [1/7] 시스템 환경 최적화..."
sudo swapoff -a
sudo mkdir -p /mnt/data && sudo chmod 777 /mnt/data
sudo systemctl restart containerd
sudo systemctl restart kubelet
sleep 5

REAL_IP=$(hostname -I | awk '{print $1}')
echo "📡 서버 IP: $REAL_IP"

echo "⏳ [2/7] Kubernetes API 대기..."
until kubectl get nodes &> /dev/null; do printf "."; sleep 3; done
echo -e "\n✅ K8s 엔진 준비 완료!"

echo "🌐 [3/7] Cilium 네트워크 복구..."
kubectl delete pods -n kube-system -l k8s-app=cilium --ignore-not-found --force --grace-period=0
echo "⏳ 네트워크 에이전트 예열 중..."
for i in {1..12}; do
    RUNNING=$(kubectl get pods -n kube-system -l k8s-app=cilium -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' | wc -w)
    if [ "$RUNNING" -ge 1 ]; then
        echo "✅ 네트워크 소켓 복구 완료!"
        break
    fi
    sleep 5
done
sleep 10

echo "📦 [4/7] DB 저장소 강제 초기화..."
kubectl delete deployment postgres pvc postgres-pvc pv postgres-pv --ignore-not-found --force --grace-period=0
sleep 5

cat <<PV_EOF > "$PROJECT_DIR/postgres-infra.yaml"
apiVersion: v1
kind: PersistentVolume
metadata: { name: postgres-pv }
spec:
  storageClassName: manual
  capacity: { storage: 1Gi }
  accessModes: [ReadWriteOnce]
  hostPath: { path: "/mnt/data" }
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: postgres-pvc }
spec:
  storageClassName: manual
  accessModes: [ReadWriteOnce]
  resources: { requests: { storage: 1Gi } }
PV_EOF

kubectl apply -f "$PROJECT_DIR/postgres-infra.yaml"
kubectl apply -f "$PROJECT_DIR/postgres.yaml"
kubectl wait --for=condition=Ready pod -l app=postgres --timeout=120s

echo "🐳 [5/7] 백엔드 이미지 빌드 (실제 프로젝트 파일 사용)..."
# 사용자님의 실제 Dockerfile을 사용합니다.
docker build -f "$PROJECT_DIR/backend.Dockerfile" -t mes-api:latest "$PROJECT_DIR"

echo "🚀 [6/7] 백엔드 배포 (Port 8000 동기화)..."
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
        image: mes-api:latest
        imagePullPolicy: Never
        ports: [{ containerPort: 8000 }]
---
apiVersion: v1
kind: Service
metadata: { name: mes-api-service }
spec:
  type: NodePort
  selector: { app: mes-api }
  ports:
  - { port: 80, targetPort: 8000, nodePort: 30461 }
K8S

echo "🎨 [7/7] 프론트엔드 빌드 및 배포..."
sed -i "s|http://.*:30461|http://$REAL_IP:30461|g" "$PROJECT_DIR/frontend/src/App.jsx"
cd "$PROJECT_DIR/frontend" && npm install && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl apply -f "$PROJECT_DIR/mes-final.yaml"

echo "--------------------------------------------------------"
echo "🎉 통합 복구 완료! 접속 주소: http://$REAL_IP:30173"
echo "--------------------------------------------------------"
