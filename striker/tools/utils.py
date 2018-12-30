# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Wikimedia Foundation and contributors.
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

from django.conf import settings
from django.contrib.auth.models import Group

from striker.labsauth.utils import get_next_gid
from striker.register import utils as reg_utils
from striker.tools.models import SudoRole
from striker.tools.models import Tool
from striker.tools.models import ToolUser


logger = logging.getLogger(__name__)


def toolname_available(name):
    toolname = 'tools.{0!s}'.format(name)
    try:
        Tool.objects.get(cn=toolname)
    except Tool.DoesNotExist:
        return True
    else:
        return False


def check_toolname_create(name):
    """Check to see if a given name would be allowed as a tool name.

    Returns True if the username would be allowed. Returns either False or a
    reason specifier if the username is not allowed.
    Returns a dict with these keys:
    - ok : Can a new user be created with this name (True/False)
    - name : Canonicalized version of the given name
    - error : Error message if ok is False; None otherwise
    """
    return reg_utils.check_username_create(name)


def create_tool(name, user):
    """Create a new tool account."""
    group_name = 'tools.{}'.format(name)
    gid = get_next_gid()

    # Create group
    tool = Tool(cn=group_name, gid_number=gid, members=[user.ldap_dn])
    tool.save()

    # Create user that tool runs as
    service_user = ToolUser(
        uid=group_name,
        sn=group_name,
        cn=group_name,
        uid_number=gid,
        gid_number=gid,
        home_directory='/data/project/{}'.format(name),
        login_shell='/bin/bash',
    )
    service_user.save()

    # Create sudoers rule to allow maintainers to act as tool user
    sudoers = SudoRole(
        cn='runas-{}'.format(group_name),
        users=['%{}'.format(group_name)],
        hosts=['ALL'],
        commands=['ALL'],
        options=['!authenticate'],
        runas_users=[group_name],
    )
    sudoers.save()

    # Mirror the tool as a Django Group so we can send notifications.
    # This is normally done on user login by labsauth.
    try:
        maintainers, created = Group.objects.get_or_create(name=tool.cn)
        user.groups.add(maintainers.id)
    except Exception:
        logger.exception(
            'Failed to add %s to django maintainers group', user)

    return tool


def member_or_admin(tool, user):
    """Is the given user a member of the given tool or a global admin?"""
    if user.is_anonymous:
        return False
    if user.ldap_dn in tool.members:
        return True
    return tools_admin(user)


def tools_admin(user):
    """Is the given user an administrator of the tools project?"""
    if user.is_anonymous:
        return False
    return user.ldap_dn in Tool.objects.get(cn='tools.admin').members


def project_member(user):
    groups = user.groups.values_list('name', flat=True)
    return settings.TOOLS_TOOL_LABS_GROUP_NAME in groups
