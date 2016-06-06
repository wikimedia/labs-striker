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

from django import template
from django.conf import settings


logger = logging.getLogger(__name__)
register = template.Library()


@register.inclusion_tag('tools/templatetags/phab_project.html')
def phab_project(project):
    return {
        'phab_url': settings.PHABRICATOR_URL,
        'project': project,
    }


@register.inclusion_tag('tools/templatetags/phab_user.html')
def phab_user(user):
    return {
        'phab_url': settings.PHABRICATOR_URL,
        'user': user,
    }


@register.inclusion_tag('tools/templatetags/phab_policy.html')
def phab_policy(policy, phids):
    return {
        'phab_url': settings.PHABRICATOR_URL,
        'policy': policy,
        'phids': phids,
    }


@register.inclusion_tag('tools/templatetags/phab_rule.html')
def phab_rule(rule, phids):
    return {
        'phab_url': settings.PHABRICATOR_URL,
        'rule': rule,
        'phids': phids,
    }


@register.filter
def get(dictionary, key):
    try:
        return dictionary.get(key)
    except TypeError, e:
        logger.error(
            'Invalid arguments: dictionary=%s key=%s %s', dictionary, key, e)
        return None
