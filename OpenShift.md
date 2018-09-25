# OpenShift Dev

Red Hat's OpenShift[1] is supported for development. Tested with OpenShift 3.7.

OpenShift is not yet supported for production.

This guide assumes a cluster with persistent storage.
Make sure that the `oc` client is set up for the right project.

Create application:

    oc process -f openshift/configmaster.yaml | oc create -f -

Tear down:

    oc delete all,secret,pvc -l app=configmaster

Live sync (transfer modified files to the pod):

    openshift/sync.sh

Remote shell in the active pod:

    openshift/rsh.sh

Rebuild:

    oc start-build configmaster -F

[1]: https://github.com/openshift/origin
