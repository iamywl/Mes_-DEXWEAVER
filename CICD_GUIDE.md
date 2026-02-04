# CI/CD 파이프라인 및 테스트 가이드

이 문서는 프로젝트에 구축된 CI/CD (Continuous Integration/Continuous Deployment) 파이프라인과 통합된 테스트 전략에 대해 설명합니다.

## 1. 변경된 내용 요약

주요 변경 사항은 다음과 같습니다:

-   **자동화된 테스트 통합**: 애플리케이션의 프런트엔드와 백엔드 모두에 대한 단위 테스트가 CI/CD 파이프라인에 추가되었습니다.
-   **Jenkinsfile 업데이트**: Jenkins 파이프라인이 이제 Docker 이미지 빌드, 테스트 실행, Docker 이미지 푸시 및 Kubernetes 배포 단계를 포함합니다.

이러한 변경 사항은 코드 변경 사항이 프로덕션 환경에 배포되기 전에 자동으로 검증되도록 하여, 애플리케이션의 안정성과 품질을 향상시키는 데 기여합니다.

## 2. CI/CD 파이프라인 동작 방식

`Jenkinsfile`은 다음과 같은 단계를 수행하도록 업데이트되었습니다:

1.  **Clean Workspace**: 이전 빌드 아티팩트를 정리합니다.
2.  **Build Backend Docker Image**: 백엔드 (`backend.Dockerfile`) Docker 이미지를 빌드합니다.
3.  **Build Frontend Docker Image**: 프런트엔드 (`frontend/frontend.Dockerfile`) Docker 이미지를 빌드합니다.
4.  **Run Tests**:
    *   **프런트엔드 테스트**: `frontend/` 디렉토리에서 `npm install` 후 `npm test` (Jest)를 실행합니다.
    *   **백엔드 테스트**: 프로젝트 루트 디렉토리에서 `pip install -r requirements.txt` 후 `pytest`를 실행합니다.
5.  **Push Docker Images**: 빌드된 Docker 이미지를 설정된 Docker 레지스트리 (`DOCKER_REGISTRY`)에 푸시합니다.
6.  **Deploy to Kubernetes**:
    *   `k8s/postgres.yaml`을 먼저 적용합니다.
    *   `k8s/backend-deployment.yaml`과 `k8s/frontend-deployment.yaml`을 업데이트하고 `kubectl set image` 명령을 사용하여 새로운 Docker 이미지 태그로 배포를 업데이트합니다.
    *   `k8s/backend-service.yaml` 및 `k8s/frontend-service.yaml`을 적용하여 서비스가 정상적으로 작동하도록 합니다.
    *   배포가 완료될 때까지 기다립니다.

## 3. `http://192.168.64.5:30173/` 에서의 변화

이 주소는 현재 배포된 애플리케이션에 접근하는 URL입니다. 제가 만든 CI/CD 파이프라인 변경 사항은 **애플리케이션 자체의 기능이나 UI를 직접적으로 변경하지 않습니다.**

대신, 새로운 코드 변경 사항이 이 주소로 **배포되기 전에** 코드의 품질과 안정성을 보장하기 위한 프로세스를 구축한 것입니다. 즉, 파이프라인이 성공적으로 실행되면, `http://192.168.64.5:30173/` 에 배포되는 애플리케이션은 테스트를 통과한, 더 신뢰할 수 있는 버전이 될 것입니다.

## 4. 테스트 및 검증 방법

이러한 CI/CD 및 테스트 변경 사항을 검증하려면 Jenkins와 같은 CI/CD 도구를 사용해야 합니다.

1.  **Jenkins 빌드 트리거**:
    *   Jenkins 서버에서 이 프로젝트의 파이프라인 빌드를 수동으로 트리거하거나, 코드 저장소에 변경 사항을 푸시하여 자동 빌드를 트리거합니다.
2.  **Jenkins 빌드 로그 확인**:
    *   Jenkins 대시보드에서 해당 빌드의 로그를 확인합니다.
    *   **`Run Tests` 스테이지**를 찾아 프런트엔드(`npm test` 출력) 및 백엔드(`pytest` 출력) 테스트 결과가 성공했는지 확인합니다.
    *   모든 스테이지가 성공적으로 완료되어야 Docker 이미지가 푸시되고 Kubernetes에 배포됩니다.
3.  **Kubernetes 배포 확인**:
    *   Jenkins 파이프라인이 성공적으로 완료된 후, `kubectl get pods -n default` 또는 `kubectl get deployments -n default` 명령을 사용하여 Kubernetes 클러스터에서 새로운 파드가 배포되었는지, 또는 기존 배포의 이미지가 업데이트되었는지 확인할 수 있습니다.

### 추가된 테스트 파일:

-   **프런트엔드**: `frontend/src/App.test.jsx`
    *   `App.jsx` 컴포넌트가 올바르게 렌더링되는지 확인하는 간단한 예제 테스트입니다.
-   **백엔드**: `test_app.py`
    *   `/api/data` 엔드포인트가 예상대로 작동하고, 데이터베이스 연결 오류를 적절히 처리하는지 확인하는 테스트입니다. 데이터베이스 연결은 테스트를 위해 Mocking 됩니다.

이러한 테스트는 Jenkins 파이프라인의 `Run Tests` 스테이지에서 자동으로 실행됩니다. 파이프라인이 성공적으로 실행되고 배포되면, `http://192.168.64.5:30173/`의 애플리케이션은 테스트를 통과한 코드로 업데이트된 상태가 됩니다.
