# 🏭 스마트 팩토리 MES (Manufacturing Execution System)

> **K8s 기반 모듈화 MES 시스템** - 경북대학교 스마트 팩토리 운영 시스템

## 📋 프로젝트 개요

**MES (Manufacturing Execution System)**는 제조 현장의 생산 계획, 실행, 품질 관리 등을 종합적으로 관리하는 엔터프라이즈 시스템입니다. 본 프로젝트는 Kubernetes 기반의 클라우드 네이티브 아키텍처로 구축되며, 실시간 모니터링 및 확장성을 제공합니다.

---

## 🛠 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| **인프라** | Kubernetes (K8s) | v1.30+ |
| **네트워크** | Cilium eBPF | Hubble 포함 |
| **데이터베이스** | PostgreSQL | 최신 |
| **백엔드 API** | Python FastAPI | 0.109.0+ |
| **웹 애플리케이션** | React18 + Vite | 최신 |
| **컨테이너** | Docker | 최신 |
| **배포 자동화** | Jenkins CI/CD | Jenkinsfile 기반 |

---

## 📂 프로젝트 구조

```
MES_PROJECT/
├── app.py                          # FastAPI 메인 애플리케이션
├── database.py                     # PostgreSQL 연결 설정
├── requirements.txt                # Python 의존성
├── docker-compose.yml              # 로컬 개발 환경 설정
├── Dockerfile                      # 백엔드 이미지 빌드 설정
├── Jenkinsfile                     # CI/CD 파이프라인
│
├── api_modules/                    # 📦 핵심 비즈니스 로직 (모듈화)
│   ├── database.py                 # ORM 모델 정의
│   ├── db_core.py                  # DB 코어 유틸리티
│   ├── sys_logic.py                # 시스템 로직 (K8s 모니터링)
│   ├── mes_dashboard.py            # 대시보드 데이터
│   ├── mes_master.py               # 기초 정보 관리
│   ├── mes_production.py           # 생산 관리
│   ├── mes_inventory_status.py     # 재고 상태
│   ├── mes_inventory_movement.py   # 재고 이동
│   ├── mes_material_receipt.py     # 자재 수입
│   ├── mes_work_order.py           # 작업 지시
│   ├── mes_execution.py            # 생산 실행
│   ├── mes_logistics.py            # 물류 관리
│   ├── mes_performance.py          # 성능 지표
│   ├── mes_service.py              # 서비스 로직
│   ├── mes_ai_prediction.py        # AI 수요 예측
│   ├── mes_defect_predict.py       # AI 불량 예측
│   └── k8s_service.py              # Kubernetes API
│
├── frontend/                       # 🎨 React 프론트엔드
│   ├── src/
│   │   ├── App.jsx                 # 메인 컴포넌트
│   │   ├── api.js                  # API 호출
│   │   ├── main.jsx                # 진입점
│   │   ├── BOMManager.jsx          # BOM 관리
│   │   ├── BomList.jsx             # BOM 리스트
│   │   ├── BomRegistrationForm.jsx # BOM 등록
│   │   └── PlanForm.jsx            # 생산 계획 양식
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── k8s/                            # ☸️ Kubernetes 배포
│   ├── backend-deployment.yaml     # 백엔드 배포
│   ├── backend-service.yaml        # 백엔드 서비스
│   ├── frontend-deployment.yaml    # 프론트엔드 배포
│   └── frontend-service.yaml       # 프론트엔드 서비스
│
├── db/
│   └── init.sql                    # DB 초기 스키마
│
├── doc/                            # 📚 문서
│   ├── STATUS_*.md
│   ├── 주간보고_*.md
│   └── REQ/
│       ├── Requirements_Specification.md
│       ├── Functional_Specification.md
│       └── DatabaseSchema.md
│
├── 배포 스크립트/
│   ├── build-image.sh              # Docker 이미지 빌드
│   ├── deploy-k8s.sh               # K8s 배포
│   └── mes-all-in-one.sh           # 통합 배포 및 복구
│
├── 주요 문서/
│   ├── README.md                   # 이 파일
│   ├── REQUIREMENTS.md             # 요구사항 정의서
│   ├── GUIDE.md                    # 운영 가이드
│   └── CICD_GUIDE.md               # CI/CD 파이프라인 가이드
│
└── test_app.py                     # 백엔드 테스트
```

---

## 🚀 빠른 시작

### 1️⃣ 로컬 개발 환경 (Docker Compose)

```bash
# 환경 설정
cd /root/MES_PROJECT

# Docker Compose로 PostgreSQL + FastAPI 실행
docker-compose -f docker-compose.yml up -d

# 백엔드 서버 실행
pip install -r requirements.txt
python app.py

# 프론트엔드 서버 실행
cd frontend
npm install
npm run dev
```

**접속 정보:**
- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000/docs
- PostgreSQL: localhost:5433 (user: postgres, password: 1234)

---

### 2️⃣ Kubernetes 배포 (클라우드 환경)

#### **A) 전체 자동 배포** (권장)
```bash
# 인프라 초기화 + 배포 완료
bash mes-all-in-one.sh

# 배포 상태 확인
kubectl get pods -o wide
```

#### **B) 단계별 배포**
```bash
# 1단계: Docker 이미지 빌드
bash build-image.sh

# 2단계: K8s 클러스터에 배포
bash deploy-k8s.sh

# 3단계: 서비스 접속 정보 확인
kubectl get svc
```

---

## 📚 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/mes/data` | GET | MES 대시보드 데이터 |
| `/api/k8s/pods` | GET | K8s 파드 상태 |
| `/api/infra/status` | GET | 인프라 상태 |
| `/api/network/flows` | GET | 네트워크 플로우 |

자세한 API 문서는 Swagger UI에서 확인합니다 (`/docs`).

---

## 🔧 시스템 관리

### 배포 상태 확인
```bash
kubectl get pods
kubectl logs -f deployment/backend-deployment
kubectl top pods
```

### 서비스 재시작
```bash
# 백엔드 재시작
kubectl rollout restart deployment/backend-deployment

# 전체 초기화
bash mes-all-in-one.sh
```

---

## 📋 구현 현황

### ✅ 완료된 기능
- [x] 데이터베이스 (REQ-001): PostgreSQL 배포 및 자동 스키마 생성
- [x] 품목 관리 (REQ-004, 005): 품목 등록 및 리스트 조회
- [x] BOM 관리 (REQ-007, 008): 제품 계층 구조 및 소요량
- [x] 생산 계획 (REQ-013, 014): 생산계획 수립 및 필터링
- [x] 설비 & 인프라 (REQ-012): eBPF 기반 네트워크 모니터링
- [x] K8s 관리: 파드 상태 모니터링 및 실시간 로그
- [x] 모듈화 아키텍처 (v21.0): 유지보수성 향상

### 🔄 개발 중인 기능
- [ ] 생산 실행 (REQ-017, 019): 작업지시 생성 및 작업 실적 등록
- [ ] AI 지능화 (REQ-015, 024): 수요예측 & 불량예측 모듈

---

## 📖 추가 문서

- **[REQUIREMENTS.md](REQUIREMENTS.md)** - 요구사항 정의서
- **[GUIDE.md](GUIDE.md)** - 운영 가이드
- **[CICD_GUIDE.md](CICD_GUIDE.md)** - CI/CD 파이프라인
- **[doc/REQ/](doc/REQ/)** - 기술 사양서

---

## 👥 팀 협업

### API 모듈 추가
```bash
# 1. api_modules/mes_newmodule.py 생성
# 2. app.py에 라우트 추가
# 3. 배포
bash build-image.sh && bash deploy-k8s.sh
```

---

**최종 업데이트**: 2026년 2월  
**프로젝트**: K8s 기반 스마트 팩토리 MES  
**지원**: 경북대학교 스마트 팩토리 개발팀
