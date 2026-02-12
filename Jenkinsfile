pipeline {
    agent any

    environment {
        // Replace with your Docker Hub username or private registry
        DOCKER_REGISTRY = "your-docker-repo"
        // Replace with your Kubernetes context if needed, or ensure kubectl is configured
        KUBECONFIG_CONTEXT = ""
    }

    stages {
        stage('Clean Workspace') {
            steps {
                sh 'rm -rf /root/.gemini/tmp/667d357ee42cffd7150c85b61417bee9093e201dfd6f0f7d1b97f10eb3141d4c/frontend/node_modules'
                sh 'rm -rf /root/.gemini/tmp/667d357ee42cffd7150c85b61417bee9093e201dfd6f0f7d1b97f10eb3141d4c/frontend/dist'
            }
        }
        stage('Lint & Format Check') {
            steps {
                script {
                    // Python linting and formatting checks
                    sh '''
                      python3 -m pip install --user black flake8 isort || true
                      ~/.local/bin/black --check . || true
                      ~/.local/bin/flake8 . --max-line-length=99 || true
                    '''

                    // Frontend linting
                    dir('frontend') {
                        sh '''
                          npm install --silent
                          npx eslint --version || true
                          npx eslint src --ext .js,.jsx || true
                        '''
                    }
                }
            }
        }
        stage('Build Backend Docker Image') {
            steps {
                sh "docker build -t ${DOCKER_REGISTRY}/mes-backend:${BUILD_NUMBER} -f backend.Dockerfile ."
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
        stage('Push Docker Images') {
            steps {
                // Ensure Docker credentials are set up in Jenkins
                // For example, using `withRegistry` step for Docker Hub
                // withRegistry('https://registry.hub.docker.com', 'docker-credentials-id') {
                sh "docker push ${DOCKER_REGISTRY}/mes-backend:${BUILD_NUMBER}"
                sh "docker push ${DOCKER_REGISTRY}/mes-backend:latest"
                sh "docker push ${DOCKER_REGISTRY}/mes-frontend:${BUILD_NUMBER}"
                sh "docker push ${DOCKER_REGISTRY}/mes-frontend:latest"
                // }
            }
        }
        stage('Run Tests') {
            steps {
                script {
                    // Run Frontend Tests
                    dir('frontend') {
                        sh 'npm install'
                        sh 'npm test'
                    }
                    // Run Backend Tests
                    sh 'pip install -r requirements.txt'
                    sh 'pytest'
                }
            }
        }
        stage('Deploy to Kubernetes') {
            steps {
                // Apply postgres first
                sh "kubectl apply -f k8s/postgres.yaml"

                // Update image for backend deployment
                sh "kubectl set image deployment/backend-deployment backend=${DOCKER_REGISTRY}/mes-backend:${BUILD_NUMBER} -n default"
                // Apply backend service and deployment (if not using `set image`)
                sh "kubectl apply -f k8s/backend-service.yaml"
                sh "kubectl apply -f k8s/backend-deployment.yaml"

                // Update image for frontend deployment
                sh "kubectl set image deployment/frontend-deployment frontend=${DOCKER_REGISTRY}/mes-frontend:${BUILD_NUMBER} -n default"
                // Apply frontend service and deployment (if not using `set image`)
                sh "kubectl apply -f k8s/frontend-service.yaml"
                sh "kubectl apply -f k8s/frontend-deployment.yaml"

                // Wait for deployments to be ready (optional, but recommended)
                sh "kubectl rollout status deployment/backend-deployment -n default --timeout=300s"
                sh "kubectl rollout status deployment/frontend-deployment -n default --timeout=300s"
            }
        }
    }
}
