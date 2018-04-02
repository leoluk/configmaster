pipeline {
  agent any
  stages {
    stage('Setup') {
      steps {
        timeout(unit: 'MINUTES', time: 10) {
          sh '''oc process -f openshift/configmaster.yaml "GIT_REF=${BRANCH_NAME}" "NAME=configmaster-branch-${BRANCH_NAME}" -l "app=branch-${BRANCH_NAME}" | oc create -f -
oc rollout status dc/configmaster-branch-jenkins'''
        }
        
      }
    }
    stage('Run tests') {
      steps {
        catchError() {
          sh 'oc rsh "dc/configmaster-branch-${BRANCH_NAME}" scl enable python27 -- ./manage.py run junos-dev-vmx-16'
        }
        
      }
    }
    stage('Teardown') {
      steps {
        sh 'oc delete all,secret,pvc -l "app=branch-${BRANCH_NAME}"'
      }
    }
  }
}