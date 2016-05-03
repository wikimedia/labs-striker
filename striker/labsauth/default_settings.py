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
"""Default settings for authentication."""

import django_auth_ldap.config
import ldap
import logging

# Install our custom User model
AUTH_USER_MODEL = 'labsauth.LabsUser'

# LDAP Authentication
AUTH_LDAP_SERVER_URI = 'ldap://127.0.0.1:3389'
AUTH_LDAP_START_TLS = True
AUTH_LDAP_GLOBAL_OPTIONS = {
    ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER,
}
AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = True
AUTH_LDAP_USER_ATTR_MAP = {
    'ldapemail': 'mail',
    'shellname': 'uid',
    'realname': 'sn',
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

LOGIN_URL = 'labsauth:login'

# FIXME: proper logging config needed
logger = logging.getLogger('django_auth_ldap')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
