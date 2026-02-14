---
marp: true
theme: default
paginate: true
---

# KNU MES

## 클라우드 네이티브 스마트 팩토리 시스템

경북대학교 스마트 팩토리 프로젝트

---

## MES란 무엇인가?

- **MES** (Manufacturing Execution System) : 제조 실행 시스템
- ERP(전사적 자원관리)와 **공장 현장** 사이의 중간 계층
- 생산의 전 과정을 실시간으로 관리하는 핵심 소프트웨어

```
  ERP (경영 계획)
       |
    [ MES ]  <-- 생산 계획 / 실행 / 품질 / 재고 / 보고
       |
  공장 현장 (설비, 센서, 작업자)
```

- 스마트 팩토리 구현의 **핵심 시스템**

---

## 우리의 MES 시스템 개요

| 구분 | 내용 |
|------|------|
| 메뉴 수 | **14개** |
| API 엔드포인트 | **37+ REST API** |
| 아키텍처 | **단일 페이지 웹 애플리케이션 (SPA)** |

**메뉴 구성**

- 대시보드 (1)
- 기준정보 관리 (4) : 품목, BOM, 공정, 설비
- 생산관리 (2) : 생산계획, 작업지시
- 품질/재고 (2) : 품질검사, 재고관리
- AI 분석 (1) : 예측 엔진
- 리포트 (1) : 생산 보고서
- 모니터링 (3) : 인프라, 네트워크, 로그

---

## 인프라 관점 -- 시스템 구동 방식 (1/2)

### Kubernetes 기반 컨테이너 오케스트레이션

```
  +--[ Kubernetes Cluster (kubeadm) ]--+
  |                                     |
  |  Pod: PostgreSQL    (DB)            |
  |  Pod: FastAPI        (백엔드 API)    |
  |  Pod: nginx + React (프론트엔드)     |
  |  Pod: Keycloak      (인증 서버)      |
  |                                     |
  +-------------------------------------+
```

- **Cilium eBPF CNI** : 고성능 네트워크 플러그인
- **Hubble** : 네트워크 플로우 모니터링

---

## 인프라 관점 -- 시스템 구동 방식 (2/2)

### ConfigMap 기반 무중단 배포

- Docker 이미지 재빌드 **불필요**
- 소스 코드를 ConfigMap으로 마운트하여 즉시 반영

### 서비스 노출 (NodePort)

| 서비스 | 포트 |
|--------|------|
| 프론트엔드 (React) | **30173** |
| API (FastAPI) | **30461** |
| Keycloak (인증) | **30080** |

### 운영 자동화

- `init.sh` 하나로 전체 시스템 자동 기동
- `env.sh`로 설정 집중 관리 -- **하드코딩 제로**

---

## 개발자 관점 -- 시스템 구동 방식 (1/2)

### 프론트엔드

- **React 19** + **Vite** (빌드 도구) + **Tailwind CSS 4**
- Keycloak 연동 : `keycloak-js` 라이브러리 사용
- `axios interceptor`로 JWT 토큰 자동 주입

### 백엔드

- **FastAPI** (Python) + **psycopg2** 커넥션 풀
- 모듈화된 `api_modules/` 구조 (기능별 파일 분리)

```
api_modules/
  +-- items.py        (품목 관리)
  +-- bom.py          (BOM 관리)
  +-- process.py      (공정 관리)
  +-- equipment.py    (설비 관리)
  +-- ...
```

---

## 개발자 관점 -- 시스템 구동 방식 (2/2)

### 배포 플로우

```
코드 변경  -->  ConfigMap 재생성  -->  rollout restart  -->  반영 완료
```

- Pod 재시작 시 새 ConfigMap 자동 마운트
- 빌드 과정 없이 **수 초 내 배포** 완료

### 인증 연동

```
사용자 --> React --> Keycloak (OIDC PKCE) --> JWT 발급
                         |
React (axios) --> Authorization: Bearer <JWT> --> FastAPI
```

- PKCE 방식으로 프론트엔드에서 안전하게 인증 처리

---

## 보안 표준 준수

| 항목 | 적용 기술 |
|------|----------|
| 인증 프로토콜 | OAuth 2.0 / OpenID Connect (Keycloak) |
| CSRF 방지 | PKCE (Proof Key for Code Exchange) |
| API 인증 | JWT Bearer 토큰 |
| 교차 출처 | CORS 정책 (env.sh로 동적 설정) |
| DB 자격증명 | Kubernetes Secret 관리 |
| 네트워크 보안 | Cilium eBPF 기반 네트워크 정책 적용 가능 |

- 산업 표준 보안 프로토콜 적용
- 하드코딩된 자격증명 **제로** -- 전부 Secret/env.sh로 관리

---

## 특별한 기능

### AI 예측 엔진
- 수요예측, 불량예측, 고장예측, AI 인사이트

### Hubble 네트워크 모니터링
- 실시간 서비스 맵, 플로우 분석

### 인프라 모니터링
- CPU/메모리 사용량, Pod 상태, 로그 조회

### 데이터 관리
- 전 테이블 **필터/검색** 기능
- BOM 다단계 전개 및 **역전개** (Where-Used)

### UI/UX
- **반응형 다크 테마** UI

---

## 기술 스택 요약

| 계층 | 기술 | 역할 |
|------|------|------|
| 인프라 | Kubernetes (kubeadm) | 컨테이너 오케스트레이션 |
| 네트워크 | Cilium, Hubble | eBPF CNI, 모니터링 |
| DB | PostgreSQL 15 | 관계형 데이터 저장소 |
| 백엔드 | Python FastAPI | REST API 서버 |
| 프론트엔드 | React 19, Vite, Tailwind CSS 4 | SPA 웹 UI |
| 인증 | Keycloak | OIDC / PKCE 인증 |
| 배포 | ConfigMap, init.sh | 무중단 자동 배포 |

---

## 원클릭 부팅 프로세스

`init.sh` 실행 한 번으로 **9단계 자동 처리**

```
1. swap off           (메모리 스왑 비활성화)
2. K8s API 대기       (클러스터 준비 확인)
3. Cilium 복구        (CNI 네트워크 복구)
4. Pod 정리           (기존 리소스 정리)
5. DB 기동            (PostgreSQL 시작)
6. Keycloak 기동      (인증 서버 시작)
7. API 기동           (FastAPI 서버 시작)
8. Frontend 기동      (React 앱 시작)
9. 검증               (헬스 체크 및 확인)
```

- 약 **2~5분** 내 전체 시스템 기동 완료

---

## 향후 발전 방향

- **RBAC 세분화**
  - Role-Based Access Control을 통한 메뉴/기능별 권한 제어

- **CI/CD 파이프라인 자동화**
  - Git push 시 자동 빌드, 테스트, 배포

- **멀티 노드 K8s 클러스터 확장**
  - 고가용성(HA) 및 부하 분산 구성

- **실제 PLC/IoT 디바이스 연동**
  - 공장 설비에서 실시간 데이터 수집

- **대시보드 실시간 업데이트**
  - WebSocket 기반 실시간 데이터 반영

---

# 감사합니다

**KNU MES** -- 클라우드 네이티브 스마트 팩토리 시스템

경북대학교 스마트 팩토리 프로젝트
