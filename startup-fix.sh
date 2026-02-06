#!/bin/bash
# 1. 컨테이너 런타임 및 쿠블렛 강제 활성화 (containerd 대응)
sudo swapoff -a

# docker 대신 containerd를 확인하고 재시작합니다.
if systemctl list-unit-files | grep -q containerd.service; then
    sudo systemctl restart containerd
    echo "✅ Containerd restarted."
else
    echo "⚠️ Neither docker nor containerd found. Please check your runtime."
fi

sudo systemctl restart kubelet

REAL_IP=$(hostname -I | awk '{print $1}')
echo "🚀 Detected IP: $REAL_IP"

# 2. 쿠버네티스 API 서버 대기 (최대 120초)
echo "⏳ Waiting for Kubernetes API Server (up to 120s)..."
for i in {1..30}; do
  if kubectl get nodes &> /dev/null; then
    echo -e "\n✅ Kubernetes is ready!"
    break
  fi
  printf "."
  sleep 4
  if [ $i -eq 30 ]; then
    echo -e "\n❌ API Server timed out. Run 'journalctl -xeu kubelet' for logs."
    exit 1
  fi
done

# 3. 프론트엔드 빌드 및 배포
sed -i "s/http:\/\/.*:30461/http:\/\/$REAL_IP:30461/g" ~/MES_PROJECT/frontend/src/App.jsx
cd ~/MES_PROJECT/frontend && npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend

# 4. 방화벽 개방
sudo ufw allow 30000:32767/tcp
echo "✅ All systems recovered at http://$REAL_IP:30173"
