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
from django.core import paginator

from striker.tools.models import Tool
from striker.tools.utils import project_member


def index(req):
    ctx = {
        'my_tools': [],
        'query': req.GET.get('q', ''),
        'member': False,
    }
    if not req.user.is_anonymous():
        # TODO: do we need to paginate the user's tools too? Magnus has 60!
        ctx['my_tools'] = Tool.objects.filter(
            members__contains=req.user.ldap_dn).order_by('cn')
        ctx['member'] = project_member(req.user)

    page = req.GET.get('p')
    if ctx['query'] == '':
        tool_list = Tool.objects.all()
    else:
        tool_list = Tool.objects.filter(cn__icontains=ctx['query'])
    tool_list = tool_list.order_by('cn')
    pager = paginator.Paginator(tool_list, 10)
    try:
        tools = pager.page(page)
    except paginator.PageNotAnInteger:
        tools = pager.page(1)
    except paginator.EmptyPage:
        tools = pager.page(pager.num_pages)
    ctx['all_tools'] = tools

    return shortcuts.render(req, 'tools/index.html', ctx)
