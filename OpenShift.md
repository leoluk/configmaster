# OpenShift Dev

Red Hat's OpenShift[1] is supported for development. Tested with OpenShift 3.7.

OpenShift is not yet supported for production.

This guide assumes a cluster with persistent storage.
Make sure that the `oc` client is set up for the right project.

The devices to be tested against need to be reachable from the OpenShift node
and the default hostnames specified in the fixtures need to resolve. You can use
openshift/dns-local.sh as template.

Generate SSH key and upload it:

    ssh-keygen -f local/configmaster_dev
    oc secrets new-sshauth configmaster-ssh --ssh-privatekey=local/configmaster_dev

Create application:

    oc process -f openshift/configmaster.yaml | oc create -f -

Tear down:

    oc delete all,secret,pvc -l app=configmaster

Live sync (transfer modified files to the pod):

    openshift/sync.sh

Remote shell in the active pod:

    openshift/rsh.sh

Remote shell in database:

    oc rsh dc/configmaster-db
    $ mysql -u root
    
ConfigMaster run via rsh:

    # load nss_wrapper to make Git work
    . /opt/app-root/etc/generate_container_user
    ./manage.py run junos-dev-vmx-16
    
(https://github.com/sclorg/s2i-base-container/issues/116)
    
Rebuild:

    oc start-build configmaster -F

[1]: https://github.com/openshift/origin
