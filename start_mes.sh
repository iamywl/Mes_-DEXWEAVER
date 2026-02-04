#!/bin/bash
echo "🌟 MES 시스템 가동을 시작합니다..."

# 시스템 최적화
sudo swapoff -a
sudo systemctl restart containerd
sudo systemctl restart kubelet

echo "⏳ K8s API 서버 응답 대기 중..."
until kubectl get nodes &> /dev/null; do sleep 5; done

# 서비스 배포 (DB -> Backend -> Frontend)
kubectl apply -f ~/MES_PROJECT/postgres.yaml
kubectl apply -f ~/MES_PROJECT/mes-final.yaml
# 프론트엔드는 configMap 대문자 수정된 버전으로 이미 적용됨

echo "✅ 모든 서비스 가동 완료!"
echo "🌐 접속 주소: http://192.168.64.5:30173"
