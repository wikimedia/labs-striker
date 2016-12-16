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

app_name = 'labsauth'
urlpatterns = [
    urls.url(r'login/$', 'striker.labsauth.views.login', name='login'),
    urls.url(r'logout/$', 'striker.labsauth.views.logout', name='logout'),
    urls.url(
        r'oath$',
        'striker.labsauth.views.oath',
        name='oath'
    ),
    urls.url(
        r'initiate$',
        'striker.labsauth.views.oauth_initiate',
        name='oauth_initiate'
    ),
    urls.url(
        r'callback$',
        'striker.labsauth.views.oauth_callback',
        name='oauth_callback'
    ),
]
