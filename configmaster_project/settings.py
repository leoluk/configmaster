"""
Django settings for configmaster_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
import ldap
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Directories

TEMPLATE_DIRS = (os.path.join(BASE_DIR, "templates"))

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

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
    'south',
    'icons_famfamfam',
    #'debug_toolbar',
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
AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=Users,dc=continum,dc=net",
                                   ldap.SCOPE_SUBTREE, "(uid=%(user)s)")

AUTH_LDAP_ALWAYS_UPDATE_USER = True
AUTH_LDAP_START_TLS = False

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    'ou=Roles,dc=continum,dc=net',
    ldap.SCOPE_SUBTREE)

AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

LOGIN_ALLOWED_GROUPS = ("ldapGroup", )

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS

TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug'
)


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

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

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

from local_settings import *
