#!groovy

def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block()
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: '#ci-channel', color: 'danger'

        throw t
    }
    finally {
        if (tearDown) {
            tearDown()
        }
    }
}


node {
    stage("Checkout") {
        checkout scm
    }

    stage('Test') {
        tryStep "test", {
            docker.withRegistry("${DOCKER_REGISTRY}",'docker-registry') {
                docker.build("mijnams/decosjoin:${env.BUILD_NUMBER}")
                sh "docker run --rm mijnams/decosjoin:${env.BUILD_NUMBER} /app/test.sh"
            }
        }
    }


    stage("Build image") {
        tryStep "build", {
            docker.withRegistry("${DOCKER_REGISTRY}",'docker-registry') {
                def image = docker.build("mijnams/decosjoin:${env.BUILD_NUMBER}")
                image.push()
            }
        }
    }
}

String BRANCH = "${env.BRANCH_NAME}"

if (BRANCH == "master") {

    node {
        stage('Push acceptance image') {
            tryStep "image tagging", {
                docker.withRegistry("${DOCKER_REGISTRY}",'docker-registry') {
                    def image = docker.image("mijnams/decosjoin:${env.BUILD_NUMBER}")
                    image.pull()
                    image.push("acceptance")
                }
            }
        }
    }

    node {
        stage("Deploy to ACC") {
            tryStep "deployment", {
                build job: 'Subtask_Openstack_Playbook',
                    parameters: [
                        [$class: 'StringParameterValue', name: 'INVENTORY', value: 'acceptance'],
                        [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-mijn-decos-join.yml'],
                    ]
            }
        }
    }

    stage('Waiting for approval') {
        slackSend channel: '#ci-channel', color: 'warning', message: 'mijn-decos-join-api is waiting for Production Release - please confirm'
        input "Deploy to Production?"
    }

    node {
        stage('Push production image') {
            tryStep "image tagging", {
               docker.withRegistry("${DOCKER_REGISTRY}",'docker-registry') {
                    def image = docker.image("mijnams/decosjoin:${env.BUILD_NUMBER}")
                    image.pull()
                    image.push("production")
                    image.push("latest")
                }
            }
        }
    }

    node {
        stage("Deploy") {
            tryStep "deployment", {
                build job: 'Subtask_Openstack_Playbook',
                    parameters: [
                        [$class: 'StringParameterValue', name: 'INVENTORY', value: 'production'],
                        [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-mijn-decos-join.yml'],
                    ]
            }
        }
    }
}
