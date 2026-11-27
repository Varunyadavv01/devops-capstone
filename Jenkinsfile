pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        skipDefaultCheckout()
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    environment {
        IMAGE = 'axdy02/taskops'
        TOOLS = '/var/lib/jenkins/security-tools/bin'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }
            }
        }

        stage('Automated Tests') {
            steps {
                sh 'bash scripts/test.sh'
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    $TOOLS/bandit -r app/ wsgi.py gunicorn.conf.py -ll -ii
                    $TOOLS/pip-audit -r requirements.txt
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                    docker build \
                      --build-arg APP_VERSION=0.1.0 \
                      --build-arg GIT_COMMIT_SHA=$(git rev-parse HEAD) \
                      --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
                      -t $IMAGE:$IMAGE_TAG .
                '''
            }
        }

        stage('Container Scan') {
            steps {
                sh '''
                    docker run --rm \
                      -v /var/run/docker.sock:/var/run/docker.sock \
                      -v taskops-trivy-cache:/root/.cache/trivy \
                      aquasec/trivy:0.76.2 image \
                      --scanners vuln \
                      --severity HIGH,CRITICAL \
                      --exit-code 0 \
                      --format table \
                      $IMAGE:$IMAGE_TAG > trivy-report.txt

                    cat trivy-report.txt
                '''
            }
        }

        stage('Docker Hub Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-credentials',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_TOKEN'
                )]) {
                    sh '''
                        set +x
                        export DOCKER_CONFIG=$(mktemp -d)
                        trap 'rm -rf "$DOCKER_CONFIG"' EXIT

                        printf '%s' "$DOCKER_TOKEN" | \
                          docker login -u "$DOCKER_USER" --password-stdin

                        docker push $IMAGE:$IMAGE_TAG

                        docker tag $IMAGE:$IMAGE_TAG $IMAGE:latest
                        docker push $IMAGE:latest

                        docker logout
                    '''
                }
            }
        }

        stage('Update GitOps') {
            when {
                expression {
                    !sh(
                        script: 'git log -1 --format=%s | grep -q "^GitOps:"',
                        returnStatus: true
                    ).equals(0)
                }
            }
            steps {
                withCredentials([gitUsernamePassword(
                    credentialsId: 'github-credentials',
                    gitToolName: 'Default'
                )]) {
                    sh '''
                        git config user.name "TaskOps Jenkins"
                        git config user.email "jenkins@taskops.local"

                        sed -i "s|image: axdy02/taskops:.*|image: $IMAGE:$IMAGE_TAG|" kubernetes/deployment.yaml

                        git add kubernetes/deployment.yaml

                        if ! git diff --cached --quiet; then
                            git commit -m "GitOps: Deploy TaskOps $IMAGE_TAG"
                            git push origin HEAD:main
                        fi
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'trivy-report.txt',
                             allowEmptyArchive: true
        }
        success {
            echo 'TaskOps CI pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check console output.'
        }
    }
}
