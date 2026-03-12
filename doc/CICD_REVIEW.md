# KNU MES — CI/CD 파이프라인 검토 보고서

> 작성일: 2026-02-15
> 검토 대상: Jenkinsfile, docker-compose.yml, k8s/ 디렉터리, test_app.py, requirements.txt, frontend/frontend.Dockerfile

---

## 1. 검토 결과 요약

| 항목 | 상태 | 평가 |
|------|------|------|
| **Jenkinsfile** | 존재하지만 구조 불일치 | **재작성 완료** |
| **테스트 (test_app.py)** | 25개 테스트 존재 | 부분 커버리지 (인프라/AI만) |
| **GitHub Actions / GitLab CI** | 없음 | Jenkins 단독 |
| **docker-compose.yml** | 레거시 (postgres only) | 로컬 개발용으로 유지 |
| **k8s/ 디렉터리** | 레거시 (infra/와 중복) | 정리 대상 |
| **requirements.txt** | 존재 | pydantic 누락 → 수정 완료 |
| **frontend.Dockerfile** | 존재 | Docker 빌드 방식 사용 시 참고용 |
| **코드 린팅 도구** | Jenkinsfile에서 설치 | black, flake8, isort, eslint |

### 총평

> **CI/CD 파이프라인은 "골격만 존재"하는 상태였습니다.**
>
> 기존 Jenkinsfile은 Docker 이미지 빌드 + 레지스트리 Push 방식으로 작성되어 있었으나,
> 실제 배포는 **ConfigMap 기반**(Docker 빌드 없음)으로 수행되고 있어 **완전히 불일치**했습니다.
> 이번 검토를 통해 현행 아키텍처에 맞게 Jenkinsfile을 재작성했습니다.

---

## 1-A. Jenkins 파이프라인 실행 엔진 — 심층 분석

### 1-A-1. Jenkinsfile 파싱 과정

Jenkins는 Declarative Pipeline(Jenkinsfile)을 다음 단계로 처리한다.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Jenkinsfile 파싱 → 실행 흐름                         │
│                                                                     │
│  Jenkinsfile (Groovy DSL 텍스트)                                     │
│       │                                                             │
│       ▼                                                             │
│  [1] Groovy CPS Compiler                                            │
│       │  - Continuation-Passing Style로 변환                         │
│       │  - 각 statement를 직렬화 가능한 Continuation 객체로 래핑       │
│       │  - Jenkins 재시작 시에도 파이프라인 상태 복원 가능              │
│       ▼                                                             │
│  [2] Pipeline Model Definition (Declarative 전용)                    │
│       │  - pipeline {} 블록을 ModelASTPipelineDef 객체로 파싱          │
│       │  - stages, agent, post, environment 등 구조적 검증            │
│       │  - 문법 오류 시 파이프라인 시작 전 즉시 실패                    │
│       ▼                                                             │
│  [3] Stage Graph 생성                                                │
│       │  - 각 stage → FlowNode 매핑                                  │
│       │  - FlowNode는 DAG(방향 비순환 그래프) 형태                    │
│       │  - parallel {} 블록은 ParallelStep으로 분기                   │
│       ▼                                                             │
│  [4] FlowGraphTable (실행 계획)                                      │
│       │  - 노드 간 의존성 정의                                        │
│       │  - 각 노드에 실행 환경(agent), 조건(when) 바인딩               │
│       ▼                                                             │
│  [5] CPS VM Thread에서 순차 실행                                      │
│       - 각 step 호출 시 StepExecution 객체 생성                       │
│       - I/O 블로킹 step은 비동기 콜백으로 처리 (sh, bat 등)            │
│       - 콜백 완료 시 다음 Continuation 호출                           │
└─────────────────────────────────────────────────────────────────────┘
```

**핵심 메커니즘 — CPS(Continuation-Passing Style)**:
일반 Groovy 코드와 달리 Jenkins Pipeline Groovy는 CPS 변환을 거친다. 이유는 Jenkins 컨트롤러(마스터)가 재시작되더라도 파이프라인 실행 상태를 디스크에서 복원할 수 있어야 하기 때문이다. 모든 로컬 변수, 호출 스택이 직렬화 가능한 Continuation 객체 체인으로 변환되며, `@NonCPS` 어노테이션이 붙은 함수만 이 변환에서 제외된다.

### 1-A-2. agent 블록의 실행 환경 결정 메커니즘

```
┌─────────────────────────────────────────────────────────────────┐
│  agent { label 'k8s-worker' }  →  실행 환경 할당 과정            │
│                                                                 │
│  [1] Label Expression 평가                                      │
│       │  - "k8s-worker" 라벨을 가진 노드(에이전트) 검색           │
│       │  - 복합 표현식 가능: "linux && docker && !gpu"            │
│       ▼                                                         │
│  [2] Node Provisioning                                          │
│       │  - Cloud 플러그인(K8s Plugin 등) → 동적 에이전트 생성     │
│       │  - 정적 에이전트: 기존 연결된 에이전트에서 선택            │
│       │  - 큐에 빌드 대기 → 노드 가용 시 할당                    │
│       ▼                                                         │
│  [3] Workspace 생성                                              │
│       │  - 기본 경로: /home/jenkins/workspace/<job-name>         │
│       │  - 동일 노드에서 같은 Job 동시 실행 시 @2, @3 접미사      │
│       │  - SCM checkout으로 소스코드 클론                         │
│       ▼                                                         │
│  [4] 환경 변수 주입                                              │
│       │  - environment {} 블록 → 프로세스 env로 전달              │
│       │  - credentials() → Jenkins Credential Store에서 복호화    │
│       │  - WORKSPACE, BUILD_NUMBER 등 빌트인 변수                │
│       ▼                                                         │
│  [5] Stage 실행 시작                                             │
│       - 해당 노드의 executor에서 sh/bat step 실행                 │
│       - agent none 시: 각 stage별 개별 agent 필요                 │
│       - agent가 stage 레벨에 있으면 해당 stage만 그 노드에서 실행  │
└─────────────────────────────────────────────────────────────────┘
```

### 1-A-3. Stage/Step 실행 흐름

**Sequential Stages** (기본):
```groovy
stages {
    stage('Lint')  { ... }  // 완료 후 →
    stage('Test')  { ... }  // 완료 후 →
    stage('Build') { ... }  // 완료 후 →
    stage('Deploy'){ ... }
}
```
각 stage는 이전 stage가 성공한 경우에만 실행된다. 하나라도 실패하면 후속 stage는 스킵되고 post { failure {} } 블록이 실행된다.

**Parallel Stages**:
```groovy
stage('Lint & Test') {
    parallel {
        stage('Backend Lint')  { steps { sh 'black --check .' } }
        stage('Frontend Lint') { steps { sh 'npx eslint src/' } }
        stage('Backend Test')  { steps { sh 'pytest' } }
    }
    // 모든 병렬 stage 완료 후 다음 stage로 진행
    // failFast true 옵션: 하나라도 실패 시 나머지 즉시 중단
}
```

**stash/unstash 패턴** — 서로 다른 agent 간 파일 전달:
```groovy
stage('Build FE') {
    agent { label 'node-builder' }
    steps {
        sh 'npm run build'
        stash includes: 'dist/**', name: 'frontend-build'
        // dist/ 디렉터리를 Jenkins 마스터 메모리에 임시 저장
    }
}
stage('Deploy FE') {
    agent { label 'k8s-deployer' }
    steps {
        unstash 'frontend-build'
        // Jenkins 마스터에서 현재 workspace로 파일 복원
        sh 'kubectl create configmap frontend-build --from-file=dist/'
    }
}
```

### 1-A-4. post 블록 실행 조건

```
┌──────────────────────────────────────────────────┐
│  post 블록 실행 매트릭스                           │
│                                                  │
│  빌드 결과         │ 실행되는 post 조건             │
│  ─────────────────┼────────────────────────────── │
│  SUCCESS           │ always, success, changed(*)  │
│  FAILURE           │ always, failure, changed(*)  │
│  UNSTABLE          │ always, unstable, changed(*) │
│  ABORTED           │ always, aborted             │
│                                                  │
│  (*) changed: 이전 빌드와 결과가 다를 때 실행       │
│                                                  │
│  실행 순서:                                       │
│  always → success/failure/unstable → changed      │
│  → fixed/regression → cleanup                    │
│                                                  │
│  cleanup: 다른 모든 post 조건 실행 후 마지막 실행   │
│           (workspace 정리 등에 활용)               │
└──────────────────────────────────────────────────┘
```

---

## 2. 기존 Jenkinsfile 문제점 분석

### 2.1 치명적 문제 (CRITICAL)

| # | 문제 | 영향 |
|---|------|------|
| C-01 | `DOCKER_REGISTRY = "your-docker-repo"` 플레이스홀더 | Docker Push 단계에서 100% 실패 |
| C-02 | `k8s/backend-service.yaml` 참조 (레거시 경로) | `infra/` 디렉터리와 불일치, 배포 실패 |
| C-03 | Docker 빌드 방식 ↔ ConfigMap 방식 불일치 | 실제 운영 배포 흐름과 완전 다름 |
| C-04 | Keycloak 배포 단계 없음 | 인증 서버 미배포 |
| C-05 | CORS_ORIGINS 처리 없음 | API 서버 CORS 오류 |

### 2.2 경고 (WARNING)

| # | 문제 | 영향 |
|---|------|------|
| W-01 | 거의 모든 명령에 `\|\| true` 적용 | 실패가 마스킹되어 디버깅 불가 |
| W-02 | `port: 8000` 하드코딩 (backend-service.yaml) | 실제 API는 port 80 사용 |
| W-03 | `env.sh` 미활용 | 하드코딩된 설정값 |
| W-04 | `requirements.txt`에 pydantic 누락 | pip install 시 누락 가능 |
| W-05 | 프론트엔드 Docker 빌드 방식 | 실제는 ConfigMap 방식 사용 |

### 2.3 정보 (INFO)

| # | 항목 | 상세 |
|---|------|------|
| I-01 | Lint 단계 존재 | black, flake8, isort, eslint 설치 및 실행 |
| I-02 | 테스트 단계 존재 | pytest, npm test 실행 |
| I-03 | IP 자동 감지 | `hostname -I` 사용 |
| I-04 | 배포 검증 단계 존재 | kubectl get pods/svc 확인 |

### 2-A. 린팅 도구 내부 동작 — 심층 분석

#### (1) Black — Python 코드 포매터

```
┌──────────────────────────────────────────────────────────────────┐
│  black --check app.py 실행 흐름                                   │
│                                                                  │
│  [1] 소스 파일 읽기 + 인코딩 감지 (UTF-8 기본)                    │
│       │                                                          │
│       ▼                                                          │
│  [2] Python AST 파싱 (lib2to3 기반 CST 파서 사용)                 │
│       │  - AST(Abstract Syntax Tree): 구문 구조만 보존             │
│       │  - CST(Concrete Syntax Tree): 공백, 주석, 괄호까지 보존    │
│       │  - Black은 CST를 사용하여 주석/문자열을 유지하면서 포매팅   │
│       ▼                                                          │
│  [3] Line Length 최적화 알고리즘                                   │
│       │  - 목표: 88자 이내 (기본값)                                │
│       │  - 전략: "모든 것을 한 줄에 넣거나, 각 요소를 개별 줄로"    │
│       │  - Magic Trailing Comma: 마지막 쉼표 있으면 무조건 분리     │
│       │  - 중첩 괄호에서 최소 분리점을 탐색 (비용 함수 최적화)      │
│       ▼                                                          │
│  [4] 문자열 정규화                                                │
│       │  - 작은따옴표 → 큰따옴표 (기본)                            │
│       │  - f-string 내부는 건드리지 않음                            │
│       ▼                                                          │
│  [5] AST 동등성 검증 (안전 장치)                                   │
│       │  - 포매팅 전후 AST를 비교                                  │
│       │  - 불일치 시 포매팅 거부 (코드 의미 변경 방지)              │
│       ▼                                                          │
│  [6] --check 모드: 변경 필요 시 exit code 1 반환 (파일 미수정)     │
│      일반 모드: 포매팅된 결과로 파일 덮어쓰기                      │
└──────────────────────────────────────────────────────────────────┘
```

#### (2) flake8 — Python 린터 (메타 도구)

```
┌──────────────────────────────────────────────────────────────────┐
│  flake8의 3개 내장 검사기 조합                                     │
│                                                                  │
│  ┌──────────────────────┐                                        │
│  │ pycodestyle (E/W)    │  PEP 8 스타일 검사                      │
│  │ - E501: 줄 길이 초과  │  - 토큰 기반 검사 (AST 불필요)         │
│  │ - W291: 후행 공백    │  - 각 물리적 줄을 정규표현식으로 검사    │
│  │ - E302: 빈 줄 부족   │                                        │
│  └──────────┬───────────┘                                        │
│             │                                                    │
│  ┌──────────┴───────────┐                                        │
│  │ pyflakes (F)         │  논리적 오류 검사                       │
│  │ - F401: 미사용 import │  - AST 파싱 기반                       │
│  │ - F841: 미사용 변수   │  - 스코프 분석 (바인딩/참조 추적)      │
│  │ - F811: 재정의       │  - import 그래프 구축                   │
│  └──────────┬───────────┘                                        │
│             │                                                    │
│  ┌──────────┴───────────┐                                        │
│  │ mccabe (C)           │  복잡도 검사                            │
│  │ - C901: 함수 복잡도   │  - AST 순회로 분기점 카운트             │
│  │   ≥ 10이면 경고      │  - McCabe Cyclomatic Complexity 계산   │
│  │                      │  - if/for/while/except/and/or 각 +1    │
│  └──────────────────────┘                                        │
│                                                                  │
│  실행 흐름:                                                       │
│  1. flake8 CLI → FileChecker 객체 생성 (파일당 1개)               │
│  2. 멀티프로세싱으로 병렬 검사 (--jobs=auto)                       │
│  3. 각 검사기의 결과를 통합 → 라인:컬럼:코드:메시지 출력           │
│  4. --max-line-length, --ignore, --select로 규칙 커스터마이징      │
└──────────────────────────────────────────────────────────────────┘
```

#### (3) ESLint — JavaScript/JSX 린터

```
┌──────────────────────────────────────────────────────────────────┐
│  npx eslint src/App.jsx 실행 흐름                                 │
│                                                                  │
│  [1] 설정 로드 (.eslintrc.* / eslint.config.js)                   │
│       │  - Flat Config (v9+) 또는 Legacy Config                   │
│       │  - extends, plugins, rules 해석                           │
│       ▼                                                          │
│  [2] Parser 실행 (기본: espree)                                   │
│       │  - espree = acorn 기반 ECMAScript 파서                    │
│       │  - JSX 지원: espree의 jsx 옵션 활성화                     │
│       │  - TypeScript: @typescript-eslint/parser 사용 시           │
│       │    ts.createProgram()으로 타입 정보까지 제공               │
│       │  - 결과: ESTree 호환 AST                                  │
│       ▼                                                          │
│  [3] AST 순회 + Rule Visitor 실행                                 │
│       │  ┌─────────────────────────────────────────────────┐     │
│       │  │ Rule = { create(context) {                      │     │
│       │  │   return {                                      │     │
│       │  │     // Visitor 패턴: AST 노드 타입별 핸들러       │     │
│       │  │     FunctionDeclaration(node) { ... },          │     │
│       │  │     VariableDeclarator(node) { ... },           │     │
│       │  │     ImportDeclaration(node) { ... },            │     │
│       │  │   }                                             │     │
│       │  │ }}                                              │     │
│       │  └─────────────────────────────────────────────────┘     │
│       │                                                          │
│       │  - Linter가 AST를 DFS(깊이우선) 순회                     │
│       │  - 각 노드 방문 시 해당 타입에 등록된 모든 rule 콜백 실행  │
│       │  - rule 내에서 context.report()로 위반 보고                │
│       ▼                                                          │
│  [4] 결과 수집 + Formatter 적용                                   │
│       - 기본: stylish 포맷 (컬러 테이블 출력)                     │
│       - --fix 옵션: 자동 수정 가능한 위반을 AST 조작으로 수정     │
│       - exit code: 0 (clean), 1 (warning), 2 (error)             │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 수행된 조치

### 3.1 Jenkinsfile 재작성

**변경 전**: Docker 빌드 + Registry Push + 레거시 k8s/ YAML 참조
**변경 후**: ConfigMap 기반 배포 (init.sh 아키텍처와 동일)

| 단계 | 변경 전 | 변경 후 |
|------|---------|---------|
| 환경 설정 | `DOCKER_REGISTRY` 플레이스홀더 | `env.sh` source |
| 린팅 | `\|\| true`로 실패 무시 | 경고만 출력 (빌드 실패하지 않음) |
| 테스트 | pytest + npm test | pytest + npm test (동일) |
| 백엔드 빌드 | Docker 이미지 빌드 | **제거** (ConfigMap 방식) |
| 프론트엔드 빌드 | Docker 이미지 빌드 | `npm run build` (ConfigMap용) |
| DB 배포 | 없음 | `infra/postgres-pv.yaml` + `postgres.yaml` |
| Keycloak | 없음 | **추가**: `infra/keycloak.yaml` + `setup-keycloak.sh` |
| 백엔드 배포 | Docker 이미지 → k8s/ YAML | ConfigMap(`api-code`) + `infra/mes-api.yaml` |
| 프론트엔드 배포 | Docker 이미지 → k8s/ YAML | ConfigMap(`frontend-build`) + `infra/mes-frontend.yaml` |
| 검증 | kubectl get pods/svc | HTTP 200 응답 확인 포함 |

### 3.1-A. ConfigMap 기반 배포가 작동하는 원리 — 심층 분석

#### (1) `kubectl create configmap --from-file` 내부 동작

```
┌──────────────────────────────────────────────────────────────────────────┐
│  kubectl create configmap api-code --from-file=app.py                    │
│                                                                          │
│  [단계 1] 클라이언트 측 (kubectl)                                         │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 1. 파일 시스템에서 app.py 읽기 (바이너리 → UTF-8 텍스트)            │  │
│  │ 2. ConfigMap manifest 생성:                                        │  │
│  │    {                                                               │  │
│  │      "apiVersion": "v1",                                          │  │
│  │      "kind": "ConfigMap",                                         │  │
│  │      "metadata": { "name": "api-code", "namespace": "default" },  │  │
│  │      "data": {         ← 텍스트 데이터 (UTF-8)                     │  │
│  │        "app.py": "import fastapi\n..."                            │  │
│  │      }                                                            │  │
│  │    }                                                               │  │
│  │    ※ data 필드: 텍스트 (base64 인코딩 안 함)                       │  │
│  │    ※ binaryData 필드: 바이너리 파일일 경우 base64 인코딩           │  │
│  │                                                                    │  │
│  │ 3. JSON 직렬화 → HTTP POST /api/v1/namespaces/default/configmaps  │  │
│  │    - Content-Type: application/json                                │  │
│  │    - Authorization: Bearer <token> (kubeconfig에서 로드)           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              ▼                                           │
│  [단계 2] API Server 처리                                                │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Authentication: Bearer 토큰 / 클라이언트 인증서 검증             │  │
│  │ 2. Authorization: RBAC 규칙으로 configmaps create 권한 확인         │  │
│  │ 3. Admission Controllers (순차 실행):                               │  │
│  │    - MutatingAdmissionWebhook: 리소스 수정 가능 (라벨 추가 등)      │  │
│  │    - ValidatingAdmissionWebhook: 정책 검증 (OPA/Gatekeeper 등)     │  │
│  │    - ResourceQuota: 네임스페이스 리소스 한도 확인                    │  │
│  │    - LimitRange: ConfigMap 크기 제한 확인 (기본 1MB)               │  │
│  │ 4. Validation: 스키마 검증 (키 이름 규칙, 데이터 크기 등)           │  │
│  │ 5. etcd 저장: /registry/configmaps/default/api-code                │  │
│  │    - 값은 protobuf 직렬화 + 선택적 암호화(EncryptionConfiguration) │  │
│  │ 6. 201 Created 응답 반환                                           │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                              │                                           │
│                              ▼                                           │
│  [단계 3] Watch 이벤트 전파                                              │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ - kubelet이 API Server를 watch 중                                  │  │
│  │ - ConfigMap 변경 감지 → 해당 ConfigMap을 마운트한 Pod에 반영        │  │
│  │ - 단, subPath 마운트 시 자동 갱신 안 됨 (rollout restart 필요)      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

#### (2) `kubectl rollout restart` 메커니즘

```
┌──────────────────────────────────────────────────────────────────────────┐
│  kubectl rollout restart deployment/mes-api                              │
│                                                                          │
│  [1] kubectl이 Deployment의 pod template에 어노테이션 추가:              │
│      spec.template.metadata.annotations:                                 │
│        kubectl.kubernetes.io/restartedAt: "2026-03-12T09:30:00Z"         │
│      → 이것만으로 pod template이 변경된 것으로 간주됨                     │
│                                                                          │
│  [2] Deployment Controller (kube-controller-manager 내부) 동작:          │
│      ┌────────────────────────────────────────────────────────────┐      │
│      │ a. pod template hash 재계산                                │      │
│      │    - 새 hash ≠ 기존 ReplicaSet hash → 새 ReplicaSet 생성  │      │
│      │                                                            │      │
│      │ b. 롤링 업데이트 전략 적용 (RollingUpdate):                 │      │
│      │    - maxSurge: 25% (기본) → 원래 replicas 수 이상 추가      │      │
│      │      가능한 Pod 수. replicas=4이면 최대 5개까지 동시 존재    │      │
│      │    - maxUnavailable: 25% (기본) → 업데이트 중 사용 불가     │      │
│      │      허용 Pod 수. replicas=4이면 최소 3개는 Running 유지    │      │
│      │                                                            │      │
│      │ c. Pod 교체 순서:                                           │      │
│      │    ┌──────────────────────────────────────────────┐        │      │
│      │    │ T0: Old RS(4 pods), New RS(0 pods)           │        │      │
│      │    │ T1: New RS → 1 pod 생성 (surge)              │        │      │
│      │    │     New pod Ready 확인 (readinessProbe)      │        │      │
│      │    │ T2: Old RS → 1 pod 종료                      │        │      │
│      │    │     (terminationGracePeriodSeconds 대기)     │        │      │
│      │    │ T3: New RS → 다음 pod 생성                   │        │      │
│      │    │     ... 반복 ...                              │        │      │
│      │    │ Tn: Old RS(0 pods), New RS(4 pods) → 완료    │        │      │
│      │    └──────────────────────────────────────────────┘        │      │
│      └────────────────────────────────────────────────────────────┘      │
│                                                                          │
│  [3] 새 Pod에서 ConfigMap Volume 마운트 과정:                            │
│      ┌────────────────────────────────────────────────────────────┐      │
│      │ a. kubelet이 Pod spec 수신                                 │      │
│      │ b. Volume Plugin (configmap type) 호출                     │      │
│      │ c. API Server에서 최신 ConfigMap 데이터 fetch               │      │
│      │ d. Pod의 volumeMount 경로에 파일로 마운트:                  │      │
│      │    /app/app.py ← ConfigMap "api-code"의 "app.py" 키       │      │
│      │ e. 컨테이너 프로세스 시작 (python app.py 등)               │      │
│      │ f. 최신 코드로 실행됨                                      │      │
│      └────────────────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────────┘
```

**ConfigMap 크기 제한**: 단일 ConfigMap은 **1MB** (1,048,576 bytes)까지 저장 가능하다. 이 프로젝트의 app.py(약 30KB)와 프론트엔드 빌드 결과물은 이 한도 내에서 충분히 처리된다. 한도 초과 시 별도 PV/PVC 또는 initContainer 기반 다운로드 방식을 고려해야 한다.

### 3.2 requirements.txt 수정

```diff
+ pydantic>=2.0
```

### 3.3 레거시 파일 정리

| 파일/디렉터리 | 조치 | 사유 |
|-------------|------|------|
| `k8s/` 디렉터리 | 삭제 | `infra/`와 완전 중복, `your-docker-repo` 플레이스홀더 |
| `docker-compose.yml` | 유지 | 로컬 개발용 PostgreSQL로 활용 가능 |
| `frontend/frontend.Dockerfile` | 유지 | Docker 빌드 방식 전환 시 참고용 |

---

## 4. 테스트 커버리지 현황

### 4.1 현재 테스트 범위 (test_app.py — 25개)

| 테스트 클래스 | 테스트 수 | 대상 |
|--------------|----------|------|
| TestMESDataEndpoints | 8 | 인프라/네트워크/K8s API |
| TestErrorHandling | 4 | 404/405 에러 |
| TestResponseFormat | 5 | JSON 스키마 |
| TestNetworkTopology | 3 | 토폴로지 집계 |
| TestInfraStatusParsing | 3 | 파싱 로직 |
| TestAIPrediction | 2 | AI 예측 |

### 4.2 미커버 영역

| 미커버 API | 엔드포인트 | 비고 |
|-----------|-----------|------|
| 품목 CRUD | `/api/items` (GET/POST/PUT) | DB 의존 |
| BOM | `/api/bom`, `/api/bom/explode`, `/api/bom/where-used` | DB 의존 |
| 공정/라우팅 | `/api/processes`, `/api/routings` | DB 의존 |
| 설비 | `/api/equipments` | DB 의존 |
| 생산계획 | `/api/plans` | DB 의존 |
| 작업지시/실적 | `/api/work-orders`, `/api/work-results` | DB 의존 |
| 품질 | `/api/quality/*` | DB 의존 |
| 재고 | `/api/inventory/*` | DB 의존 |
| 리포트 | `/api/reports/*` | DB 의존 |
| 인증 | `/api/auth/*` | DB 의존 |

> **참고**: DB 의존 테스트는 테스트 DB(mock 또는 별도 PostgreSQL)를 구성해야 합니다.
> 현재 테스트는 DB 연결 없이 실행 가능한 엔드포인트만 대상으로 합니다.

### 4-A. 테스트 실행 메커니즘 — 심층 분석

#### (1) pytest 수집/실행 원리

```
┌──────────────────────────────────────────────────────────────────────┐
│  pytest test_app.py 실행 흐름                                         │
│                                                                      │
│  ══════════════════════════════════════════════════════════════════   │
│  Phase 1: Collection (테스트 수집)                                    │
│  ══════════════════════════════════════════════════════════════════   │
│                                                                      │
│  [1] conftest.py 탐색 (루트 → 하위 디렉터리 순)                       │
│       │  - 각 conftest.py의 fixture, hook, plugin 등록                │
│       ▼                                                              │
│  [2] 테스트 파일 탐색                                                 │
│       │  - 패턴: test_*.py 또는 *_test.py (설정 가능)                 │
│       │  - 재귀적으로 디렉터리 탐색                                   │
│       ▼                                                              │
│  [3] 테스트 항목 수집                                                 │
│       │  - 클래스: Test* 로 시작하는 클래스                            │
│       │  - 함수: test_* 로 시작하는 함수/메서드                        │
│       │  - 파라미터화: @pytest.mark.parametrize → 개별 Item 생성      │
│       │  - 결과: [Item, Item, Item, ...] 리스트                       │
│       ▼                                                              │
│  [4] 마커/필터 적용                                                   │
│       - -k "keyword": 이름 기반 필터링                                │
│       - -m "marker": 마커 기반 필터링                                 │
│       - --collect-only: 수집만 하고 실행 안 함                        │
│                                                                      │
│  ══════════════════════════════════════════════════════════════════   │
│  Phase 2: Execution (테스트 실행)                                     │
│  ══════════════════════════════════════════════════════════════════   │
│                                                                      │
│  각 테스트 Item에 대해:                                               │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ [a] Fixture Setup (의존성 해결)                                 │  │
│  │     - 테스트 함수의 파라미터 이름 → fixture 매칭                 │  │
│  │     - fixture 간 의존성 그래프 구축 → 위상 정렬                 │  │
│  │     - scope에 따라 캐싱 (아래 표 참조)                          │  │
│  │                                                                │  │
│  │ [b] Test Execution                                             │  │
│  │     - fixture 값을 인자로 전달하여 테스트 함수 호출              │  │
│  │     - assert 문 실패 시 AssertionError → FAILED                │  │
│  │     - pytest의 assertion rewriting: assert 구문을 AST 수준에서 │  │
│  │       변환하여 상세한 실패 메시지 자동 생성                     │  │
│  │                                                                │  │
│  │ [c] Fixture Teardown                                           │  │
│  │     - yield fixture: yield 이후 코드가 teardown으로 실행        │  │
│  │     - scope 만료 시점에 역순으로 teardown                       │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ══════════════════════════════════════════════════════════════════   │
│  Phase 3: Reporting (결과 보고)                                       │
│  ══════════════════════════════════════════════════════════════════   │
│  - PASSED / FAILED / ERROR / SKIPPED / XFAIL / XPASS 집계            │
│  - --tb=short/long/auto: 트레이스백 출력 레벨                         │
│  - --junitxml: Jenkins 연동용 XML 리포트 생성                         │
│  - exit code: 0 (전체 통과), 1 (실패 있음), 2 (인터럽트),             │
│    3 (내부 오류), 4 (사용법 오류), 5 (테스트 없음)                     │
└──────────────────────────────────────────────────────────────────────┘
```

#### pytest fixture 스코프와 라이프사이클

| 스코프 | 생성 시점 | 소멸 시점 | 용도 예시 |
|--------|----------|----------|----------|
| `function` (기본) | 각 테스트 함수 시작 전 | 해당 함수 종료 후 | DB 트랜잭션 롤백, mock 객체 |
| `class` | 테스트 클래스 첫 번째 테스트 전 | 마지막 테스트 후 | 클래스 공유 상태 |
| `module` | .py 파일의 첫 번째 테스트 전 | 마지막 테스트 후 | DB 연결, 임시 파일 |
| `session` | 전체 pytest 세션 시작 시 | 세션 종료 시 | Docker 컨테이너, 서버 프로세스 |

```python
# fixture 라이프사이클 예시
@pytest.fixture(scope="session")
def db_connection():
    conn = psycopg2.connect(...)   # Session 시작 시 1회 생성
    yield conn                      # 모든 테스트에서 공유
    conn.close()                    # Session 종료 시 정리

@pytest.fixture(scope="function")
def db_transaction(db_connection):
    tx = db_connection.begin()     # 각 테스트 전 트랜잭션 시작
    yield db_connection
    tx.rollback()                  # 각 테스트 후 롤백 (데이터 격리)
```

#### (2) npm test (Vitest) 실행 흐름

```
┌──────────────────────────────────────────────────────────────────┐
│  npm test → vitest run (또는 jest) 실행 흐름                      │
│                                                                  │
│  [1] 설정 로드                                                    │
│       │  - vitest.config.ts / jest.config.js                     │
│       │  - 변환기 설정 (Vite의 esbuild / Babel)                   │
│       ▼                                                          │
│  [2] 테스트 파일 탐색                                             │
│       │  - **/*.test.{js,jsx,ts,tsx}                             │
│       │  - **/*.spec.{js,jsx,ts,tsx}                             │
│       ▼                                                          │
│  [3] 변환 (Transform)                                            │
│       │  - JSX → JavaScript (esbuild/Babel)                      │
│       │  - TypeScript → JavaScript                               │
│       │  - CSS Modules → 객체 mock                               │
│       │  - import → require (CJS 환경) 또는 ESM 네이티브          │
│       ▼                                                          │
│  [4] 테스트 실행                                                  │
│       │  - Vitest: Worker Thread 풀 (기본 CPU 코어 수)            │
│       │  - Jest: Worker Process 풀 (--forked)                    │
│       │  - 각 테스트 파일은 격리된 모듈 환경에서 실행              │
│       │  - describe/it/test 블록 순차 실행                        │
│       │  - beforeAll/afterAll → beforeEach/afterEach 훅          │
│       ▼                                                          │
│  [5] Assertion + Snapshot                                        │
│       │  - expect().toBe/toEqual/toMatchSnapshot 등              │
│       │  - 스냅샷: 첫 실행 시 .snap 파일 생성 → 이후 비교        │
│       ▼                                                          │
│  [6] 커버리지 수집 (--coverage)                                   │
│       - v8 또는 istanbul 기반                                    │
│       - statement / branch / function / line 커버리지             │
└──────────────────────────────────────────────────────────────────┘
```

### 4.3 개선 권장사항

| 우선순위 | 항목 | 설명 |
|---------|------|------|
| P1 | DB Mock 테스트 환경 구축 | pytest-mock 또는 testcontainers로 PostgreSQL 연동 테스트 |
| P2 | 비즈니스 API CRUD 테스트 추가 | items, bom, plans 등 핵심 비즈니스 로직 |
| P3 | 프론트엔드 테스트 추가 | React Testing Library + Vitest |
| P4 | E2E 테스트 | Playwright/Cypress로 로그인 → 메뉴 탐색 → CRUD 시나리오 |

---

## 4-B. 배포 검증 단계의 의미 — 심층 분석

### 4-B-1. Pod 상태값의 의미

`kubectl get pods`가 반환하는 STATUS 필드는 Pod의 라이프사이클 단계를 나타낸다.

```
┌──────────────────────────────────────────────────────────────────────┐
│  Pod 라이프사이클 상태 전이도                                          │
│                                                                      │
│  [Pending] ──→ [ContainerCreating] ──→ [Running] ──→ [Succeeded]    │
│      │               │                    │              (정상 종료)  │
│      │               │                    │                          │
│      │               ▼                    ▼                          │
│      │          [ErrImagePull]      [CrashLoopBackOff]               │
│      │          [ImagePullBackOff]  [Error]                          │
│      │                              [OOMKilled]                      │
│      ▼                                                               │
│  [Unschedulable]                                                     │
│  (노드 리소스 부족)                                                   │
└──────────────────────────────────────────────────────────────────────┘
```

| 상태 | 의미 | 원인/상세 |
|------|------|----------|
| **Pending** | 스케줄링 대기 중 | 노드 선택 중이거나, 리소스(CPU/메모리) 부족으로 배치 불가. PVC 바인딩 대기 중일 수도 있음 |
| **ContainerCreating** | 컨테이너 생성 중 | 이미지 pull, volume 마운트, init container 실행 중. ConfigMap/Secret 마운트도 이 단계에서 수행 |
| **Running** | 실행 중 | 최소 1개 컨테이너가 실행 중. Ready 여부는 별도 (READY 열 확인 필요) |
| **Completed/Succeeded** | 정상 종료 | 모든 컨테이너가 exit code 0으로 종료 (Job/CronJob에서 일반적) |
| **CrashLoopBackOff** | 반복 충돌 | 컨테이너가 시작 후 즉시 종료를 반복. 재시작 간격이 지수적으로 증가 (10s, 20s, 40s, ..., 최대 5분) |
| **Error** | 에러 종료 | 컨테이너가 비정상 exit code로 종료 |
| **OOMKilled** | 메모리 초과 | 컨테이너가 memory limit을 초과하여 커널 OOM Killer에 의해 강제 종료 |
| **ErrImagePull** | 이미지 풀 실패 | 이미지 이름 오타, 레지스트리 인증 실패, 이미지 미존재 |
| **ImagePullBackOff** | 이미지 풀 재시도 대기 | ErrImagePull 반복 후 백오프 상태 |

### 4-B-2. readinessProbe / livenessProbe의 역할

```
┌──────────────────────────────────────────────────────────────────────┐
│  Probe 작동 원리와 배포 성공 판단                                      │
│                                                                      │
│  ┌─────────────────────────────────────────────┐                    │
│  │           livenessProbe                      │                    │
│  │  "컨테이너가 살아있는가?"                      │                    │
│  │                                              │                    │
│  │  - 실패 시: kubelet이 컨테이너를 kill → 재시작 │                    │
│  │  - 용도: 데드락, 무한루프 감지                 │                    │
│  │  - 예시:                                     │                    │
│  │    livenessProbe:                            │                    │
│  │      httpGet:                                │                    │
│  │        path: /api/health                     │                    │
│  │        port: 8000                            │                    │
│  │      initialDelaySeconds: 15                 │                    │
│  │      periodSeconds: 10                       │                    │
│  │      failureThreshold: 3  ← 3번 연속 실패 시  │                    │
│  │                             컨테이너 재시작    │                    │
│  └─────────────────────────────────────────────┘                    │
│                                                                      │
│  ┌─────────────────────────────────────────────┐                    │
│  │           readinessProbe                     │                    │
│  │  "트래픽을 받을 준비가 되었는가?"               │                    │
│  │                                              │                    │
│  │  - 실패 시: Service 엔드포인트에서 제거         │                    │
│  │    (Pod는 죽이지 않음, 트래픽만 차단)           │                    │
│  │  - 롤링 업데이트에서 핵심 역할:                │                    │
│  │    새 Pod의 readinessProbe 통과 전까지         │                    │
│  │    이전 Pod를 유지 → 무중단 배포 보장           │                    │
│  │  - 예시:                                     │                    │
│  │    readinessProbe:                           │                    │
│  │      httpGet:                                │                    │
│  │        path: /api/health                     │                    │
│  │        port: 8000                            │                    │
│  │      initialDelaySeconds: 5                  │                    │
│  │      periodSeconds: 5                        │                    │
│  │      successThreshold: 1  ← 1번 성공 시       │                    │
│  │                             Ready로 전환      │                    │
│  └─────────────────────────────────────────────┘                    │
│                                                                      │
│  ┌─────────────────────────────────────────────┐                    │
│  │           startupProbe (K8s 1.20+)           │                    │
│  │  "초기 기동이 완료되었는가?"                    │                    │
│  │                                              │                    │
│  │  - startupProbe 통과 전까지 liveness/readiness │                   │
│  │    비활성화 → 느린 시작 애플리케이션 보호        │                    │
│  │  - 실패 시: 컨테이너 kill + 재시작             │                    │
│  └─────────────────────────────────────────────┘                    │
│                                                                      │
│  Probe 방식 3가지:                                                    │
│  ┌──────────────┬──────────────┬──────────────┐                     │
│  │   httpGet    │   tcpSocket  │    exec      │                     │
│  │ HTTP 200~399 │ TCP 연결 성공 │ 명령 exit 0  │                     │
│  │ 가장 일반적   │ DB 포트 확인  │ 파일 존재 확인│                     │
│  └──────────────┴──────────────┴──────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 4-B-3. `kubectl rollout status`가 내부적으로 모니터링하는 것

```
┌──────────────────────────────────────────────────────────────────────┐
│  kubectl rollout status deployment/mes-api --timeout=120s            │
│                                                                      │
│  내부 동작:                                                           │
│  [1] API Server에 Deployment watch 요청                              │
│      GET /apis/apps/v1/namespaces/default/deployments/mes-api?watch=1│
│                                                                      │
│  [2] 매 이벤트마다 다음 조건 확인:                                     │
│      ┌─────────────────────────────────────────────────────────┐     │
│      │ a. deployment.status.observedGeneration                 │     │
│      │    == deployment.metadata.generation                    │     │
│      │    → Controller가 최신 spec을 인식했는지 확인             │     │
│      │                                                         │     │
│      │ b. deployment.status.updatedReplicas                    │     │
│      │    == deployment.spec.replicas                          │     │
│      │    → 모든 replica가 새 template으로 업데이트되었는지      │     │
│      │                                                         │     │
│      │ c. deployment.status.availableReplicas                  │     │
│      │    == deployment.spec.replicas                          │     │
│      │    → 모든 replica가 Available(Ready + minReadySeconds)  │     │
│      │                                                         │     │
│      │ d. deployment.status.conditions에서                      │     │
│      │    type=Progressing, status=True,                       │     │
│      │    reason=NewReplicaSetAvailable 확인                    │     │
│      └─────────────────────────────────────────────────────────┘     │
│                                                                      │
│  [3] 모든 조건 충족 시:                                               │
│      "deployment "mes-api" successfully rolled out" 출력 + exit 0    │
│                                                                      │
│  [4] 타임아웃 초과 시:                                                │
│      "error: timed out waiting for the condition" + exit 1           │
│      → 파이프라인 실패 처리                                           │
│                                                                      │
│  [5] Progressing 조건이 False + reason=ProgressDeadlineExceeded:      │
│      → .spec.progressDeadlineSeconds (기본 600초) 초과 시             │
│      → 즉시 실패 반환                                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4-C. CI/CD 보안 고려사항 — 심층 분석

### 4-C-1. Jenkins Credential 관리 메커니즘

```
┌──────────────────────────────────────────────────────────────────────┐
│  Jenkins Credential 저장/주입 흐름                                    │
│                                                                      │
│  [저장 계층]                                                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Jenkins Credential Store                                       │  │
│  │                                                                │  │
│  │  저장 위치: $JENKINS_HOME/credentials.xml                      │  │
│  │  암호화: AES-128-ECB (Jenkins master key로 암호화)              │  │
│  │  마스터 키: $JENKINS_HOME/secrets/master.key                    │  │
│  │  → 이 파일이 유출되면 모든 credential 복호화 가능 (보안 핵심)    │  │
│  │                                                                │  │
│  │  Credential 종류:                                               │  │
│  │  ┌─────────────────────┬───────────────────────────────────┐   │  │
│  │  │ 종류                │ 용도                               │   │  │
│  │  ├─────────────────────┼───────────────────────────────────┤   │  │
│  │  │ Username/Password   │ Git 인증, DB 접속                  │   │  │
│  │  │ Secret Text         │ API 토큰, 단일 비밀 값             │   │  │
│  │  │ Secret File         │ kubeconfig, 인증서 파일            │   │  │
│  │  │ SSH Key             │ Git SSH, 서버 접속                 │   │  │
│  │  │ Certificate (PKCS12)│ 클라이언트 인증서                  │   │  │
│  │  └─────────────────────┴───────────────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│  [주입 메커니즘]              ▼                                       │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Jenkinsfile에서 사용:                                          │  │
│  │                                                                │  │
│  │ environment {                                                  │  │
│  │     DB_PASSWORD = credentials('postgres-password')             │  │
│  │     // → 환경 변수로 주입 (빌드 로그에서 자동 마스킹 ****)       │  │
│  │     KUBECONFIG = credentials('k8s-kubeconfig')                 │  │
│  │     // Secret File → 임시 파일 생성, 경로를 환경변수에 설정      │  │
│  │ }                                                              │  │
│  │                                                                │  │
│  │ withCredentials([usernamePassword(                              │  │
│  │     credentialsId: 'git-cred',                                 │  │
│  │     usernameVariable: 'GIT_USER',                              │  │
│  │     passwordVariable: 'GIT_PASS')]) {                          │  │
│  │     // 이 블록 내에서만 변수 유효 (스코프 제한)                  │  │
│  │     sh 'git push https://$GIT_USER:$GIT_PASS@repo.git'        │  │
│  │ }                                                              │  │
│  │                                                                │  │
│  │ 보안 주의사항:                                                  │  │
│  │ - sh "echo $DB_PASSWORD" → 로그에 **** 로 마스킹               │  │
│  │ - sh "env | sort" → 마스킹 우회 가능! (출력 전체에는 미적용)     │  │
│  │ - writeFile로 credential 값을 파일에 쓰면 아티팩트 유출 위험     │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 4-C-2. kubectl 인증 체계 (kubeconfig → RBAC)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Jenkins에서 K8s 클러스터 접근 인증 흐름                               │
│                                                                      │
│  [1] kubeconfig 구조                                                 │
│      ┌─────────────────────────────────────────────────┐             │
│      │ apiVersion: v1                                  │             │
│      │ clusters:                                       │             │
│      │ - cluster:                                      │             │
│      │     server: https://10.0.0.1:6443               │             │
│      │     certificate-authority-data: <base64 CA cert>│             │
│      │ users:                                          │             │
│      │ - user:                                         │             │
│      │     token: <ServiceAccount 토큰>                │             │
│      │     # 또는 client-certificate + client-key      │             │
│      │ contexts:                                       │             │
│      │ - context:                                      │             │
│      │     cluster: knu-mes-cluster                    │             │
│      │     user: jenkins-deployer                      │             │
│      │     namespace: default                          │             │
│      └─────────────────────────────────────────────────┘             │
│                              │                                       │
│                              ▼                                       │
│  [2] API Server 인증 (Authentication)                                │
│      ┌─────────────────────────────────────────────────┐             │
│      │ API Server는 다음 순서로 인증 시도:              │             │
│      │                                                 │             │
│      │ a. Client Certificate (X.509)                   │             │
│      │    - CN = 사용자명, O = 그룹                     │             │
│      │                                                 │             │
│      │ b. Bearer Token                                 │             │
│      │    - ServiceAccount 토큰 (JWT, /var/run/secrets) │             │
│      │    - OIDC 토큰 (Keycloak 등 IdP 연동 시)        │             │
│      │                                                 │             │
│      │ c. Bootstrap Token (클러스터 초기 설정용)         │             │
│      │                                                 │             │
│      │ → 인증 실패 시 401 Unauthorized                  │             │
│      └─────────────────────────────────────────────────┘             │
│                              │                                       │
│                              ▼                                       │
│  [3] RBAC 인가 (Authorization)                                       │
│      ┌─────────────────────────────────────────────────┐             │
│      │ Role/ClusterRole:                               │             │
│      │   어떤 리소스에 어떤 동작을 허용하는지 정의        │             │
│      │                                                 │             │
│      │ # Jenkins 배포용 Role 예시:                      │             │
│      │ kind: Role                                      │             │
│      │ rules:                                          │             │
│      │ - apiGroups: [""]                               │             │
│      │   resources: ["configmaps", "pods", "services"] │             │
│      │   verbs: ["get","list","create","update","delete"]│            │
│      │ - apiGroups: ["apps"]                           │             │
│      │   resources: ["deployments"]                    │             │
│      │   verbs: ["get","list","update","patch"]        │             │
│      │                                                 │             │
│      │ RoleBinding:                                    │             │
│      │   Role과 User/ServiceAccount를 연결              │             │
│      │                                                 │             │
│      │ kind: RoleBinding                               │             │
│      │ subjects:                                       │             │
│      │ - kind: ServiceAccount                          │             │
│      │   name: jenkins-deployer                        │             │
│      │ roleRef:                                        │             │
│      │   kind: Role                                    │             │
│      │   name: mes-deployer-role                       │             │
│      │                                                 │             │
│      │ → 인가 실패 시 403 Forbidden                     │             │
│      └─────────────────────────────────────────────────┘             │
│                                                                      │
│  최소 권한 원칙 (Least Privilege):                                    │
│  - Jenkins SA에 cluster-admin 부여 금지                              │
│  - 필요한 namespace의 필요한 리소스만 허용                             │
│  - configmaps, deployments, pods에 한정                              │
│  - delete 권한은 가능하면 제외                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### 4-C-3. Secret vs ConfigMap 보안 차이

```
┌──────────────────────────────────────────────────────────────────────┐
│  ConfigMap vs Secret 비교                                            │
│                                                                      │
│  ┌─────────────────────┬────────────────────┬───────────────────┐   │
│  │ 항목                │ ConfigMap          │ Secret            │   │
│  ├─────────────────────┼────────────────────┼───────────────────┤   │
│  │ etcd 저장           │ 평문               │ base64 인코딩     │   │
│  │                     │                    │ (암호화 아님!)     │   │
│  │ etcd 암호화         │ 선택적             │ 선택적             │   │
│  │ (EncryptionConfig)  │ (보통 미적용)       │ (권장: 적용)      │   │
│  │ RBAC 분리           │ configmaps 리소스   │ secrets 리소스    │   │
│  │                     │                    │ (별도 권한 관리)   │   │
│  │ tmpfs 마운트        │ 아니오 (디스크)     │ 예 (메모리)       │   │
│  │                     │                    │ → 디스크 잔류 없음 │   │
│  │ kubectl get 시      │ data 필드 노출     │ data 필드 노출    │   │
│  │                     │                    │ (base64이지만     │   │
│  │                     │                    │  쉽게 디코딩 가능) │   │
│  │ 크기 제한           │ 1MB                │ 1MB               │   │
│  │ 용도                │ 설정, 코드         │ 비밀번호, 토큰,    │   │
│  │                     │                    │ 인증서, API 키    │   │
│  └─────────────────────┴────────────────────┴───────────────────┘   │
│                                                                      │
│  본 프로젝트의 보안 구성:                                             │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ConfigMap으로 관리하는 것 (비밀 아닌 데이터):                    │  │
│  │  - api-code: app.py 소스코드                                   │  │
│  │  - frontend-build: 프론트엔드 빌드 결과물                       │  │
│  │  - nginx-config: nginx 설정                                    │  │
│  │                                                                │  │
│  │ Secret으로 관리해야 하는 것 (비밀 데이터):                       │  │
│  │  - postgres-secret: DB 비밀번호 (POSTGRES_PASSWORD)             │  │
│  │  - jwt-secret: JWT 서명 키 (SECRET_KEY)                        │  │
│  │  - keycloak-secret: Keycloak admin 비밀번호                    │  │
│  │                                                                │  │
│  │ 추가 보안 강화 방안:                                            │  │
│  │  1. etcd 암호화 활성화 (EncryptionConfiguration)                │  │
│  │  2. Sealed Secrets 또는 External Secrets Operator 사용          │  │
│  │     → Secret을 Git에 암호화된 형태로 저장 가능                  │  │
│  │  3. RBAC에서 secrets 리소스 접근을 배포 SA에만 한정              │  │
│  │  4. Pod SecurityContext에서 readOnlyRootFilesystem 활성화       │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

> **주의**: Secret의 base64 인코딩은 보안 메커니즘이 **아니다**. `echo "cGFzc3dvcmQ=" | base64 -d` 만으로 복호화된다. 진정한 보안은 etcd 레벨 암호화(aescbc/aesgcm/secretbox)와 RBAC 접근 제어를 통해 달성된다.

---

## 5. CI/CD 아키텍처 다이어그램

```
┌──────────────────────────────────────────────────────────────┐
│                    Jenkins Pipeline                          │
│                                                              │
│  [1] Clean ──→ [2] Lint ──→ [3] Test ──→ [4] Build FE      │
│                  │ black       │ pytest     │ npm run build  │
│                  │ flake8      │ npm test   │                │
│                  │ isort       │            │                │
│                  │ eslint      │            │                │
│                                                              │
│  [5] Deploy DB ──→ [6] Deploy Keycloak                      │
│       │ PV/PVC        │ keycloak.yaml                       │
│       │ Secret        │ setup-keycloak.sh                   │
│       │ postgres.yaml │                                     │
│                                                              │
│  [7] Deploy Backend ──→ [8] Deploy Frontend                 │
│       │ ConfigMap          │ ConfigMap                       │
│       │   api-code         │   frontend-build               │
│       │ mes-api.yaml       │ nginx-config.yaml              │
│       │ CORS 치환          │ mes-frontend.yaml              │
│                                                              │
│  [9] Verify                                                  │
│       │ kubectl get pods                                     │
│       │ HTTP 200 확인 (API, Frontend)                       │
│       │ Keycloak Realm 확인                                 │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. 결론

| 항목 | 개선 전 | 개선 후 |
|------|---------|---------|
| Jenkinsfile 일치도 | **20%** (Docker 방식 ↔ ConfigMap 방식 불일치) | **95%** (init.sh와 동일한 배포 흐름) |
| Keycloak 배포 | 없음 | 포함 |
| 에러 마스킹 | `\|\| true` 남용 | 제거 (실패 시 파이프라인 중단) |
| 환경 설정 | 하드코딩 | `env.sh` source |
| 레거시 파일 | `k8s/` 디렉터리 잔존 | 삭제 완료 |
| 테스트 커버리지 | 25개 (인프라/AI 전용) | 동일 (비즈니스 API 테스트 추가 권장) |

---

**최종 업데이트**: 2026-03-12 (심층 기술 보강)
