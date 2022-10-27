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

from django.urls import include
from django.urls import path

from striker.tools import views
from striker.tools.views import membership
from striker.tools.views import repo
from striker.tools.views import tool
from striker.tools.views import toolinfo
from striker.tools.views import project

app_name = 'tools'
urlpatterns = [
    path('', views.index, name='index'),
    path('id/<slug:tool>', views.tool.view, name='tool'),
    path('id/<slug:tool>/', include([
        path('info/', include([
            path('create', toolinfo.create, name='info_create'),
            path('id/<int:info_id>', toolinfo.read, name='info_read'),
            path('id/<int:info_id>/', include([
                path('edit', toolinfo.edit, name='info_edit'),
                path('delete', toolinfo.delete, name='info_delete'),
                path(
                    'history',
                    toolinfo.HistoryView.as_view(), name='info_history'),
                path('history/', include([
                    path(
                        'rev/<int:version_id>',
                        toolinfo.revision, name='info_revision'),
                    path(
                        'admin/<int:version_id>',
                        toolinfo.revision, name='info_admin'),
                ])),
            ])),
        ])),
        path('repos/', include([
            path('create', repo.create, name='repo_create'),
            path('id/<int:repo_id>', repo.view, name='repo_view'),
        ])),
        path('projects/', include([
            path('create', project.create, name='project_create'),
            path('id/<slug:project>', project.view, name='project_view')
        ])),
        path('maintainers/', tool.maintainers, name='maintainers'),
        path('disable/', tool.disable, name='disable'),
        path('enable/', tool.enable, name='enable'),
    ])),
    path('membership/', include([
        path('', membership.membership, name='membership'),
        path('apply', membership.apply, name='membership_apply'),
        path(
            'status/<int:app_id>',
            membership.status, name='membership_status'),
    ])),
    path(
        'tags/autocomplete/',
        toolinfo.TagAutocomplete.as_view(), name='tags_autocomplete'),
    path('toolinfo/v1/toolinfo.json', toolinfo.json_v1, name='toolinfo'),
    path(
        'toolinfo/v1.2/toolinfo.json',
        toolinfo.json_v1_2, name='toolinfo-1.2'),
    path('create', tool.create, name='tool_create'),
    path('api/', include(([
        path('autocomplete/', include([
            path(
                'author',
                toolinfo.AuthorAutocomplete.as_view(), name='author'),
            path(
                'maintainer',
                tool.MaintainerAutocomplete.as_view(), name='maintainer'),
            path(
                'tooluser',
                tool.ToolUserAutocomplete.as_view(), name='tooluser'),
        ])),
        path('toolname/<name>', tool.toolname_available, name='toolname'),
    ], 'api'))),
]
