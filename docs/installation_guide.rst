Installation guide
==================

.. highlight:: sh

.. note::
    We recommend using a configuration management system like Ansible or
    Puppet for production setups. You can use this guide to integrate
    ConfigMaster with your config management setup.

    Official Ansible and Puppet modules are planned.

Dependencies
************

ConfigMaster requires Python 2.7.2.

We recommend either CentOS 7 or Debian 9 for production setups, but you can
probably make it work on any reasonably recent GNU/Linux distribution.

Debian 8 dependencies:

- python-pip
- python-dev
- libmysqlclient-dev
- libldap-dev
- libsasl2-dev

Debian 9 dependencies:

- python-pip
- python-dev
- libmariadbclient-dev
- libldap-dev
- libsasl2-dev

Ubuntu 16.04 dependencies:

- python-pip
- python-dev
- libmysqlclient-dev
- libldap2-dev
- libsasl2-dev

CentOS 7 dependencies:

- epel-release (this one first, then the others)
- python-pip
- openldap-devel
- python-devel

Python 3 future
---------------

Note that we do not guarantee distribution compatibility - while some of the
current dependencies happen to be packaged by most major distributions,
we're moving to Python 3 in the near future.

Depending on the recent-ness of your distro, you'll have to use `pyenv`_ or
something like Red Hat's Software Collections to get a more recent version
of Python than your base distribution provides.

This may sound inconvenient at first, but de-coupling application and
base operating system is fundamentally a good thing. It allows you to use a
stable, long-term-support operating system like Debian or RHEL/CentOS
with a modern stack on top.

Here's a short assessment for some popular distributions so you can already
plan the migration:

*Debian 8*
    Only Python 3.4, which is too old no matter what. Will require `pyenv`_.

*Debian 9*
    Contains Python 3.5. Python 3.6 would need pyenv.

*Ubuntu 14.04 LTS*
    Python 3.4, like Debian 8.

*Ubuntu 16.04 LTS*
    Python 3.5. Inofficial PPA for 3.6 exists.

*RHEL/CentOS 6 and 7*
    Red Hat has published a rh-python35 and rh-python36 `SCL`_.

*Fedora 26 and up*
    Python 3.6.


.. _pyenv: https://github.com/pyenv/pyenv
.. _SCL: https://www.softwarecollections.org/en/scls/rhscl/rh-python35/

Application setup
*****************

ConfigMaster does not require root privileges.

ConfigMaster is designed to run as its own user. This guide assumes a user
and group named ``configmaster`` with a home directory ``/home/configmaster``
have been created::

    useradd -m configmaster -s /bin/bash
    sudo -i -u configmaster

Clone the source code::

    git clone https://github.com/leoluk/configmaster
    cd configmaster/

Since all ConfigMaster modules use the same Python environment, it is not
necessary (but possible, and in some cases useful) to use a virtualenv. This
guide will proceed without a virtualenv.

Install the Python requirements::

    pip2 install --user --no-use-wheel -r requirements.txt

``--user`` installs the packages into the user's local site-packages
directory.

``--no-use-wheel`` prevents the use of pre-compiled binary
packages. For security reasons, we're pinning the package hashes and the
binary hashes differ depending on Python version and architecture. We want
to get and compile the source code instead.

If you're getting compilation errors, this means that
you're missing a compilation dependency. You can either install your
distribution's binary package (if it's not too old) or install the
compilation dependencies.

.. todo::
    Document how to initialize the database (in short: run ``./manage.py
    migrate``) and import a fixture.


Application server
******************

ConfigMaster has been designed and tested with the `gunicorn`_ application
server, but any WSGI-compliant application should work.

We recommend using systemd for service supervision. If you do not have
systemd, supervisord works fine, too, but is more heavy-weight.

.. _python-path:

.. hint::
    The Python interpreter path is important if you're using `pyenv`_ or a
    virtualenv. Instead of sourcing ``activate`` in a shell, you should always
    specify the full interpreter path instead if you're working in a
    non-interactive environment.

    This is how an example invocation would look like with a virtualenv::

        /home/configmaster/python_env/bin/python \
            /home/configmaster/configmaster/manage.py runserver

    Likewise, you can directly run application binaries::

        /home/configmaster/python_env/bin/gunicorn \
            /home/configmaster/configmaster/configmaster_project

.. todo:: Add service supervision examples

.. _gunicorn: http://gunicorn.org/

Cronjobs
********

ConfigMaster requires some daily cleanup tasks:

  * ``./manage.py clearsessions``
  * ``./manage.py clear_old_reports``

In addition to that, you'll need to schedule the runs themselves.

.. todo:: Add cron and systemd timer file examples

Have a look at the
:ref:`documentation for run.py <run-command-docs>` for more details on the
command-line syntax and the internal workings of the task runner.

.. _crash-warning:

.. warning::
    **Be careful.** The embedded code running on many network devices,
    especially older generations, may have memory leaks, counter overflows
    or similar issues that only express themselves when you connect many,
    many times.

    We managed to crash HP ProCurve by doing more than 100000+ SSH logins.
    On the other hand, devices which run a full operating system like
    FortiGate or JunOS have no such issues and can be queried each hour (or
    in even shorter intervals) without experiencing any issues.

    The ProCurve crash would take 12+ years to reproduce with daily runs,
    but would theoretically occur within a few weeks or months when doing
    hourly runs (depending on the number of tasks).

    In general, a daily run is sufficient for most environments and the safest
    option. ConfigMaster has been running in production for 3+ years with
    daily runs on a diverse set of devices, vendors and firmware versions.

    The :doc:`devices/device_library` has more information about the
    production-readiness and long term stability of particular device vendor
    implementations.



Webserver configuration
***********************

.. todo:: Add webserver configuration examples
