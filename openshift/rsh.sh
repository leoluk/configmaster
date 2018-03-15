#!/bin/bash

oc project

DC=configmaster
POD=$(oc get pod -l deploymentconfig=${DC} -o name|cut -f2 -d/)

echo ${POD}
oc rsh ${POD} "$@"
