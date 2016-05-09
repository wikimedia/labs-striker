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

from django import shortcuts
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from striker.tools.models import Tool


@login_required
def tools(req):
    # FIXME: Should we do this with the Tools model instead? probably.
    tools = sorted(name[6:] for name in req.user.groups.filter(
        name__startswith='tools.').values_list(
            'name', flat=True))
    return shortcuts.render(req, 'tools/index.html', {'tools': tools})


@login_required
def tool(req, name):
    try:
        tool = Tool.objects.get(name='tools.%s' % name)
    except ObjectDoesNotExist:
        messages.error(req, _('Tool %(tool)s not found') % {'tool': name})
        return shortcuts.redirect(
            urlresolvers.reverse('tools:index'))
    else:
        return shortcuts.render(req, 'tools/tool.html', {
            'name': name, 'tool': tool})
