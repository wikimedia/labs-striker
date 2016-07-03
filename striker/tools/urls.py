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


TOOL = r'(?P<tool>[_a-z][-0-9_a-z]*)'
REPO = r'(?P<repo>[_a-z][-0-9_a-z]*)'

urlpatterns = [
    urls.url(r'^$', 'striker.tools.views.index', name='index'),
    urls.url(
        r'^id/{tool}$'.format(tool=TOOL),
        'striker.tools.views.tool',
        name='tool'
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
]
