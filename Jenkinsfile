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
String IMAGE_TEST = "${IMAGE_NAME}:test-${env.BUILD_NUMBER}"
String CMDB_ID = "app_mijn-decos-join"

node {
    stage("Checkout") {
        checkout scm
    }

    // Skipping tests for the test branch
    if (BRANCH != "test-acc") {
        stage("Test") {
            docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
                sh "docker build -t ${IMAGE_TEST} " +
                    "--target=tests " +
                    "--shm-size 1G " +
                    "."
                sh "docker run --rm ${IMAGE_TEST}"
            }
        }
    }

    stage("Build image") {
        docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
            def image = docker.build(IMAGE_TAG, "--target=publish .")
            image.push()
        }
    }

    if (BRANCH == "test-acc" || BRANCH == "main") {
        stage("Push acceptance image") {
            docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
                docker.image(IMAGE_TAG).pull()
                retagAndPush(IMAGE_NAME, env.BUILD_NUMBER, "acceptance")
            }
        }

        stage("Deploy to ACC") {
            build job: "Subtask_Openstack_Playbook",
                parameters: [
                    [$class: "StringParameterValue", name: "INVENTORY", value: "acceptance"],
                    [$class: "StringParameterValue", name: "PLAYBOOK", value: "deploy.yml"],
                    [$class: "StringParameterValue", name: "PLAYBOOKPARAMS", value: "-e cmdb_id=${CMDB_ID}"]
                ]
        }
    }

    if (BRANCH == "production-release") {
        stage("Waiting for approval") {
            input "Deploy to Production?"
        }

        stage("Push production image") {
            docker.withRegistry(DOCKER_REGISTRY_HOST, "docker_registry_auth") {
                docker.image(IMAGE_TAG).pull()
                retagAndPush(IMAGE_NAME, env.BUILD_NUMBER, "production")
            }
        }

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
