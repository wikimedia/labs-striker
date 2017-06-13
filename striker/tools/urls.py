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

import striker.tools.views


TOOL = r'(?P<tool>[_a-z][-0-9_a-z]*)'
REPO = r'(?P<repo>[_a-zA-Z][-0-9_a-zA-Z]*)'
INFO_ID = r'(?P<info_id>\d+)'
VERSION_ID = r'(?P<version_id>\d+)'

urlpatterns = [
    urls.url(r'^$', 'striker.tools.views.index', name='index'),
    urls.url(
        r'^id/{tool}$'.format(tool=TOOL),
        'striker.tools.views.tool',
        name='tool'
    ),
    urls.url(
        r'^id/{tool}/info/create$'.format(tool=TOOL),
        'striker.tools.views.info_create',
        name='info_create'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}$'.format(
            tool=TOOL,
            info_id=INFO_ID,
        ),
        'striker.tools.views.info_read',
        name='info_read'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/edit$'.format(
            tool=TOOL,
            info_id=INFO_ID,
        ),
        'striker.tools.views.info_edit',
        name='info_edit'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/history$'.format(
            tool=TOOL,
            info_id=INFO_ID,
        ),
        striker.tools.views.ToolInfoHistoryView.as_view(),
        name='info_history'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/history/rev/{version_id}$'.format(
            tool=TOOL,
            info_id=INFO_ID,
            version_id=VERSION_ID,
        ),
        'striker.tools.views.info_revision',
        name='info_revision'
    ),
    urls.url(
        r'^id/{tool}/info/id/{info_id}/history/admin/{version_id}$'.format(
            tool=TOOL,
            info_id=INFO_ID,
            version_id=VERSION_ID,
        ),
        'striker.tools.views.info_revision',
        name='info_admin'
    ),
    urls.url(
        r'^id/{tool}/repos/create$'.format(tool=TOOL),
        'striker.tools.views.repo_create',
        name='repo_create'
    ),
    urls.url(
        r'^id/{tool}/repos/id/{repo}$'.format(tool=TOOL, repo=REPO),
        'striker.tools.views.repo_view',
        name='repo_view'
    ),
    urls.url(
        r'^membership/$',
        'striker.tools.views.membership',
        name='membership'
    ),
    urls.url(
        r'^membership/apply$',
        'striker.tools.views.membership_apply',
        name='membership_apply'
    ),
    urls.url(
        r'^membership/status/(?P<app_id>\d+)$',
        'striker.tools.views.membership_status',
        name='membership_status'
    ),
    urls.url(
        r'tags/autocomplete/$',
        striker.tools.views.ToolInfoTagAutocomplete.as_view(),
        name='tags_autocomplete'
    ),
]
