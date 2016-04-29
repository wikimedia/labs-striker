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

import django_auth_ldap.config
import ldap
import logging
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '3sjg74^=vk&**k1%1-kmmhb_^#-$zx_l2arwia^u0-jac@)^35'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'striker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'striker.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'

# LDAP Authentication
AUTH_LDAP_SERVER_URI = 'ldap://127.0.0.1:3389'
AUTH_LDAP_START_TLS = True
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
}
AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = True
AUTH_LDAP_USER_ATTR_MAP = {
    'email': 'mail',
}
AUTH_LDAP_USER_SEARCH = django_auth_ldap.config.LDAPSearch(
    'ou=people,dc=wikimedia,dc=org',
    ldap.SCOPE_SUBTREE,
    '(cn=%(user)s)'
)
AUTH_LDAP_GROUP_SEARCH = django_auth_ldap.config.LDAPSearch(
    'dc=wikimedia,dc=org',
    ldap.SCOPE_SUBTREE,
    '(objectClass=groupOfNames)'
)
AUTH_LDAP_GROUP_TYPE = django_auth_ldap.config.GroupOfNamesType()
AUTH_LDAP_MIRROR_GROUPS = True
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    'is_active': 'cn=project-tools,ou=groups,dc=wikimedia,dc=org',
    'is_staff': 'cn=wmf,ou=groups,dc=wikimedia,dc=org',
    'is_superuser': 'cn=tools.admin,ou=servicegroups,dc=wikimedia,dc=org',
}

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# FIXME: proper logging config needed
logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
