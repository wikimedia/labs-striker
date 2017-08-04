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

from django.conf import urls

from striker.tools.views.tool import MaintainerAutocomplete
from striker.tools.views.tool import ToolUserAutocomplete
from striker.tools.views.toolinfo import AuthorAutocomplete
from striker.tools.views.toolinfo import HistoryView
from striker.tools.views.toolinfo import TagAutocomplete


TOOL = r'(?P<tool>[_a-z][-0-9_a-z]*)'
REPO = r'(?P<repo>[_a-zA-Z][-0-9_a-zA-Z]*)'
INFO_ID = r'(?P<info_id>\d+)'
VERSION_ID = r'(?P<version_id>\d+)'

urlpatterns = [
    urls.url(r'^$', 'striker.tools.views.index', name='index'),
    urls.url(
        r'^id/{tool}$'.format(tool=TOOL),
        'striker.tools.views.tool.view',
        name='tool'
    ),
    urls.url(
        r'^id/{tool}/info/create$'.format(tool=TOOL),
        'striker.tools.views.toolinfo.create',
        name='info_create'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}$'.format(
            tool=TOOL,
            info_id=INFO_ID,
        ),
        'striker.tools.views.toolinfo.read',
        name='info_read'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/edit$'.format(
            tool=TOOL,
            info_id=INFO_ID,
        ),
        'striker.tools.views.toolinfo.edit',
        name='info_edit'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/history$'.format(
            tool=TOOL,
            info_id=INFO_ID,
        ),
        HistoryView.as_view(),
        name='info_history'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/history/rev/{version_id}$'.format(
            tool=TOOL,
            info_id=INFO_ID,
            version_id=VERSION_ID,
        ),
        'striker.tools.views.toolinfo.revision',
        name='info_revision'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/history/admin/{version_id}$'.format(
            tool=TOOL,
            info_id=INFO_ID,
            version_id=VERSION_ID,
        ),
        'striker.tools.views.toolinfo.revision',
        name='info_admin'
    ),
    urls.url(
        r'^id/{tool}/repos/create$'.format(tool=TOOL),
        'striker.tools.views.repo.create',
        name='repo_create'
    ),
    urls.url(
        r'^id/{tool}/repos/id/{repo}$'.format(tool=TOOL, repo=REPO),
        'striker.tools.views.repo.view',
        name='repo_view'
    ),
    urls.url(
        r'^id/{tool}/maintainers/$'.format(tool=TOOL),
        'striker.tools.views.tool.maintainers',
        name='maintainers'
    ),
    urls.url(
        r'^membership/$',
        'striker.tools.views.membership.membership',
        name='membership'
    ),
    urls.url(
        r'^membership/apply$',
        'striker.tools.views.membership.apply',
        name='membership_apply'
    ),
    urls.url(
        r'^membership/status/(?P<app_id>\d+)$',
        'striker.tools.views.membership.status',
        name='membership_status'
    ),
    urls.url(
        r'tags/autocomplete/$',
        TagAutocomplete.as_view(),
        name='tags_autocomplete'
    ),
    urls.url(
        r'toolinfo/v1/toolinfo.json$',
        'striker.tools.views.toolinfo.json_v1',
        name='toolinfo'
    ),
    urls.url(
        r'create/$',
        'striker.tools.views.tool.create',
        name='tool_create'
    ),
    urls.url(r'^api/', urls.include(
        urls.patterns(
            'striker.tools.views',
            urls.url(
                r'autocomplete/author',
                AuthorAutocomplete.as_view(),
                name='author'),
            urls.url(
                r'^autocomplete/maintainer$',
                MaintainerAutocomplete.as_view(),
                name='maintainer'),
            urls.url(
                r'^autocomplete/tooluser$',
                ToolUserAutocomplete.as_view(),
                name='tooluser'),
            urls.url(
                r'^toolname/(?P<name>.+)$',
                'tool.toolname_available',
                name='toolname'),
        ),
        namespace='api'
    )),
]
