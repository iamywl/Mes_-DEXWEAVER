# 🏭 경북대 스마트 팩토리 MES 협업 프로젝트

이 프로젝트는 Kubernetes(K8s)와 Cilium 네트워크 기반에서 작동하는 MES 시스템입니다. 모든 팀원이 동일한 화면과 데이터를 보려면 아래 절차를 반드시 준수해야 합니다.

## 🛠 기술 스택
* **Infrastructure**: Kubernetes (v1.30+), Cilium (eBPF)
* **Database**: PostgreSQL (mes_db)
* **Backend**: Python Flask

## 🚀 환경 동기화 순서 (필수)

### 1단계: 최신 코드 가져오기
가장 먼저 Git에서 친구가 올린 최신 코드를 내려받아야 합니다.
```bash
git pull origin main
```

### 2단계: 데이터베이스 및 테이블 초기화
모든 팀원이 동일한 테이블 구조를 가져야 합니다. (이미 생성했다면 생략 가능)
```bash
kubectl apply -f postgres.yaml
# 테이블 생성 SQL 실행 (최초 1회)
kubectl exec -it $(kubectl get pod -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -d mes_db -f /path/to/your/schema.sql
```

### 3단계: 기본 테스트 데이터 동기화 (일관성 유지)
화면에 동일한 데이터가 뜨게 하려면 아래 명령어를 똑같이 실행하세요.
```bash
kubectl exec -it $(kubectl get pod -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -d mes_db -c "
INSERT INTO items (item_code, name, category, unit) VALUES ('PRD-001', '전기차 배터리 패크', 'PRODUCT', 'EA');
INSERT INTO items (item_code, name, category, unit) VALUES ('TEST-V01', '시운전 배터리', 'PRODUCT', 'EA');
"
```

### 4단계: 웹 서버 적용
```bash
kubectl delete configmap mes-code --ignore-not-found
kubectl create configmap mes-code --from-literal=main.py="$(cat app.py)"
kubectl rollout restart deployment/mes-web
```

## 🔍 접속 및 확인
* **접속 주소**: http://192.168.64.5:30461
* **데이터 불일치 시**: 브라우저에서 `Ctrl + F5`를 눌러 캐시를 새로고침하세요.

## 📋 구현 현황
- [x] 품목 관리 (REQ-004): 품목 등록 및 실시간 DB 대시보드 출력
- [ ] 생산 계획 (REQ-013): 계획 수립 및 상태 추적 기능 (개발 예정)
