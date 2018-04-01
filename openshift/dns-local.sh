#!/bin/bash

oc create service externalname junos-dev-vmx-16 --external-name=192.168.122.2
