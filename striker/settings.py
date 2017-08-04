# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Wikimedia Foundation and contributors.
# All Rights Reserved.
#
# This file is part of Striker.
#
# Striker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Striker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Striker.  If not, see <http://www.gnu.org/licenses/>.

import configparser
import ldap
import os
import sys

import django_auth_ldap.config


STRIKER_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(STRIKER_DIR)

# Read configuration settings from ini files
# Based on example given at:
# https://code.djangoproject.com/wiki/SplitSettings#ini-stylefilefordeployment
ini = configparser.RawConfigParser(allow_no_value=True)
ini.read([
    os.path.join(STRIKER_DIR, 'striker.ini'),
    os.path.join(BASE_DIR, 'striker.ini'),
    '/etc/striker/striker.ini',
])

# Hack so that we can guard things that will probably fail miserably in test
# like contacting an external server
TEST_MODE = 'test' in sys.argv

# == Logging ==
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'incremental': False,
    'filters': {
        'request_id': {
            '()': 'log_request_id.filters.RequestIDFilter'
        }
    },
    'formatters': {
        'line': {
            'format':
                '%(asctime)s [%(request_id)s] %(name)s %(levelname)s: '
                '%(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%SZ',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'line',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': ini.get('logging', 'FILE_FILENAME'),
            'filters': ['request_id'],
            'formatter': 'line',
            'level': 'DEBUG',
         },
        'logstash': {
            'class': 'logstash.TCPLogstashHandler',
            'host': ini.get('logging', 'LOGSTASH_HOST'),
            'port': int(ini.get('logging', 'LOGSTASH_PORT')),
            'version': 1,
            'message_type': 'striker',
            'fqdn': False,
            'filters': ['request_id'],
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
        'django.security': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
        'django_auth_ldap': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
        'ldapdb': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
        'ratelimitbackend': {
            'handlers': ini.get('logging', 'HANDLERS').split(),
            'level': ini.get('logging', 'LEVEL'),
            'propagate': False,
        },
    },
    'root': {
        'handlers': ini.get('logging', 'HANDLERS').split(),
        'level': ini.get('logging', 'LEVEL'),
    },
}

# == Django settings ==
SECRET_KEY = ini.get('secrets', 'SECRET_KEY')
DEBUG = ini.getboolean('debug', 'DEBUG')
ALLOWED_HOSTS = ini.get('hosts', 'ALLOWED_HOSTS').split()

INSTALLED_APPS = (
    'bootstrap3',
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'formtools',
    'notifications',
    'reversion',
    'reversion_compare',
    'striker',
    'striker.goals.apps.GoalsConfig',
    'striker.labsauth',
    'striker.profile',
    'striker.register',
    'striker.tools',
)

MIDDLEWARE_CLASSES = (
    'log_request_id.middleware.RequestIDMiddleware',
    'striker.middleware.XForwaredForMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'striker.labsauth.middleware.OathMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'ratelimitbackend.middleware.RateLimitMiddleware',
)

ROOT_URLCONF = 'striker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(STRIKER_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'striker.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': ini.get('db', 'ENGINE'),
        'NAME': ini.get('db', 'NAME'),
        'USER': ini.get('db', 'USER'),
        'PASSWORD': ini.get('db', 'PASSWORD'),
        'HOST': ini.get('db', 'HOST'),
        'PORT': ini.get('db', 'PORT'),
    },
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': ini.get('ldap', 'SERVER_URI'),
        'USER': ini.get('ldap', 'BIND_USER'),
        'PASSWORD': ini.get('ldap', 'BIND_PASSWORD'),
    },
}
DATABASE_ROUTERS = [
    'striker.labsauth.router.CustomLdapRouter',
]
if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    # Make Django and MySQL play nice
    # https://blog.ionelmc.ro/2014/12/28/terrible-choices-mysql/
    # NOTE: use of utf8mb4 charset assumes innodb_large_prefix on the hosting
    # MySQL server. If not enabled, you will receive errors mentioning
    # "Specified key was too long; max key length is 767 bytes" for UNIQUE
    # indices on varchar(255) fields.
    DATABASES['default']['OPTIONS'] = {
        'sql_mode': 'TRADITIONAL',
        'charset': 'utf8mb4',
        'init_command':
            'SET character_set_connection=utf8mb4,'
            'collation_connection=utf8mb4_unicode_ci;'
            'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED',
    }

CACHES = {
    'default': {
        'BACKEND': ini.get('cache', 'BACKEND'),
        'LOCATION': ini.get('cache', 'LOCATION'),
        'KEY_PREFIX': 'striker',
        'VERSION': 1,
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = ini.get('static', 'STATIC_ROOT')
if STATIC_ROOT == 'default':
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
STATICFILES_STORAGE = \
    'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = ini.getboolean('https', 'REQUIRE_HTTPS')
SECURE_SSL_HOST = ini.get('https', 'SSL_CANONICAL_HOST')

# Should we be using X-Forwared-For headers?
STRIKER_USE_XFF_HEADER = ini.get('xff', 'USE_XFF_HEADER')
IPWARE_TRUSTED_PROXY_LIST = ini.get('xff', 'TRUSTED_PROXY_LIST').split()

# === Sessions ===
# Cache session data in memcached but keep db persistance as backup
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
# Default session cookie TTL is until browser close. The "remember me" option
# at login will change this.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = ini.getboolean('https', 'REQUIRE_HTTPS')
REMEMBER_ME_TTL = int(ini.get('user_session', 'REMEMBER_ME_TTL'))

# === CSRF ===
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = ini.getboolean('https', 'REQUIRE_HTTPS')

# === django.middleware.security.SecurityMiddleware flags ===
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# == Content-Security-Policy ==
# https://django-csp.readthedocs.io/en/latest/configuration.html
CSP_DEFAULT_SRC = ["'none'"]  # Use a whitelist only approach
CSP_SCRIPT_SRC = ["'self'"]
CSP_IMG_SRC = ["'self'"]
CSP_OBJECT_SRC = ["'none'"]
CSP_MEDIA_SRC = ["'none'"]
CSP_FONT_SRC = ["'self'"]
CSP_CONNECT_SRC = ["'self'"]
CSP_STYLE_SRC = ["'self'"]
CSP_BASE_URI = ["'none'"]
CSP_CHILD_SRC = ["'none'"]
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_FORM_ACTION = ["'self'"]
CSP_SANDBOX = [
    'allow-forms',
    'allow-same-origin',
    'allow-scripts',
    'allow-top-navigation',
]
CSP_REPORT_URI = '/csp-report'

# == Bootstrap3 settings ==
BOOTSTRAP3 = {
    'jquery_url': STATIC_URL + 'js/jquery.min.js',
    'base_url': STATIC_URL,
    'javascript_url': STATIC_URL + 'js/bootstrap.min.js',
    'include_jquery': True,
}

# == Authentication settings ==
# LDAP Authentication
AUTH_LDAP_SERVER_URI = ini.get('ldap', 'SERVER_URI')
AUTH_LDAP_START_TLS = ini.getboolean('ldap', 'TLS')
AUTH_LDAP_USER_SEARCH = django_auth_ldap.config.LDAPSearch(
    ini.get('ldap', 'USER_SEARCH_BASE'),
    ldap.SCOPE_ONELEVEL,
    ini.get('ldap', 'USER_SEARCH_FILTER')
)
AUTH_LDAP_USER_ATTR_MAP = {
    'ldapname': 'cn',
    'ldapemail': 'mail',
    'shellname': 'uid',
}
AUTH_LDAP_GROUP_SEARCH = django_auth_ldap.config.LDAPSearch(
    ini.get('ldap', 'BASE_DN'),
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfNames)'
)
AUTH_LDAP_GROUP_TYPE = django_auth_ldap.config.GroupOfNamesType()
AUTH_LDAP_MIRROR_GROUPS = True
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    'is_staff': ini.get('ldap', 'STAFF_GROUP_DN'),
    'is_superuser': ini.get('ldap', 'SUPERUSER_GROUP_DN'),
}


AUTHENTICATION_BACKENDS = (
    'striker.labsauth.backends.RateLimitedLDAPBackend',
)

# Install our custom User model
AUTH_USER_MODEL = 'labsauth.LabsUser'

LOGIN_URL = 'labsauth:login'
LOGIN_REDIRECT_URL = '/'

LABSAUTH_USER_BASE = ini.get('ldap', 'USER_SEARCH_BASE')
LABSAUTH_GROUP_BASE = ini.get('ldap', 'BASE_DN')

LABSAUTH_DEFAULT_GID = int(ini.get('ldap', 'DEFAULT_GID'))
LABSAUTH_DEFAULT_SHELL = ini.get('ldap', 'DEFAULT_SHELL')
LABSAUTH_MIN_GID = int(ini.get('ldap', 'MIN_GID'))
LABSAUTH_MAX_GID = int(ini.get('ldap', 'MAX_GID'))
LABSAUTH_MIN_UID = int(ini.get('ldap', 'MIN_UID'))
LABSAUTH_MAX_UID = int(ini.get('ldap', 'MAX_UID'))

# == OAuth settings ==
OAUTH_CONSUMER_KEY = ini.get('oauth', 'CONSUMER_KEY')
OAUTH_CONSUMER_SECRET = ini.get('oauth', 'CONSUMER_SECRET')
OAUTH_MWURL = ini.get('oauth', 'MWURL')

# == Phabricator settings ==
PHABRICATOR_URL = ini.get('phabricator', 'SERVER_URL')
PHABRICATOR_USER = ini.get('phabricator', 'USER')
PHABRICATOR_TOKEN = ini.get('phabricator', 'TOKEN')
# phid of group granted Diffusion admin rights (i.e. #Repository-Admins)
PHABRICATOR_REPO_ADMIN_GROUP = ini.get('phabricator', 'REPO_ADMIN_GROUP')

# == Wikitech settings ==
WIKITECH_URL = ini.get('wikitech', 'SERVER_URL')
WIKITECH_USER = ini.get('wikitech', 'USER')
WIKITECH_CONSUMER_TOKEN = ini.get('wikitech', 'CONSUMER_TOKEN')
WIKITECH_CONSUMER_SECRET = ini.get('wikitech', 'CONSUMER_SECRET')
WIKITECH_ACCESS_TOKEN = ini.get('wikitech', 'ACCESS_TOKEN')
WIKITECH_ACCESS_SECRET = ini.get('wikitech', 'ACCESS_SECRET')

# == Tools settings ==
TOOLS_MAINTAINER_BASE_DN = ini.get('ldap', 'TOOLS_MAINTAINER_BASE_DN')
TOOLS_TOOL_BASE_DN = ini.get('ldap', 'TOOLS_TOOL_BASE_DN')
TOOLS_TOOL_LABS_GROUP_NAME = ini.get('ldap', 'TOOLS_TOOL_LABS_GROUP_NAME')

# == Project settings ==
PROJECTS_BASE_DN = 'ou=projects,{}'.format(ini.get('ldap', 'BASE_DN'))

# == OATH settings ==
OATHMIDDLEWARE_REDIRECT = 'labsauth:oath'

# == OpenStack settings ==
OPENSTACK_URL = ini.get('openstack', 'URL')
OPENSTACK_USER = ini.get('openstack', 'USER')
OPENSTACK_PASSWORD = ini.get('openstack', 'PASSWORD')
OPENSTACK_PROJECT = ini.get('openstack', 'PROJECT')
OPENSTACK_USER_ROLE = ini.get('openstack', 'USER_ROLE')
OPENSTACK_ADMIN_ROLE = ini.get('openstack', 'ADMIN_ROLE')

# == Notifications ==
NOTIFICATIONS_SOFT_DELETE = True
NOTIFICATIONS_USE_JSONFIELD = True
