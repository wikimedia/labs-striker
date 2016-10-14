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

import logging

from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from striker import mediawiki
from striker.labsauth.models import LabsUser
from striker.tools.models import Maintainer


logger = logging.getLogger(__name__)
mwapi = mediawiki.Client.default_client()


def sul_available(name):
    try:
        LabsUser.objects.get(sulname=name)
    except LabsUser.DoesNotExist:
        return True
    else:
        return False


def username_available(name):
    try:
        Maintainer.objects.get(full_name=name)
    except Maintainer.DoesNotExist:
        return True
    else:
        return False


def shellname_available(name):
    try:
        Maintainer.objects.get(username=name)
    except Maintainer.DoesNotExist:
        return True
    else:
        return False


def check_username_create(name):
    """Check to see if a given name would be allowed as a username.

    Returns True if the username would be allowed. Returns either False or a
    reason specifier if the username is not allowed.
    Returns a dict with these keys:
    - ok : Can a new user be created with this name (True/False)
    - name : Canonicalized version of the given name
    - error : Error message if ok is False; None otherwise
    """
    user = mwapi.query_users_cancreate(name)[0]
    # Example response:
    # [{'missing': True, 'name': 'Puppet',
    # 'cancreate': False, 'cancreateerror': [{'message':
    # 'titleblacklist-forbidden-new-account', 'params': ['
    # ^(User:)?puppet$ <newaccountonly>', 'Puppet'], 'type': 'error'}]}]
    ret = {
        'ok': False,
        'name': user['name'],
        'error': None,
    }
    if user['missing'] and user['cancreate']:
        ret['ok'] = True
    elif 'userid' in user:
        ret['error'] = _('%(name)s is already in use.') % ret
    elif 'cancreateerror' in user:
        try:
            ret['error'] = mwapi.get_message(
                    user['cancreateerror'][0]['message'],
                    *user['cancreateerror'][0]['params'],
                    lang=translation.get_language().split('-')[0])
        except Exception:
            logger.exception('Failed to get expanded message for %s', user)
            ret['error'] = user['cancreateerror'][0]['message']
    return ret


def check_ip_blocked_from_create(ip):
    """Check to see if an ip address is banned from creating accounts.

    Returns a block reason or False if not blocked.
    """
    res = mwapi.query_blocks_ip(ip)
    for block in res:
        if block['nocreate']:
            return block['reason']
    return False
