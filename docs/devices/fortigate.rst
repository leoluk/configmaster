FortiGate firewalls
===================

.. highlight:: sh

**In production for 3+ years.**

Works with the following FortiOS versions:

* FortiOS 4
* FortiOS 5

Supported features:

* Config backup
* System clock check
* Admin password change
* Checksum comparison
* Firmware version detection

FortiGate does not have a running/startup config distinction.

Remote control class:
:class:`utils.remote.fortigate.FortigateRemoteControl`


.. todo:: Add FortiGate docs


Device setup
++++++++++++

::

    config system global
        set admin-scp enable
    exit

