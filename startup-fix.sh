#!/bin/bash
# 1. 현재 진짜 IP 감지
REAL_IP=$(hostname -I | awk '{print $1}')
echo "🚀 Detected IP: $REAL_IP"

# 2. 프론트엔드 코드 내 IP 주소 자동 교체
sed -i "s/http:\/\/.*:30461/http:\/\/$REAL_IP:30461/g" ~/MES_PROJECT/frontend/src/App.jsx

# 3. 프론트엔드 재빌드 및 배포 업데이트
cd ~/MES_PROJECT/frontend
npm run build
kubectl delete configmap frontend-build --ignore-not-found
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend

# 4. 방화벽 다시 열기
sudo ufw allow 30000:32767/tcp
echo "✅ System recovered with IP: $REAL_IP"
