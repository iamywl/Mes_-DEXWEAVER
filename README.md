## 🛠 개발 환경 구축 (Docker)

본 프로젝트는 팀원 간 동일한 DB 환경을 유지하기 위해 Docker를 사용합니다. 
아래 순서에 따라 데이터베이스를 실행해 주세요.

### 1. 전제 조건
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)이 설치 및 실행 중이어야 합니다.
- 5433 포트가 사용 가능해야 합니다. (로컬 PostgreSQL과 충돌 방지)

### 2. 실행 방법
터미널에서 프로젝트 루트 폴더로 이동한 후 아래 명령어를 입력하세요.

```bash
# 컨테이너 실행 및 DB 초기화 (백그라운드 모드)
docker-compose up -d
