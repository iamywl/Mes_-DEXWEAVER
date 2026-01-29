# 🏭 스마트 팩토리 MES 프로젝트 요구사항 정의서

본 문서는 경북대학교 실습 환경(K8s)을 기반으로 구축되는 싱글 테넌트 MES 시스템의 요구사항을 정의합니다.

## 1. 프로젝트 개요
* **프로젝트명**: K8s 기반 스마트 팩토리 MES (Kyungpook National Univ.)
* **인프라**: Kubernetes (v1.30+), Cilium (eBPF 기반 네트워크)
* **데이터베이스**: PostgreSQL
* **백엔드/프론트엔드**: Python Flask

## 2. 시스템 아키텍처 (Infrastructure)
* **Containerization**: 모든 서비스는 Docker 컨테이너로 추상화됨.
* **Orchestration**: Kubernetes를 통한 서비스 배포 및 자동 복구(Self-healing).
* **Storage**: ConfigMap을 활용한 소스 코드 동기화 및 DB 연동.

## 3. 기능 요구사항 (Functional Requirements)

### [REQ-001] 데이터베이스 기초 환경 구축
- [x] PostgreSQL 컨테이너 배포 및 `mes_db` 데이터베이스 생성.
- [x] 서비스 재시작 시에도 테이블 스키마 자동 빌드 스크립트 구현.

### [REQ-004] 품목 관리 (Item Management)
- [x] 품목(원자재, 반제품, 완제품) 코드 및 정보 등록.
- [x] 웹 화면을 통한 실시간 품목 리스트 조회.

### [REQ-007] BOM(Bill of Materials) 관리
- [ ] 제품 구성 정보(레시피) 등록 기능.
- [ ] 상위 품목과 하위 품목 간의 조립 관계 설정.

### [REQ-010] 생산 및 설비 모니터링
- [x] 생산 계획(Production Plans) 현황 대시보드 출력.
- [x] 설비(Equipments) 상태(RUN/IDLE) 실시간 모니터링 화면.

## 4. 기술 요구사항 (Technical Requirements)
* **보안**: 컨테이너 간 격리 및 네트워크 정책 적용 고려.
* **자동화**: `start_mes.sh`를 통한 시스템 부팅 및 환경 설정 자동화.
* **버전 관리**: GitHub(`seohannyeong/MES_PROJECT`)를 통한 SSH 기반 협업 및 코드 관리.

## 5. 데이터베이스 스키마 설계
| 테이블명 | 용도 | 비고 |
| :--- | :--- | :--- |
| **items** | 품목 마스터 정보 | PK: item_code |
| **production_plans** | 생산 계획 및 상태 | FK: item_code |
| **processes** | 생산 공정 정의 | - |
| **equipments** | 공장 설비 현황 | - |

---
*최종 업데이트: 2026-01-29*
*작성자: iamywl (Kyungpook National Univ.)*
