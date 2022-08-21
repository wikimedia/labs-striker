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

import functools

from django import shortcuts
from django import urls
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _

from striker.tools.models import Tool
from striker.tools.utils import project_member


def inject_tool(f):
    """Inject a Tool into the wrapped function in place of a 'tool' kwarg."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'tool' in kwargs:
            name = kwargs['tool']
            try:
                kwargs['tool'] = Tool.objects.get(
                    cn='{0}.{1}'.format(settings.OPENSTACK_PROJECT, name)
                )
            except ObjectDoesNotExist:
                req = args[0]
                messages.error(
                    req, _('Tool {tool} not found').format(tool=name))
                return shortcuts.redirect(
                    urls.reverse('tools:index'))
        return f(*args, **kwargs)
    return decorated


def require_tools_member(f):
    """Ensure that the active user is a member of the tools project."""
    @functools.wraps(f)
    def decorated(request, *args, **kwargs):
        if project_member(request.user):
            return f(request, *args, **kwargs)
        raise PermissionDenied
    return decorated
