# KNU MES v5.3 — 스마트 팩토리 Manufacturing Execution System

> Kubernetes 기반 클라우드 네이티브 MES 시스템 — 경북대학교 스마트 팩토리

---

## VM 부팅 후 서버 시작 방법

### 1단계: VM 접속

```bash
# SSH 접속 (외부에서)
ssh c1_master1@192.168.64.5

# root 전환
sudo -s
# 비밀번호 입력
```

### 2단계: 서버 시작 (원클릭)

```bash
bash /root/MES_PROJECT/init.sh
```

이 스크립트 하나로 아래 작업이 자동으로 수행됩니다:

| 단계 | 작업 | 설명 |
|------|------|------|
| 1/9 | 시스템 설정 | swap 비활성화, containerd/kubelet 재시작 |
| 2/9 | K8s API 대기 | Kubernetes API 서버 응답 대기 |
| 3/9 | 네트워크 복구 | Cilium CNI Pod 재시작 |
| 4/9 | Pod 정리 | Unknown/Error 상태 Pod 삭제 |
| 5/9 | DB 배포 | PostgreSQL + PV/PVC + Secret 생성 |
| 6/9 | Keycloak 배포 | Keycloak 인증 서버 배포 |
| 7/9 | 백엔드 배포 | FastAPI ConfigMap 생성 + Deployment 배포 |
| 8/9 | 프론트엔드 배포 | React 빌드 + nginx 배포 |
| 9/9 | 검증 | 응답 확인 + Keycloak Realm/사용자 자동 설정 |

### 3단계: 접속 확인

스크립트 완료 후 브라우저에서 접속:

- **웹 UI**: `http://192.168.64.5:30173`
- **API 문서**: `http://192.168.64.5:30461/docs`
- **Keycloak**: `http://192.168.64.5:30080`

> API 서버는 pip install 때문에 최초 기동 시 1~2분 소요될 수 있습니다.

### 상태 확인 명령어

```bash
# Pod 상태 확인
kubectl get pods

# API 로그 확인
kubectl logs deployment/mes-api --tail=20

# 프론트엔드 로그
kubectl logs deployment/mes-frontend --tail=20
```

---

## 시스템 개요

14개 메뉴로 구성된 통합 제조 실행 시스템입니다.

| 영역 | 메뉴 | 주요 기능 |
|------|------|-----------|
| 기준정보 | Items, BOM, Process, Equipment | 품목/BOM(목록·전개·역전개)/공정(마스터·라우팅·요약)/설비 관리 |
| 생산관리 | Plans, Work Order | 생산계획, 작업지시 |
| 품질/재고 | Quality, Inventory | 불량 분석, 재고 현황 |
| AI 분석 | AI Center | 수요예측, 불량예측, 고장예측 |
| 리포트 | Reports | 생산/품질 리포트, AI 인사이트 |
| 모니터링 | Network, Infra, K8s | Hubble 서비스맵, 인프라, Pod 관리 |

### 공통 기능: 테이블 필터

모든 데이터 테이블에 필터 바가 제공됩니다:
- **드롭다운 필터**: 상태, 카테고리, 우선순위 등
- **텍스트 검색**: 코드, 이름, 규격 등 자유 검색
- **결과 카운트**: 필터링 건수 / 전체 건수 실시간 표시

---

## 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| 인프라 | Kubernetes (kubeadm) | v1.30+ |
| 네트워크 | Cilium eBPF + Hubble | 최신 |
| DB | PostgreSQL | 15 |
| 백엔드 | Python FastAPI | 0.109+ |
| 프론트엔드 | React 19 + Vite + Tailwind CSS 4 | 최신 |
| 프론트엔드 서빙 | nginx:alpine | 최신 |
| 인증 | Keycloak (OIDC/PKCE) | 24.0.5 |
| 배포 방식 | ConfigMap 기반 (Docker 빌드 불필요) | - |

---

## 프로젝트 구조

```
MES_PROJECT/
├── init.sh                     # 통합 초기화 스크립트 (VM 부팅 후 실행)
├── env.sh                      # 환경 변수 설정 (모든 스크립트가 source)
├── setup-keycloak.sh           # Keycloak Realm/Client/사용자 자동 설정
├── app.py                      # FastAPI 메인 라우터 (37+ 엔드포인트)
├── api_modules/                # 백엔드 비즈니스 로직 모듈
│   ├── database.py             # DB 커넥션 풀 (psycopg2)
│   ├── mes_items.py            # 품목 CRUD
│   ├── mes_bom.py              # BOM 관리/전개/역전개
│   ├── mes_process.py          # 공정/라우팅 관리
│   ├── mes_equipment.py        # 설비 관리/고장예측
│   ├── mes_plan.py             # 생산계획/AI 스케줄링
│   ├── mes_work.py             # 작업지시/실적
│   ├── mes_quality.py          # 품질 관리
│   ├── mes_inventory.py        # 재고 입출고
│   ├── mes_ai_prediction.py    # AI 수요예측
│   ├── mes_defect_predict.py   # AI 불량예측
│   ├── mes_reports.py          # 리포트/AI 인사이트
│   ├── k8s_service.py          # K8s/Hubble API 연동
│   └── sys_logic.py            # 시스템 인프라 로직
├── frontend/
│   └── src/App.jsx             # React 단일 페이지 (14개 메뉴)
├── infra/                      # K8s 매니페스트 파일
│   ├── postgres-pv.yaml        # PV + PVC
│   ├── db-secret.yaml          # DB Secret
│   ├── postgres.yaml           # PostgreSQL
│   ├── keycloak.yaml           # Keycloak 인증 서버
│   ├── mes-api.yaml            # FastAPI 백엔드
│   ├── nginx-config.yaml       # nginx 리버스 프록시
│   └── mes-frontend.yaml       # 프론트엔드
├── doc/                        # 문서
│   ├── ARCH.md                 # 아키텍처 문서
│   ├── HOWTOSTART.md           # VM 부팅 시작 가이드
│   ├── HOWTOCONTRIBUTE.md      # 기여 가이드
│   ├── HANDOVER.md             # 인수인계 문서
│   ├── CODE_REVIEW.md          # 코드 품질 검토서
│   ├── CICD_REVIEW.md          # CI/CD 파이프라인 검토서
│   ├── USER_MANUAL.md          # 사용자 매뉴얼
│   └── MES_PRESENTATION.md    # Marp 발표 자료
└── README.md                   # 이 파일
```

---

## API 엔드포인트

| 영역 | Method | URL | 설명 |
|------|--------|-----|------|
| 품목 | GET | /api/items | 품목 목록 |
| BOM | GET | /api/bom | BOM 전체 목록 |
| BOM | GET | /api/bom/explode/{code} | BOM 전개 |
| BOM | GET | /api/bom/where-used/{code} | 역전개 (사용처) |
| BOM | GET | /api/bom/summary | BOM 통계 요약 |
| 공정 | GET | /api/processes | 공정 마스터 목록 |
| 공정 | GET | /api/routings | 라우팅 요약 (전체) |
| 공정 | GET | /api/routings/{code} | 라우팅 조회 |
| 설비 | GET | /api/equipments | 설비 목록 |
| 계획 | GET | /api/plans | 생산계획 목록 |
| 작업 | GET | /api/work-orders | 작업지시 목록 |
| 품질 | GET | /api/quality/defects | 불량 현황 |
| 재고 | GET | /api/inventory | 재고 현황 |
| AI | POST | /api/ai/demand-prediction/{code} | 수요 예측 |
| AI | POST | /api/ai/defect-prediction | 불량 예측 |
| AI | POST | /api/ai/failure-predict | 고장 예측 |
| 리포트 | GET | /api/reports/production | 생산 리포트 |
| 리포트 | GET | /api/reports/quality | 품질 리포트 |
| 네트워크 | GET | /api/network/hubble-flows | Hubble 플로우 |
| 네트워크 | GET | /api/network/service-map | 서비스 의존성 맵 |
| 인프라 | GET | /api/infra/status | CPU/메모리 상태 |
| K8s | GET | /api/k8s/pods | Pod 목록 |

Swagger UI: `http://<IP>:30461/docs`

---

## 문제 해결 (Troubleshooting)

### K8s API 서버 연결 실패

```bash
# kubelet 상태 확인
systemctl status kubelet

# swap 비활성화 후 재시작
swapoff -a
systemctl restart kubelet

# 30초 후 확인
kubectl get nodes
```

### Pod가 ContainerCreating에서 멈춤

```bash
# Cilium 네트워크 문제 — Pod 재시작
kubectl delete pod -n kube-system -l k8s-app=cilium --force
sleep 10
kubectl get pods
```

### API 서버 응답 없음 (502/Connection Refused)

```bash
# API Pod 로그 확인 — pip install 진행 중일 수 있음
kubectl logs deployment/mes-api --tail=30

# 강제 재배포
kubectl rollout restart deployment mes-api
```

### 프론트엔드 빈 화면

```bash
# ConfigMap 재생성
cd /root/MES_PROJECT/frontend && npm run build
kubectl delete configmap frontend-build
kubectl create configmap frontend-build --from-file=dist/
kubectl rollout restart deployment mes-frontend
```

---

## 변경 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|-----------|
| v5.3 | 2026-02-15 | CI/CD 파이프라인(Jenkinsfile) 재구축, 코드품질/CI/CD 검토서 작성, 로그인 VERIFY_PROFILE 수정, 레거시 k8s/ 정리 |
| v5.2 | 2026-02-14 | Keycloak 인증(OIDC/PKCE), init.sh 통합(하드코딩 제거), env.sh 설정 분리, 레거시 스크립트 정리, 인수인계/기여 문서 추가 |
| v5.1 | 2026-02-13 | BOM 강화(목록/전개/역전개/통계), Process 강화(마스터/라우팅뷰어/요약), 5개 API 추가 |
| v5.0 | 2026-02-13 | 전 테이블 필터 기능, Hubble 네트워크 UI, 원클릭 시작 스크립트 |
| v4.0 | 2026-02-13 | 14개 메뉴 프론트엔드, FN-001~037 전체 구현, 시드 데이터 확장 |
| v3.0 | 2026-02-10 | 모듈화 아키텍처, ConfigMap 배포 방식 전환 |

---

**프로젝트**: 경북대학교 스마트 팩토리 MES
**최종 업데이트**: 2026-02-15
