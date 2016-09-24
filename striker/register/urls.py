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


urlpatterns = urls.patterns(
    'striker.register.views',
    urls.url(r'^$', 'index', name='index'),
    urls.url(r'^api/', urls.include(
        urls.patterns(
            'striker.register.views',
            urls.url(
                r'^username/(?P<name>.+)$',
                'username_available', name='username'),
            urls.url(
                r'^shellname/(?P<name>.+)$',
                'shellname_available', name='shellname'),
        ),
        namespace='api'
    )),
    urls.url(r'^oauth$', 'oauth', name='oauth'),
    urls.url(r'^(?P<step>.+)$', 'account_wizard', name='wizard'),
)
