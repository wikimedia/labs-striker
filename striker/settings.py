# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Wikimedia Foundation and contributors.
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

import ldap
import logging
import os
import sys

import django_auth_ldap.config

import environ


STRIKER_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(STRIKER_DIR)

env = environ.Env()
env.smart_cast = False

# Hack so that we can guard things that will probably fail miserably in test
# like contacting an external server
TEST_MODE = 'test' in sys.argv

# == Logging ==
logging.captureWarnings(True)
LOGGING_HANDLERS = env.list("LOGGING_HANDLERS", default=["console"])
LOGGING_LEVEL = env.str("LOGGING_LEVEL", default="WARNING")
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
        'cee': {
            '()': 'striker.logging.CeeFormatter',
            'message_type': 'striker',
            'fqdn': False,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_id'],
            'formatter': 'line',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': env.str("LOGGING_FILE_FILENAME", default="/dev/null"),
            'filters': ['request_id'],
            'formatter': 'line',
            'level': 'DEBUG',
         },
        'logstash': {
            'class': 'logstash.TCPLogstashHandler',
            'host': env.str("LOGSTASH_HOST", default="127.0.0.1"),
            'port': env.int("LOGSTASH_PORT", default=11514),
            'version': 1,
            'message_type': 'striker',
            'fqdn': False,
            'filters': ['request_id'],
            'level': 'DEBUG',
        },
        'cee': {
            'class': 'logging.StreamHandler',
            'formatter': 'cee',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'django': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'django.request': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'django.security': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'django_auth_ldap': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'ldapdb': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'py.warnings': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
        'ratelimitbackend': {
            'handlers': LOGGING_HANDLERS,
            'level': LOGGING_LEVEL,
            'propagate': False,
        },
    },
    'root': {
        'handlers': LOGGING_HANDLERS,
        'level': LOGGING_LEVEL,
    },
}

# == Django settings ==
SECRET_KEY = env.str("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])
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

MIDDLEWARE = (
    'log_request_id.middleware.RequestIDMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'striker.middleware.XForwaredForMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'striker.labsauth.middleware.OathMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'striker.middleware.ReferrerPolicyMiddleware',
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
        'ENGINE': env.str("DB_ENGINE", default="django.db.backends.sqlite3"),
        'NAME': env.str("DB_NAME", default=":memory:"),
        'USER': env.str("DB_USER", default=""),
        'PASSWORD': env.str("DB_PASSWORD", default=""),
        'HOST': env.str("DB_HOST", default=""),
        'PORT': env.int("DB_PORT", default=0),
    },
    'ldap': {
        'ENGINE': 'ldapdb.backends.ldap',
        'NAME': env.str("LDAP_SERVER_URI", default="ldap://127.0.0.1:389"),
        'USER': env.str("LDAP_BIND_USER", default=""),
        'PASSWORD': env.str("LDAP_BIND_PASSWORD", default=""),
    },
}
DATABASE_ROUTERS = [
    'striker.labsauth.router.CustomLdapRouter',
]
if DATABASES['default']['ENGINE'] in \
        ['django.db.backends.mysql', 'striker.db']:
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
        'BACKEND': env.str(
            "CACHE_BACKEND",
            default="django.core.cache.backends.memcached.MemcachedCache",
        ),
        'LOCATION': env.str("CACHE_LOCATION", default="127.0.0.1:11211"),
        'KEY_PREFIX': 'striker',
        'VERSION': 1,
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOGOUT_REDIRECT_URL = 'index'

STATIC_URL = '/static/'
STATIC_ROOT = env.str(
    "STATIC_ROOT", default=os.path.join(BASE_DIR, "staticfiles")
)
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
# Tests should use django.contrib.staticfiles.storage.StaticFilesStorage.
STATICFILES_STORAGE = env.str(
    "STATICFILES_STORAGE",
    default="whitenoise.storage.CompressedManifestStaticFilesStorage",
)
WHITENOISE_INDEX_FILE = True

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env.bool("REQUIRE_HTTPS", default=False)
SECURE_SSL_HOST = env.str(
    "SSL_CANONICAL_HOST", default="toolsadmin.wikimedia.org"
)

# Should we be using X-Forwared-For headers?
STRIKER_USE_XFF_HEADER = env.bool("USE_XFF_HEADER", default=False)
IPWARE_TRUSTED_PROXY_LIST = env.list("TRUSTED_PROXY_LIST", default=[])

# === Sessions ===
# Cache session data in memcached but keep db persistance as backup
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
# Default session cookie TTL is until browser close. The "remember me" option
# at login will change this.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = env.bool("REQUIRE_HTTPS", default=False)
REMEMBER_ME_TTL = env.int("REMEMBER_ME_TTL", default=1209600)  # 14 days

# === CSRF ===
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = env.bool("REQUIRE_HTTPS", default=False)

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
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_FRAME_SRC = ["'none'"]
CSP_FORM_ACTION = ["'self'"]
CSP_SANDBOX = [
    'allow-forms',
    'allow-same-origin',
    'allow-scripts',
    'allow-top-navigation',
]
CSP_REPORT_URI = '/csp-report'
CSP_WORKER_SRC = ["'none'"]

# == Referrer-Policy settings ==
REFERRER_POLICY = 'strict-origin-when-cross-origin'

# == Bootstrap3 settings ==
BOOTSTRAP3 = {
    'jquery_url': STATIC_URL + 'js/jquery.min.js',
    'base_url': STATIC_URL,
    'javascript_url': STATIC_URL + 'js/bootstrap.min.js',
    'include_jquery': True,
}

# == Authentication settings ==
# LDAP Authentication
AUTH_LDAP_SERVER_URI = env.str(
    "LDAP_SERVER_URI", default="ldap://127.0.0.1:389"
)
AUTH_LDAP_START_TLS = env.bool("LDAP_TLS", default=False)
AUTH_LDAP_USER_SEARCH = django_auth_ldap.config.LDAPSearch(
    env.str("LDAP_USER_SEARCH_BASE", default="ou=people,dc=wikimedia,dc=org"),
    ldap.SCOPE_ONELEVEL,
    env.str("LDAP_USER_SEARCH_FILTER", default="(cn=%(user)s)"),
)
AUTH_LDAP_USER_QUERY_FIELD = 'ldapname'
AUTH_LDAP_USER_ATTR_MAP = {
    'ldapname': 'cn',
    'ldapemail': 'mail',
    'shellname': 'uid',
}
AUTH_LDAP_GROUP_SEARCH = django_auth_ldap.config.LDAPSearch(
    env.str("LDAP_BASE_DN", default="dc=wikimedia,dc=org"),
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfNames)'
)
AUTH_LDAP_GROUP_TYPE = django_auth_ldap.config.GroupOfNamesType()
AUTH_LDAP_MIRROR_GROUPS = True
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    'is_staff': env.str(
        "STAFF_GROUP_DN",
        default="cn=tools.admin,ou=servicegroups,dc=wikimedia,dc=org",
    ),
    'is_superuser': env.str(
        "SUPERUSER_GROUP_DN",
        default="cn=tools.admin,ou=servicegroups,dc=wikimedia,dc=org",
    ),
}


AUTHENTICATION_BACKENDS = (
    'striker.labsauth.backends.RateLimitedLDAPBackend',
)

# Install our custom User model
AUTH_USER_MODEL = 'labsauth.LabsUser'

LOGIN_URL = 'labsauth:login'
LOGIN_REDIRECT_URL = '/'

LABSAUTH_USER_BASE = env.str(
    "LDAP_USER_SEARCH_BASE", default="ou=people,dc=wikimedia,dc=org"
)
LABSAUTH_GROUP_BASE = env.str("LDAP_BASE_DN", default="dc=wikimedia,dc=org")

LABSAUTH_DEFAULT_GID = env.int("DEFAULT_GID", default=500)
LABSAUTH_DEFAULT_SHELL = env.str("DEFAULT_SHELL", default="/bin/bash")
LABSAUTH_MIN_GID = env.int("MIN_GID", default=50000)
LABSAUTH_MAX_GID = env.int("MAX_GID", default=59999)
LABSAUTH_MIN_UID = env.int("MIN_UID", default=500)
LABSAUTH_MAX_UID = env.int("MAX_UID", default=49999)

# == OAuth settings ==
OAUTH_CONSUMER_KEY = env.str("OAUTH_CONSUMER_KEY")
OAUTH_CONSUMER_SECRET = env.str("OAUTH_CONSUMER_SECRET")
OAUTH_MWURL = env.str(
    "OAUTH_MWURL", default="https://meta.wikimedia.org/w/index.php"
)

# == Phabricator settings ==
PHABRICATOR_URL = env.str(
    "PHABRICATOR_URL", default="https://phabricator.wikimedia.org"
)
PHABRICATOR_USER = env.str("PHABRICATOR_USER", default="StrikerBot")
PHABRICATOR_TOKEN = env.str("PHABRICATOR_TOKEN")
# phid of group granted Diffusion admin rights (i.e. #Repository-Admins)
PHABRICATOR_REPO_ADMIN_GROUP = env.str(
    "PHABRICATOR_REPO_ADMIN_GROUP", default="PHID-PROJ-uew7bzww4e66466eglzw"
)
# phid of project that tool projects should be made under (i.e. #tools)
PHABRICATOR_PARENT_PROJECT = env.str(
    "PHABRICATOR_PARENT_PROJECT", default="PHID-PROJ-zywtwi3xlva5ohkdndwb"
)

# == Wikitech settings ==
WIKITECH_URL = env.str(
    "WIKITECH_URL", default="https://wikitech.wikimedia.org"
)
WIKITECH_USER = env.str("WIKITECH_USER", default="StrikerBot")
WIKITECH_CONSUMER_TOKEN = env.str("WIKITECH_CONSUMER_TOKEN")
WIKITECH_CONSUMER_SECRET = env.str("WIKITECH_CONSUMER_SECRET")
WIKITECH_ACCESS_TOKEN = env.str("WIKITECH_ACCESS_TOKEN")
WIKITECH_ACCESS_SECRET = env.str("WIKITECH_ACCESS_SECRET")

# == Tools settings ==
TOOLS_MAINTAINER_BASE_DN = env.str(
    "TOOLS_MAINTAINER_BASE_DN", default="ou=people,dc=wikimedia,dc=org"
)
TOOLS_TOOL_BASE_DN = env.str(
    "TOOLS_TOOL_BASE_DN", default="ou=servicegroups,dc=wikimedia,dc=org"
)
TOOLS_TOOL_LABS_GROUP_NAME = env.str(
    "TOOLS_TOOL_LABS_GROUP_NAME", default="project-tools"
)

# == Project settings ==
PROJECTS_BASE_DN = 'ou=projects,{}'.format(
    env.str("LDAP_BASE_DN", default="dc=wikimedia,dc=org")
)

# == OATH settings ==
OATHMIDDLEWARE_REDIRECT = 'labsauth:oath'

# == OpenStack settings ==
OPENSTACK_URL = env.str(
    "OPENSTACK_URL",
    default="https://openstack.eqiad1.wikimediacloud.org:25000/v3"
)
OPENSTACK_USER = env.str("OPENSTACK_USER", default="novaadmin")
OPENSTACK_PASSWORD = env.str("OPENSTACK_PASSWORD")
OPENSTACK_PROJECT = env.str("OPENSTACK_PROJECT", default="tools")
OPENSTACK_USER_ROLE = env.str("OPENSTACK_USER_ROLE", default="user")
OPENSTACK_ADMIN_ROLE = env.str("OPENSTACK_ADMIN_ROLE", default="projectadmin")

# == GitLab settings ==
GITLAB_URL = env.str("GITLAB_URL", default="https://gitlab.wikimedia.org")
GITLAB_ACCESS_TOKEN = env.str("GITLAB_ACCESS_TOKEN")
GITLAB_REPO_NAMESPACE_NAME = env.str(
    "GITLAB_REPO_NAMESPACE_NAME",
    default="toolforge-repos",
)
GITLAB_REPO_NAMESPACE_ID = env.int("GITLAB_REPO_NAMESPACE_ID", default=688)
GITLAB_PROVIDER = env.str("GITLAB_PROVIDER", default="cas3")
GITLAB_EXTERN_FORMAT = env.str("GITLAB_EXTERN_FORMAT", default="{}")

# == Notifications ==
NOTIFICATIONS_SOFT_DELETE = True
NOTIFICATIONS_USE_JSONFIELD = True

# == Feature flags ==
FEATURE_ACCOUNT_CREATE = env.bool("FEATURE_ACCOUNT_CREATE", default=True)
