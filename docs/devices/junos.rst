Juniper Junos
=============

**Currently being tested.**

Supported features:

* Config backup
* System clock check

Tested with:

* Junos 16.1R6.7

Junos is built on FreeBSD and runs a modified OpenSSH daemon. It's a "full"
operating system, so there are no surprises as far as SSH is concerned.

We recommend to set up a read only account with a SSH key:

    system {
        login {
            class read-only-config {
                permissions [ secret view view-configuration ];
            }
            user configmaster {
                uid 1001;
                class read-only-config;
                authentication {
                    ssh-rsa "ssh-rsa [...]";
                }
            }
        }
    }

Remote control class:
:class:`utils.remote.junos.JunosRemoteControl`

