#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

"""
Django settings for configmaster_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

import os
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Directories

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

# General

# No default value to prevent accidental usage of hardcoded secrets
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

if os.getenv('DJANGO_DEBUG'):
    DEBUG = True
    ALLOWED_HOSTS = ['*']
    INTERNAL_IPS = ['127.0.0.1']

# Application definition

INSTALLED_APPS = (
    'adminactions',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'configmaster',
    'utils.contrib.icons_famfamfam',
    # 'debug_toolbar',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'restrictedsessions.middleware.RestrictedSessionsMiddleware'
)


# LDAP auth

AUTH_LDAP_SERVER_URI = 'ldap://[...]'

AUTH_LDAP_BIND_DN = ""
AUTH_LDAP_BIND_PASSWORD = ""
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=Users,dc=example,dc=com",
    ldap.SCOPE_SUBTREE, "(uid=%(user)s)")

AUTH_LDAP_ALWAYS_UPDATE_USER = True
AUTH_LDAP_START_TLS = False

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'ou=Roles,dc=example,dc=com',
    ldap.SCOPE_SUBTREE)

AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

AUTHENTICATION_BACKENDS = (
#    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_ALLOWED_GROUPS = ("ldapGroup",)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, "templates")
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ROOT_URLCONF = 'configmaster_project.urls'

WSGI_APPLICATION = 'configmaster_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

if os.getenv('DATABASE_SERVICE_NAME'):
    import db_from_env
    DATABASES['default'] = db_from_env.config()

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'frontend_cache'
    }
}

CONFIGMASTER_RETRIES = 1
CONFIGMASTER_SECURE_GROUP = "(secure)"
CONFIGMASTER_SECURE_GROUP_PLURAL = "secure-"

CONFIGMASTER_NTP_MAX_DELTA = 5

CONFIGMASTER_PW_CHANGE_API_KEY = None

# External CMDB settings

CMDB_EXPORT_URL = None
CMDB_CREDENTIALS_URL = None
CMDB_REDIRECT = None

# Session backend

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# ESXi backup (example config)

# ESXI_BACKUP = (
#     ('esx01.example.com',
#       'http://192.168.50.50:8888/configBundle-192.168.50.50.tgz'),
#     ('esx02.example.com',
#       'http://192.168.50.50:8888/configBundle-192.168.50.50.tgz'),
#     ('esx03.example.com',
#       'http://192.168.50.50:8888/configBundle-192.168.50.50.tgz'),
# )

ESXI_FILE_BLACKLIST = (
    'state.tgz',
    'local.tgz',
    'etc/vmware/.backup.counter',
    'etc/ntp.drift',
    'etc/vmware/dvsdata.db',
    'etc/vmware/lunTimestamps.log',
)

try:
    # noinspection PyUnresolvedReferences
    from local_settings import *
except ImportError:
    pass

if DEBUG == False:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
