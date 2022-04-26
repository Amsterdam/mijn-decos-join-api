#!groovy

def retagAndPush(String imageName, String currentTag, String newTag)
{
    def regex = ~"^https?://"
    def dockerReg = DOCKER_REGISTRY_HOST - regex
    sh "docker tag ${dockerReg}/${imageName}:${currentTag} ${dockerReg}/${imageName}:${newTag}"
    sh "docker push ${dockerReg}/${imageName}:${newTag}"
}

String BRANCH = "${env.BRANCH_NAME}"
String IMAGE_NAME = "mijnams/mijn-decos-join"
String IMAGE_TAG = "${IMAGE_NAME}:${env.BUILD_NUMBER}"
String CMDB_ID = "app_mijn-decos-join"

node {
    stage("Checkout") {
        checkout scm
    }

    stage("Build image") {
        docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
            def image = docker.build(IMAGE_TAG)
            image.push()
        }
    }
}

// Skipping tests for the test branch
if (BRANCH != "test-acc") {
    node {
        stage("Test") {
            docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
                docker.image(IMAGE_TAG).pull()
                sh "docker run --rm ${IMAGE_TAG} /api/test.sh"
            }
        }
    }
}

if (BRANCH == "test-acc" || BRANCH == "main") {
    node {
        stage("Push acceptance image") {
            docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
                docker.image(IMAGE_TAG).pull()
                retagAndPush(IMAGE_NAME, env.BUILD_NUMBER, "acceptance")
            }
        }
    }

    node {
        stage("Deploy to ACC") {
            build job: "Subtask_Openstack_Playbook",
                parameters: [
                    [$class: "StringParameterValue", name: "INVENTORY", value: "acceptance"],
                    [$class: "StringParameterValue", name: "PLAYBOOK", value: "deploy.yml"],
                    [$class: "StringParameterValue", name: "PLAYBOOKPARAMS", value: "-e cmdb_id=${CMDB_ID}"]
                ]
        }
    }
}

if (BRANCH == "production-release") {
    stage("Waiting for approval") {
        input "Deploy to Production?"
    }

    node {
        stage("Push production image") {
            docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
                docker.image(IMAGE_TAG).pull()
                retagAndPush(IMAGE_NAME, env.BUILD_NUMBER, "production")
            }
        }
    }

    node {
        stage("Deploy") {
            build job: "Subtask_Openstack_Playbook",
                parameters: [
                    [$class: "StringParameterValue", name: "INVENTORY", value: "production"],
                    [$class: "StringParameterValue", name: "PLAYBOOK", value: "deploy.yml"],
                    [$class: "StringParameterValue", name: "PLAYBOOKPARAMS", value: "-e cmdb_id=${CMDB_ID}"]
                ]
        }
    }
}
