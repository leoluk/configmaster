pipeline {
  agent any
  stages {
    stage('Setup') {
      steps {
        timeout(unit: 'MINUTES', time: 10) {
          sh '''oc process -f openshift/configmaster.yaml "GIT_REF=${BRANCH_NAME}" "NAME=configmaster-build-${GIT_COMMIT:0:7}" -l "app=build-${GIT_COMMIT:0:7}" | oc create -f -
oc rollout status dc/configmaster-build-${GIT_COMMIT:0:7}'''
        }
        
      }
    }
    stage('Run tests') {
      steps {
        catchError() {
          sh 'oc rsh "dc/configmaster-build-${GIT_COMMIT:0:7}" scl enable python27 -- ./manage.py run junos-dev-vmx-16'
        }
        
      }
    }
    stage('Teardown') {
      steps {
        sh 'oc delete all,secret,pvc -l "app=build-${GIT_COMMIT:0:7}"'
      }
    }
  }
}
