HP ProCurve
===========

**In production for 3+ years.**

.. warning::
    ProCurve devices are known to have a memory leak which results in a reboot
    after 100000+ logins. While daily runs are unproblematic, hourly runs
    are not recommended.

    See :ref:`this warning <crash-warning>` in the installation guide for
    more information on crash risks.

Supported features:

* Config backup
* Comparison of running and startup config
* System clock check
* Firmware version detection

Remote control class:
:class:`utils.remote.procurve.ProCurveRemoteControl`


.. todo:: Add ProCurve docs