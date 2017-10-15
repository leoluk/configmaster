Configuration
=============

Do not edit the settings in ``configmaster_project/settings.py``.
Instead, create a ``local_settings.py`` file and override the settings there.

This document lists ConfigMaster-specific settings as well as important
Django settings which you'll probably want to set.


Required settings
+++++++++++++++++

.. option:: SECRET_KEY

    Secret key used for things like cookie signing and password reset tokens.
    It is very important that you set it to a random value in production.

    This is a Django setting: :setting:`django:SECRET_KEY`

    Example::

        SECRET_KEY = "!prt)u6r06)wov$+s=z!5xmvl57x9d2e03§"


.. option:: DATABASES

    Database configuration. ConfigMaster works with all database backends that
    Django supports, but all production environments are running MySQL.

    If you do not specify it, it defaults to a local ``db.sqlite3`` SQLite
    database for development (which is unsuitable for production!).

    See Django's :setting:`DATABASES docs <django:DATABASES>` for details.

    MySQL example config::

        DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'OPTIONS': {
                'read_default_file': '/root/my.cnf',
            }
        }

    SQLite database::

        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }

    You can also specify hostname, database and login credentials explicitly.

.. option:: ALLOWED_HOSTS

    Allowed HTTP HOST values.

    This is a Django setting: :setting:`django:ALLOWED_HOSTS`

    Example::

        ALLOWED_HOSTS = (
            'configmaster-dev.local,
        )

Optional settings
+++++++++++++++++

.. option:: CONFIGMASTER_RETRIES

    Number of times a task is retried on failure. More retries make the run
    more robust against adverse network conditions or unpredictably slow
    devices, but significantly increase the run duration by an integer factor.

    Defaults to 1.

.. option:: CONFIGMASTER_SECURE_GROUP

    If a device group name contains this identifier, its verbose output (which
    contains device config excerpts) is hidden from the Nagios status endpoint.

    Example: "(PCI-DSS)".

    Defaults to ``""``.

.. option:: CONFIGMASTER_SECURE_GROUP_PLURAL

    Configurable identifier to strip from device group.

    For example, you might have two device groups with plural values
    "Firewalls" and "PCI-DSS-Firewalls", with the "PCI-DSS" devices backed up
    to a different repository for security reasons. In this case, there's no
    point in .

    Example: "PCI-DSS-".

    Defaults to ``""``.

.. option:: CONFIGMASTER_NTP_MAX_DELTA

    Maximum clock check offset, in minutes (used by
    :class:`configmaster.management.handlers.ntp.NetworkDeviceNTPHandler`).

    Defaults to 5.

.. option:: CMDB_EXPORT_URL

    Example::

        CMDB_EXPORT_URL = "http://cmdb.example.com/configmaster_export"

    Defaults to `False` (CMDB import won't work).

.. option:: CMDB_CREDENTIALS_URL

    URL template for an external credential store. If a template is set, a link
    will be displayed in the dashboard view. ``%s`` is replaced with the device
    identifier.

    Example::

        CMDB_CREDENTIALS_URL = "https://cmdb.example.com/devices/%s"

    Defaults to `False` (no credential button shown).

.. option:: CMDB_REDIRECT

    URL template for an external CMDB that displays details for a particular
    device. The CMDB icon will link to this URL. ``%s`` is replaced with the
    device identifier.

    Example::

        CMDB_REDIRECT = "https://credmgr.example.com/credentials/%s"

    Defaults to `False` (no redirect button shown).

.. option:: CONFIGMASTER_PW_CHANGE_API_KEY

    API token for :class:`configmaster.views.PasswordChangeAPIView`.

    Defaults to `None` (endpoint disabled).

.. option:: TASK_CONFIG_BACKUP_DISABLE_GIT

    If set to `True`, Git commit and push will be disabled (the file is
    only written to the repository without touching Git).

    Useful for debugging or if you use an external tool for versioning.

    Defaults to `False`.

.. option:: TIME_ZONE

    This is a Django setting: :setting:`django:TIME_ZONE`

    Defaults to ``Europe/Berlin``.

.. option:: DEBUG

    Set to `True` for tracebacks, verbose error messages and other debugging
    goodies. Various parts of the stack, including the application
    itself, observe this settings.

    .. warning::
        Enabling DEBUG in production is dangerous and will probably expose
        confidential information (or worse). Don't.

    This is a Django setting: :setting:`django:DEBUG`

.. option:: INTERNAL_IPS

    List of internal IP addresses. Important for debugging. In a production
    environment, it adds some additional markup, but nothing else.

    This is a Django setting: :setting:`django:INTERNAL_IPS`

    Example::

        INTERNAL_IPS = (
            "172.16.4.109",
        )

.. option:: AUTHENTICATION_BACKENDS

    This is a Django setting: :setting:`django:AUTHENTICATION_BACKENDS`

    Default to only :class:`django.contrib.auth.backends.ModelBackend`.

    Example allowing both LDAP and local login::

        AUTHENTICATION_BACKENDS = (
            'django_auth_ldap.backend.LDAPBackend',
            'django.contrib.auth.backends.ModelBackend',
        )

.. option:: LOGIN_ALLOWED_GROUPS

    List of LDAP groups which are allowed to login. Assumes that you have
    set up LDAP authentication and properly configured
    :std:setting:`django_auth_ldap:AUTH_LDAP_GROUP_SEARCH`.

    Defaults to empty, which will allow no user to log in.

    Example::

        LOGIN_ALLOWED_GROUPS = ("Technik",)


LDAP authentication
+++++++++++++++++++

ConfigMaster supports the `django_auth_ldap`_ module for authentication.

Any Django authentication backend will work with ConfigMaster - you do not
have to use LDAP. You can also use local user accounts, but we
strongly recommend you use some sort of single-sign-on mechanism.

User parameters are set in the
:func:`configmaster.models.update_user_from_ldap` function. Every user will
have staff and superuser permissions in Django and can therefore modify the
ConfigMaster settings.

The following LDAP attributes are processed:

**uid**
    Will be used to populate the Django username. Should be some sort of
    unique identifier.

**email**
    The user's email address. Will be used to populate Django's email address.

**displayname** (optional)
    Concatenated name field. It is assumed that the last word is the last name.
    If it's missing, the user won't have a display name and the username will
    be used instead.


Example config::

    AUTH_LDAP_SERVER_URI = 'ldaps://auth.example.com:636'
    AUTH_LDAP_BIND_DN = "cn=ldapread,dc=example,dc=com"
    AUTH_LDAP_BIND_PASSWORD = "your_ldap_read_password"

    AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'ou=Roles,dc=exameple,dc=com',
    ldap.SCOPE_SUBTREE)

    AUTH_LDAP_USER_SEARCH = LDAPSearch(
        "ou=Users,dc=example,dc=com",
        ldap.SCOPE_SUBTREE, "(uid=%(user)s)")



Authenticating against Active Directory or without full read access to the
directory is possible, but more complicated (refer to the `django_auth_ldap`_
documentation).


.. _django_auth_ldap: https://pythonhosted.org/django-auth-ldap/
