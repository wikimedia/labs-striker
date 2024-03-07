# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Wikimedia Foundation and contributors.
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

from django import shortcuts, urls
from django.contrib.admin import site as django_site
from django.core.exceptions import PermissionDenied
from django.utils.http import urlencode
from django.views.decorators.cache import never_cache
from ratelimitbackend.admin import RateLimitAdminSite


class StrikerAdminSite(RateLimitAdminSite):
    @never_cache
    def login(self, request, extra_context=None):
        if not request.user.is_authenticated:
            # not authenticated, redirect to main login page
            return shortcuts.redirect(
                urls.reverse("labsauth:login")
                + "?"
                + urlencode(
                    {"next": urls.reverse("admin:index", current_app=self.name)}
                )
            )
        if self.has_permission(request):
            # Already logged-in, redirect to admin index
            return shortcuts.redirect(
                urls.reverse("admin:index", current_app=self.name)
            )
        else:
            # Logged in, but doesn't have required permissions
            raise PermissionDenied("You do not have access to the admin panel.")


site = StrikerAdminSite()


for model, admin in django_site._registry.items():
    site.register(model, admin.__class__)
