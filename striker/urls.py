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
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include
from django.urls import path
from django.views.generic.base import RedirectView

import notifications.urls
import ratelimitbackend.admin

import striker.labsauth.urls
import striker.profile.urls
import striker.register.urls
import striker.tools.urls
import striker.views

# Install custom error handler callbacks.
# https://docs.djangoproject.com/en/1.8/topics/http/views/#customizing-error-views
handler400 = 'striker.views.bad_request'  # noqa
handler403 = 'striker.views.permission_denied'  # noqa
handler404 = 'striker.views.page_not_found'  # noqa
handler500 = 'striker.views.server_error'  # noqa

# ratelimitbackend does not autoregister admin modules
ratelimitbackend.admin.autodiscover()

urlpatterns = [
    path('', striker.views.index, name='index'),
    path('csp-report', striker.views.csp_report, name='csp_report'),
    path('e400', striker.views.force_400, name='force_400'),
    path('e403', striker.views.force_403, name='force_403'),
    path('e500', striker.views.force_500, name='force_500'),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("img/favicon.ico")),
        name="favicon",
    ),
    path(
        "robots.txt",
        RedirectView.as_view(url=staticfiles_storage.url("robots.txt")),
        name="robots_txt",
    ),

    path('alerts/', include(notifications.urls, namespace='notifications')),
    path('auth/', include(striker.labsauth.urls, namespace='labsauth')),
    path('profile/', include(striker.profile.urls, namespace='profile')),
    path('register/', include(striker.register.urls, namespace='register')),
    path('tools/', include(striker.tools.urls, namespace='tools')),

    path('contrib-admin/', ratelimitbackend.admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
