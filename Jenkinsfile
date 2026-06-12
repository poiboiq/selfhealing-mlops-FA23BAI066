pipeline {
    agent any

    environment {
        DOCKERHUB_USERNAME = 'fa23bai066'
        DOCKERHUB_CREDENTIALS_ID = 'dockerhub-creds'
        IMAGE_NAME = 'sentiment-api'
    }

    stages {
        stage('Fetch') {
            steps {
                checkout scm
            }
        }

        stage('Build and Run') {
            steps {
                sh '''
                    set -eux
                    test -n "${DOCKERHUB_USERNAME}"
                    docker network inspect sentiment-test-net >/dev/null 2>&1 || docker network create sentiment-test-net
                    docker rm -f sentiment-app || true
                    docker build -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:unstable .
                    docker volume create sentiment-logs >/dev/null
                    docker run -d --name sentiment-app --network sentiment-test-net -p 5000:5000 \
                      -v sentiment-logs:/app/logs ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:unstable
                    for i in $(seq 1 60); do
                      if curl -fsS http://localhost:5000/health; then exit 0; fi
                      sleep 5
                    done
                    docker logs sentiment-app
                    exit 1
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    set -eux
                    docker run --rm --network sentiment-test-net \
                      -e BASE_URL=http://sentiment-app:5000 \
                      -v "$PWD/tests:/tests" python:3.11-slim \
                      sh -c "pip install --no-cache-dir pytest requests && pytest -q /tests/test_api.py"
                '''
            }
        }

        stage('UI Test') {
            steps {
                sh '''
                    set -eux
                    docker rm -f selenium-chrome || true
                    docker run -d --name selenium-chrome --network sentiment-test-net --shm-size=2g selenium/standalone-chrome:latest
                    sleep 12
                    docker run --rm --network sentiment-test-net \
                      -e BASE_URL=http://sentiment-app:5000 \
                      -e SELENIUM_REMOTE_URL=http://selenium-chrome:4444/wd/hub \
                      -v "$PWD/tests:/tests" python:3.11-slim \
                      sh -c "pip install --no-cache-dir pytest selenium requests && pytest -q /tests/test_ui.py"
                '''
            }
        }

        stage('Build and Push') {
            steps {
                sh '''
                    set -eux
                    rm -rf stable-worktree
                    git fetch origin stable-fallback:refs/remotes/origin/stable-fallback
                    git worktree add stable-worktree origin/stable-fallback
                    docker build -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:unstable .
                    docker build -t ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:stable stable-worktree
                '''
                withCredentials([usernamePassword(credentialsId: env.DOCKERHUB_CREDENTIALS_ID, usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        set -eux
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                        docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:unstable
                        docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:stable
                        docker logout || true
                    '''
                }
                sh '''
                    git worktree remove -f stable-worktree || true
                '''
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    set -eux
                    sed -i "s|fa23bai066|${DOCKERHUB_USERNAME}|g" k8s/*.yaml
                    kubectl apply -f k8s/pvc.yaml
                    kubectl apply -f k8s/blue-deployment.yaml
                    kubectl apply -f k8s/green-deployment.yaml
                    kubectl apply -f k8s/service.yaml
                    kubectl rollout status deployment/sentiment-blue-deployment --timeout=300s
                    kubectl rollout status deployment/sentiment-green-deployment --timeout=300s
                    kubectl patch service sentiment-api-service -p '{"spec":{"selector":{"app":"sentiment-api","slot":"blue"}}}'
                    pkill -f "kubectl port-forward.*sentiment-api-service.*32500:5000" || true
                    nohup kubectl port-forward --address 0.0.0.0 svc/sentiment-api-service 32500:5000 >/tmp/sentiment-portforward.log 2>&1 &
                    sleep 3
                    curl -fsS http://127.0.0.1:32500/health || true
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f selenium-chrome || true
                docker rm -f sentiment-app || true
                docker network rm sentiment-test-net || true
            '''
        }
    }
}
