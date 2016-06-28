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

import logging

from django.conf import settings
from django_auth_ldap.backend import LDAPBackend
from ratelimitbackend.backends import RateLimitMixin
import ipware.ip


logger = logging.getLogger(__name__)


class RateLimitedLDAPBackend(RateLimitMixin, LDAPBackend):
    """Add rate limiting to LDAPBackend."""
    minutes = 5
    requests = 15

    def get_ip(self, request):
        """If use of X-Forwared-For headers is enabled, get IP using them."""
        if settings.XFF_USE_XFF_HEADER:
            return ipware.ip.get_trusted_ip(request)
        return super(RateLimitedLDAPBackend, self).get_ip(request)
