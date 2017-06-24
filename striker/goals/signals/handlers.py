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

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from striker.goals import GOALS
from striker.labsauth.models import LabsUser


logger = logging.getLogger(__name__)


def check_goal_phab(user):
    """Check LabsUser model for Phabricator data."""
    if user.phabname is not None:
        user.milestones.recordMilestone(GOALS['ACCOUNT_PHAB'])


def check_goal_sul(user):
    """Check LabsUser model for SUL data."""
    if user.oauthtoken is not None:
        user.milestones.recordMilestone(GOALS['ACCOUNT_SUL'])


def check_goal_ssh(ldap):
    """Check LdapUser model for SSH data."""
    if ldap.ssh_keys:
        user = LabsUser.objects.get(ldapname=ldap.cn)
        user.milestones.recordMilestone(GOALS['ACCOUNT_SSH'])


def check_goal_member(user):
    """Check LabsUser model for Toolforge membership."""
    groups = user.groups.values_list('name', flat=True)
    if settings.TOOLS_TOOL_LABS_GROUP_NAME in groups:
        user.milestones.recordMilestone(GOALS['TOOL_MEMBER'])


def check_goal_tool(user):
    """Check LabsUser model for Tool maintainership."""
    groups = user.groups.values_list('name', flat=True)
    for g in groups:
        if g.startswith('tools.'):
            user.milestones.recordMilestone(GOALS['TOOL_MAINTAINER'])
            break


@receiver(user_logged_in, dispatch_uid=__name__)
def on_user_login(sender, request, user, **kwargs):
    check_goal_phab(user)
    check_goal_sul(user)
    check_goal_member(user)
    check_goal_tool(user)
    check_goal_ssh(user.ldapuser)


@receiver(post_save, sender=settings.AUTH_USER_MODEL, dispatch_uid=__name__)
def on_user_save(sender, instance, **kwargs):
    check_goal_phab(instance)
    check_goal_sul(instance)


@receiver(post_save, sender='tools.DiffusionRepo', dispatch_uid=__name__)
def on_diffusion_save(sender, instance, **kwargs):
    instance.created_by.milestones.recordMilestone(GOALS['TOOL_GIT'])


@receiver(post_save, sender='labsauth.LdapUser',  dispatch_uid=__name__)
def on_ldapuser_save(sender, instance, **kwargs):
    check_goal_ssh(instance)
