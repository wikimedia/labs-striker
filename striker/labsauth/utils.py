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

import ldap
import logging
import operator
import time

from django.conf import settings

from striker import mediawiki
from striker.labsauth import constants
from striker.labsauth import models


logger = logging.getLogger(__name__)


def tuple_to_unicode(t):
    """Decode a tuple of bytes to a tuple of utf8 strings."""
    return tuple([i.decode('utf-8') for i in t])


def tuple_to_bytes(t):
    """Encode a tuple of utf8 strings as a tuple of bytes."""
    return tuple([i.encode('utf-8') for i in t])


def oauth_from_session(session):
    """Get OAuth data from a user's session.

    :return: dict of username, email, realname, token, and secret
    """
    token = session.get(constants.ACCESS_TOKEN_KEY, (None, None))
    return {
        'username': session.get(constants.OAUTH_USERNAME_KEY, None),
        'email': session.get(constants.OAUTH_EMAIL_KEY, None),
        'realname': session.get(constants.OAUTH_REALNAME_KEY, None),
        'token': token[0],
        'secret': token[1],
    }


def get_next_id_number(clazz, attr, low_val, high_val):
    """Get the next id number for a given class and attribute.

    :param clazz: Model to query (e.g. striker.labsauth.models.PosixAccount)
    :param attr: Attribute to examine (e.g. 'uid_number')
    """
    entries = clazz.objects.all().values(attr)
    next_id = max(
        max(entries, key=operator.itemgetter(attr))[attr] + 1,
        low_val)
    if next_id > high_val:
        # From OpenStackNovaUser::getNextIdNumber:
        # Upper limit is only a warning, not a fatal error.
        logger.warning(
            'Id range limit exceded for %s. Soft limit %d; next %d',
            attr, high_val, next_id)
    return next_id


def get_next_uid():
    """Get the next available LDAP user uid."""
    return get_next_id_number(
        models.PosixAccount, 'uid_number',
        settings.LABSAUTH_MIN_UID, settings.LABSAUTH_MAX_UID)


def get_next_gid():
    """Get the next available LDAP group gid."""
    return get_next_id_number(
        models.PosixGroup, 'gid_number',
        settings.LABSAUTH_MIN_GID, settings.LABSAUTH_MAX_GID)


def add_ldap_user(username, shellname, passwd, email):
    """Add a new user to LDAP."""
    u = models.LdapUser()
    u.uid = shellname
    u.cn = username
    u.uid_number = get_next_uid()
    u.gid_number = settings.LABSAUTH_DEFAULT_GID
    u.home_dir = '/home/%s' % shellname
    u.login_shell = settings.LABSAUTH_DEFAULT_SHELL
    u.password = passwd
    u.sn = username
    u.mail = email
    try:
        u.save()
    except ldap.CONSTRAINT_VIOLATION:
        # LDAP uid collision. Probably a race, so try again.
        # If it happens a second time just let it rip up the stack.
        u.uid_number = get_next_uid()
        u.save()

    return u


def oath_enabled(user):
    """Is oath enabled for the given user?"""
    mwapi = mediawiki.Client.default_client()
    res = mwapi.query_meta_oath(user.ldapname)
    return res['enabled']


def oath_validate_token(user, totp):
    """Validate a TOTP OATH token."""
    mwapi = mediawiki.Client.default_client()
    res = mwapi.oathvalidate(user.ldapname, totp)
    if not res['enabled']:
        return True
    else:
        return res['valid']


def oath_save_validation(user, request):
    now = time.time()
    request.session[constants.OATH_INFO] = {
        'user': user.ldapname,
        'time': now
    }
