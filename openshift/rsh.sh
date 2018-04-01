#!/bin/bash

oc project
oc rsh dc/configmaster "$@"
