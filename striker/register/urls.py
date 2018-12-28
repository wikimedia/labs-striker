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

from striker.register import views

api_patterns = ([
    path('username/<name>', views.username_available, name='username'),
    path('shellname/<name>', views.shellname_available, name='shellname'),
], 'api')

app_name = 'register'
urlpatterns = [
    path('', views.index, name='index'),
    path('api/', include(api_patterns)),
    path('oauth', views.oauth, name='oauth'),
    path('<step>', views.account_wizard, name='wizard'),
]
