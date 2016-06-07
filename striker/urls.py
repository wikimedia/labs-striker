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

from django.conf import settings
from django.conf import urls
from django.conf.urls.static import static
from django.views.generic import TemplateView
import django.contrib.admin

import striker.labsauth.urls
import striker.profile.urls
import striker.tools.urls


urlpatterns = [
    urls.url(
        r'^$',
        TemplateView.as_view(template_name='index.html'),
        name='index'
    ),
    urls.url(r'^csp-report', 'striker.views.csp_report', name='csp_report'),

    urls.url(
        r'^auth/', urls.include(striker.labsauth.urls, namespace='labsauth')),
    urls.url(
        r'^profile/', urls.include(striker.profile.urls, namespace='profile')),
    urls.url(
        r'^tools/', urls.include(striker.tools.urls, namespace='tools')),

    urls.url(r'^contrib-admin/', urls.include(django.contrib.admin.site.urls)),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
