# DEXWEAVER MES v4.0 — 스마트 팩토리 Manufacturing Execution System

> Kubernetes 기반 클라우드 네이티브 MES 시스템 (GS인증 표준 준수)

---

## 빠른 시작

```bash
# VM 접속
ssh c1_master1@192.168.64.5
sudo -s

# 원클릭 시작 (실시간 프로그레스 바 표시)
bash /root/MES_PROJECT/init.sh
```

시작 후 접속:

| 서비스 | URL |
|--------|-----|
| 웹 UI | `http://192.168.64.5:30173` |
| API 문서 (Swagger) | `http://192.168.64.5:30461/api/docs` |
| 건강체크 (Health) | `http://192.168.64.5:30461/api/health` |

테스트 계정: `admin` / `admin1234`, `worker01` / `worker1234`, `viewer01` / `viewer1234`

> 상세 가이드: [doc/HOWTOSTART.md](doc/HOWTOSTART.md)

---

## 문서 가이드

| 문서 | 설명 | 대상 |
|------|------|------|
| **[doc/HOWTOSTART.md](doc/HOWTOSTART.md)** | VM 부팅 후 시스템 기동 절차, 상태 확인, 트러블슈팅 | 운영자 |
| **[doc/ARCH.md](doc/ARCH.md)** | 시스템 아키텍처, K8s 리소스, DB 스키마, API 전체 목록 | 개발자 |
| **[doc/HANDOVER.md](doc/HANDOVER.md)** | 개발자 인수인계 — 디렉터리 구조, 동작 흐름, 배포 방법, 주의사항 | 신규 개발자 |
| **[doc/HOWTOCONTRIBUTE.md](doc/HOWTOCONTRIBUTE.md)** | 개발 환경 설정, 코드 컨벤션, 브랜치 전략, PR 워크플로우 | 기여자 |
| **[doc/CODE_REVIEW.md](doc/CODE_REVIEW.md)** | PEP8/JS/Shell/K8s 코딩 표준 준수 검토 보고서 | 리뷰어 |
| **[doc/CICD_REVIEW.md](doc/CICD_REVIEW.md)** | Jenkins CI/CD 파이프라인 구축 현황 및 개선 사항 | DevOps |

---

## 시스템 개요

14개 메뉴, 37+ API 엔드포인트로 구성된 통합 제조 실행 시스템입니다.

| 영역 | 메뉴 | 주요 기능 |
|------|------|-----------|
| 기준정보 | Items, BOM, Process, Equipment | 품목/BOM(목록, 전개, 역전개)/공정(마스터, 라우팅, 요약)/설비 관리 |
| 생산관리 | Plans, Work Order | 생산계획, 작업지시/실적 |
| 품질/재고 | Quality, Inventory | 불량 분석, 재고 현황 |
| AI 분석 | AI Center | 수요예측, 불량예측, 고장예측 |
| 리포트 | Reports | 생산/품질 리포트, AI 인사이트 |
| 모니터링 | Network, Infra, K8s | Hubble 서비스맵, 인프라, Pod 관리 |

> 전체 아키텍처 및 DB 스키마: [doc/ARCH.md](doc/ARCH.md)

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
| CI/CD | Jenkins (Jenkinsfile) | - |
| 배포 방식 | ConfigMap 기반 (Docker 빌드 불필요) | - |

---

## 부팅 최적화 (v5.4)

`init.sh`는 병렬 배포 + 캐시 + 실시간 프로그레스 바로 최적화되어 있습니다.

```
  [1:23] ████████████░░░░░░░░ 60%  ● ● ● ● ● ● ◉ ○ ○ ○ ○ 백엔드
```

| 최적화 | 내용 |
|--------|------|
| 병렬 배포 | DB/Keycloak/Backend를 동시에 K8s apply |
| 프론트 빌드 캐시 | `dist/` 존재 시 빌드 스킵 (소스 변경 감지 시만 재빌드) |
| pip 캐시 | hostPath 볼륨으로 패키지 캐시 재사용 |
| 병렬 Health Check | 프론트/API/Keycloak 상태를 백그라운드에서 동시 확인 |
| Cilium 스킵 | 이미 Running이면 네트워크 재시작 건너뜀 |
| 프로그레스 바 | 경과시간 + 진행률 + 단계별 상태 아이콘 실시간 표시 |

> 부팅 흐름 상세: [doc/HOWTOSTART.md](doc/HOWTOSTART.md)

---

## 프로젝트 구조

```
MES_PROJECT/
├── init.sh                     # 통합 초기화 스크립트 (최적화 버전)
├── env.sh                      # 환경 변수 + 프로그레스 바 유틸
├── setup-keycloak.sh           # Keycloak Realm/Client/사용자 자동 설정
├── app.py                      # FastAPI 메인 라우터 (37+ 엔드포인트)
├── api_modules/                # 백엔드 비즈니스 로직 모듈
├── frontend/
│   └── src/App.jsx             # React 단일 페이지 (14개 메뉴)
├── infra/                      # K8s 매니페스트 (7개 YAML)
├── db/
│   └── init.sql                # DB 스키마 + 시드 데이터 (21개 테이블)
├── doc/                        # 프로젝트 문서
│   ├── HOWTOSTART.md           # VM 부팅 시작 가이드
│   ├── ARCH.md                 # 아키텍처 문서
│   ├── HANDOVER.md             # 인수인계 문서
│   ├── HOWTOCONTRIBUTE.md      # 기여 가이드
│   ├── CODE_REVIEW.md          # 코드 품질 검토서
│   └── CICD_REVIEW.md          # CI/CD 파이프라인 검토서
├── Jenkinsfile                 # CI/CD 파이프라인
└── README.md                   # 이 파일
```

> 파일별 상세 역할: [doc/HANDOVER.md](doc/HANDOVER.md)

---

## API 엔드포인트 (주요)

| 영역 | Method | URL | 설명 |
|------|--------|-----|------|
| 품목 | GET | /api/items | 품목 목록 |
| BOM | GET | /api/bom | BOM 전체 목록 |
| BOM | GET | /api/bom/explode/{code} | BOM 전개 |
| BOM | GET | /api/bom/where-used/{code} | 역전개 (사용처) |
| 공정 | GET | /api/processes | 공정 마스터 목록 |
| 라우팅 | GET | /api/routings/{code} | 품목별 라우팅 조회 |
| 설비 | GET | /api/equipments | 설비 목록 |
| 계획 | GET | /api/plans | 생산계획 목록 |
| 작업 | GET | /api/work-orders | 작업지시 목록 |
| 품질 | GET | /api/quality/defects | 불량 현황 |
| 재고 | GET | /api/inventory | 재고 현황 |
| AI | POST | /api/ai/demand-prediction/{code} | 수요 예측 |
| AI | POST | /api/ai/defect-prediction | 불량 예측 |
| AI | POST | /api/ai/failure-predict | 고장 예측 |
| 리포트 | GET | /api/reports/production | 생산 리포트 |
| 인프라 | GET | /api/infra/status | CPU/메모리 상태 |
| K8s | GET | /api/k8s/pods | Pod 목록 |

Swagger UI: `http://<IP>:30461/docs` — 전체 37+ 엔드포인트 목록은 [doc/ARCH.md](doc/ARCH.md#4-백엔드-아키텍처) 참조

---

## 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| K8s API 연결 실패 | swap 활성화 | `swapoff -a && systemctl restart kubelet` |
| Pod ContainerCreating 멈춤 | Cilium 네트워크 초기화 실패 | `kubectl delete pod -n kube-system -l k8s-app=cilium --force` |
| API 502 에러 | pip install 진행 중 (1~2분 소요) | `kubectl logs deployment/mes-api --tail=30` 으로 진행 확인 |
| 프론트엔드 빈 화면 | ConfigMap 미반영 | `npm run build` 후 ConfigMap 재생성 + rollout restart |

> 상세 트러블슈팅: [doc/HOWTOSTART.md](doc/HOWTOSTART.md#문제-해결-troubleshooting)

---

## 변경 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|-----------|
| v5.4 | 2026-02-23 | 부팅 최적화(병렬 배포, 프론트 빌드 캐시, pip 캐시, 병렬 Health Check), 실시간 프로그레스 바, 문서 정비 |
| v5.3 | 2026-02-15 | CI/CD 파이프라인(Jenkinsfile) 재구축, 코드품질/CI/CD 검토서 작성, 레거시 k8s/ 정리 |
| v5.2 | 2026-02-14 | Keycloak 인증(OIDC/PKCE), init.sh 통합, env.sh 설정 분리, 인수인계/기여 문서 |
| v5.1 | 2026-02-13 | BOM/Process 강화(목록/전개/역전개/통계/라우팅), 5개 API 추가 |
| v5.0 | 2026-02-13 | 전 테이블 필터, Hubble 네트워크 UI, 원클릭 시작 스크립트 |
| v4.0 | 2026-02-13 | 14개 메뉴 프론트엔드, FN-001~037 전체 구현 |
| v3.0 | 2026-02-10 | 모듈화 아키텍처, ConfigMap 배포 방식 전환 |

---

**프로젝트**: 경북대학교 스마트 팩토리 MES
**최종 업데이트**: 2026-02-23
