pipeline {
    agent any

    environment {
        PROJECT_DIR = "${WORKSPACE}"
    }

    stages {
        stage('Clean Workspace') {
            steps {
                sh 'rm -rf frontend/node_modules frontend/dist'
            }
        }

        stage('Lint & Format Check') {
            steps {
                script {
                    sh '''
                      pip install --user black flake8 isort 2>/dev/null
                      echo "=== Python Black ==="
                      python3 -m black --check app.py api_modules/ || echo "[WARN] black formatting issues found"
                      echo "=== Python Flake8 ==="
                      python3 -m flake8 app.py api_modules/ --max-line-length=99 || echo "[WARN] flake8 issues found"
                      echo "=== Python isort ==="
                      python3 -m isort --check-only app.py api_modules/ || echo "[WARN] isort issues found"
                    '''

                    dir('frontend') {
                        sh '''
                          npm install --silent
                          npx eslint src --ext .js,.jsx || echo "[WARN] eslint issues found"
                        '''
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh 'pip install -r requirements.txt'
                    sh 'pytest test_app.py -v'

                    dir('frontend') {
                        sh 'npm test -- --passWithNoTests'
                    }
                }
            }
        }

        stage('Build Frontend') {
            steps {
                dir('frontend') {
                    sh 'npm run build'
                }
            }
        }

        stage('Load Environment') {
            steps {
                script {
                    REAL_IP = sh(script: "hostname -I | awk '{print \$1}'", returnStdout: true).trim()
                    echo "Detected IP: ${REAL_IP}"
                }
            }
        }

        stage('Deploy Database') {
            steps {
                sh 'kubectl apply -f infra/postgres-pv.yaml'
                sh 'kubectl apply -f infra/db-secret.yaml'
                sh 'kubectl apply -f infra/postgres.yaml'
                sh 'kubectl wait --for=condition=ready pod -l app=postgres --timeout=90s'
            }
        }

        stage('Deploy Keycloak') {
            steps {
                sh 'kubectl apply -f infra/keycloak.yaml'
                echo 'Keycloak deployment requested (takes 30-60s to start)'
            }
        }

        stage('Deploy Backend') {
            steps {
                script {
                    def corsOrigins = "http://${REAL_IP}:30173,http://localhost:30173,http://localhost:3000"

                    sh 'kubectl delete configmap api-code --ignore-not-found'
                    sh 'kubectl create configmap api-code --from-file=app.py=./app.py --from-file=./api_modules/'

                    sh "sed 's|__CORS_ORIGINS__|${corsOrigins}|' infra/mes-api.yaml | kubectl apply -f -"
                    sh 'kubectl rollout restart deployment/mes-api'
                }
            }
        }

        stage('Deploy Frontend') {
            steps {
                sh 'kubectl delete configmap frontend-build --ignore-not-found'
                sh 'kubectl create configmap frontend-build --from-file=frontend/dist/'
                sh 'kubectl apply -f infra/nginx-config.yaml'
                sh 'kubectl apply -f infra/mes-frontend.yaml'
                sh 'kubectl rollout restart deployment/mes-frontend'
            }
        }

        stage('Verify & Configure') {
            steps {
                script {
                    sh 'kubectl rollout status deployment/mes-api --timeout=180s'
                    sh 'kubectl rollout status deployment/mes-frontend --timeout=90s'

                    sh 'kubectl get pods -o wide'
                    sh 'kubectl get svc'

                    // Keycloak Realm 자동 설정
                    sh '''
                      echo "Waiting for Keycloak to be ready..."
                      for i in $(seq 1 120); do
                        if curl -s -o /dev/null -w '' --max-time 2 http://localhost:30080/realms/master 2>/dev/null; then
                          echo "Keycloak is ready (${i}s)"
                          bash setup-keycloak.sh 2>/dev/null
                          break
                        fi
                        sleep 1
                      done
                    '''

                    echo "Backend API: http://${REAL_IP}:30461/docs"
                    echo "Frontend:    http://${REAL_IP}:30173"
                    echo "Keycloak:    http://${REAL_IP}:30080"
                }
            }
        }
    }

    post {
        success {
            echo 'KNU MES deployment completed successfully!'
        }
        failure {
            echo 'KNU MES deployment failed. Check stage logs for details.'
        }
    }
}
