# 🏭 스마트 팩토리 MES 프로젝트 (K8s 기반)

이 프로젝트는 Kubernetes(K8s) 환경에서 작동하는 싱글 테넌트 MES 시스템입니다.

## 🛠 구성 요소
* **Database**: PostgreSQL (포트 5432)
* **Backend/Frontend**: Flask (Python 3.9)
* **Network**: Cilium (eBPF 기반)

## 🚀 실행 순서 (복사해서 터미널에 붙여넣으세요)

### 1단계: 데이터베이스 설치
```bash
kubectl apply -f postgres.yaml
```

### 2단계: 파이썬 코드 등록 (ConfigMap)
```bash
kubectl delete configmap mes-code --ignore-not-found
kubectl create configmap mes-code --from-literal=main.py="$(cat app.py)"
```

### 3단계: 웹 서버 실행
```bash
kubectl apply -f mes-final.yaml
```

## 🔍 접속 방법
* **주소**: http://[가상머신-IP]:30461
* **확인**: `kubectl get pods` 명령어로 모든 Pod가 **Running**인지 확인하세요.

## 📊 현재 생성된 테이블
* users, items, bom, equipments, processes, production_plans 등
