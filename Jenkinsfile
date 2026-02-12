pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = "your-docker-repo"
        KUBECONFIG_CONTEXT = ""
        REAL_IP = ""
    }

    stages {
        stage('Clean Workspace') {
            steps {
                sh 'rm -rf frontend/node_modules frontend/dist || true'
            }
        }

        stage('Lint & Format Check') {
            steps {
                script {
                    sh '''
                      pip install --user black flake8 isort || true
                      python3 -m black --check app.py api_modules/ || true
                      python3 -m flake8 app.py api_modules/ --max-line-length=99 || true
                      python3 -m isort --check-only app.py api_modules/ || true
                    '''

                    dir('frontend') {
                        sh '''
                          npm install --silent
                          npx eslint src --ext .js,.jsx || true
                        '''
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh 'pip install -r requirements.txt'
                    sh 'pytest test_app.py -v || true'

                    dir('frontend') {
                        sh 'npm install'
                        sh 'npm test -- --passWithNoTests || true'
                    }
                }
            }
        }

        stage('Build Backend Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_REGISTRY}/mes-backend:${BUILD_NUMBER} -f Dockerfile ."
                sh "docker tag ${DOCKER_REGISTRY}/mes-backend:${BUILD_NUMBER} ${DOCKER_REGISTRY}/mes-backend:latest"
            }
        }

        stage('Build Frontend Docker Image') {
            steps {
                dir('frontend') {
                    sh "docker build -t ${DOCKER_REGISTRY}/mes-frontend:${BUILD_NUMBER} -f frontend.Dockerfile ."
                    sh "docker tag ${DOCKER_REGISTRY}/mes-frontend:${BUILD_NUMBER} ${DOCKER_REGISTRY}/mes-frontend:latest"
                }
            }
        }

        stage('Detect Host IP') {
            steps {
                script {
                    REAL_IP = sh(script: "hostname -I | awk '{print \$1}'", returnStdout: true).trim()
                    echo "Detected IP: ${REAL_IP}"
                }
            }
        }

        stage('Deploy Backend to Kubernetes') {
            steps {
                sh 'kubectl delete configmap api-code --ignore-not-found'
                sh 'kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/'
                sh '''
                  cat <<'K8S' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mes-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mes-api
  template:
    metadata:
      labels:
        app: mes-api
    spec:
      containers:
      - name: mes-api
        image: python:3.9-slim
        command: ["/bin/sh", "-c"]
        args:
        - |
          mkdir -p /app/api_modules &&
          cp /mnt/*.py /app/api_modules/ &&
          mv /app/api_modules/app.py /app/app.py &&
          touch /app/api_modules/__init__.py &&
          pip install --no-cache-dir fastapi uvicorn psycopg2-binary kubernetes pydantic psutil &&
          python /app/app.py
        volumeMounts:
        - name: code-volume
          mountPath: /mnt
      volumes:
      - name: code-volume
        configMap:
          name: api-code
K8S
                '''
                sh 'kubectl apply -f k8s/backend-service.yaml || true'
                sh 'kubectl rollout restart deployment/mes-api'
                sh 'kubectl rollout status deployment/mes-api --timeout=300s || true'
            }
        }

        stage('Deploy Frontend to Kubernetes') {
            steps {
                sh "kubectl apply -f k8s/frontend-deployment.yaml || true"
                sh "kubectl apply -f k8s/frontend-service.yaml || true"
                sh 'kubectl rollout status deployment/frontend-deployment --timeout=300s || true'
            }
        }

        stage('Verify Deployment') {
            steps {
                sh 'kubectl get pods -o wide'
                sh 'kubectl get svc'
                echo "Backend: http://${REAL_IP}:30461/docs"
                echo "Frontend: http://${REAL_IP}:30173"
            }
        }
    }

    post {
        success {
            echo 'MES deployment completed successfully!'
        }
        failure {
            echo 'MES deployment failed. Check logs for details.'
        }
    }
}
