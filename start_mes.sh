#!/bin/bash

# 프로젝트 폴더로 이동
cd ~/MES_PROJECT

echo "🌟 [iamywl] MES 시스템 통합 가동을 시작합니다..."

# 1. K8s 엔진 강제 복구 (Swap 끄기 및 서비스 재시작)
echo "🔧 1단계: K8s 엔진 상태 최적화 중 (Swap off & Restart)..."
sudo swapoff -a
sudo systemctl restart containerd
sudo systemctl restart kubelet

# 2. 쿠버네티스 API 서버가 응답할 때까지 대기 (최대 3분)
echo "⏳ 2단계: 쿠버네티스 API 서버 응답 대기 중..."
MAX_RETRIES=36
COUNT=0
while ! kubectl get nodes &> /dev/null; do
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ 에러: 쿠버네티스가 3분 안에 살아나지 않았습니다."
        echo "명령어 'journalctl -u kubelet -n 100'으로 로그를 확인해 보세요."
        exit 1
    fi
    echo "   (로딩 중... $((COUNT * 5))초 경과)"
    sleep 5
done

echo "✅ 쿠버네티스 엔진 가동 확인!"

# 3. 데이터베이스 및 서버 설정 적용
echo "📦 3단계: MES 인프라 및 DB 설정 적용 중..."
kubectl apply -f postgres.yaml
kubectl apply -f mes-final.yaml

# 4. 최신 파이썬 코드 주입
echo "📝 4단계: app.py 코드를 ConfigMap에 동기화 중..."
kubectl delete configmap mes-code --ignore-not-found
kubectl create configmap mes-code --from-literal=main.py="$(cat app.py)"

# 5. 웹 서버 재시작 및 최종 확인
echo "♻️ 5단계: 웹 서버 서비스 갱신 중..."
kubectl rollout restart deployment/mes-web

echo "⏳ 최종 안정화 대기 (10초)..."
sleep 10
kubectl get pods

echo "------------------------------------------------"
echo "🎉 모든 준비가 끝났습니다!"
echo "주소: http://192.168.64.5:30461"
echo "------------------------------------------------"
