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

import ipware
from django.conf import settings


class XForwaredForMiddleware(object):
    """Replace request.META['REMOTE_ADDR'] with X-Forwared-For data."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.STRIKER_USE_XFF_HEADER:
            ip = None
            if settings.IPWARE_TRUSTED_PROXY_LIST:
                ip, _ = ipware.get_client_ip(
                    request,
                    proxy_trusted_ips=settings.IPWARE_TRUSTED_PROXY_LIST,
                )
            if ip is not None:
                request.META["REMOTE_ADDR"] = ip
        response = self.get_response(request)
        return response


class ReferrerPolicyMiddleware(object):
    """Add a Referrer-Policy header to responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        header = "Referrer-Policy"
        if header not in response:
            response[header] = getattr(settings, "REFERRER_POLICY", "strict-origin")
        return response
