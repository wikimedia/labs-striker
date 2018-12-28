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

from django import shortcuts
from django import urls
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils import functional
from django.utils import http

from striker.labsauth import constants


class OathMiddleware(object):
    """Ensure that OATH account protection is enforced for configured users"""
    def process_request(self, request):
        assert hasattr(request, 'user'), "AuthenticationMiddleware required"

        plain_user = request.user
        request.user = functional.SimpleLazyObject(
            lambda: self.decorate_oath_user(request, plain_user))

        if not plain_user.is_authenticated():
            return None

        oath_path = urls.reverse(settings.OATHMIDDLEWARE_REDIRECT)
        request_path = request.path_info
        if request_path == oath_path:
            # Don't redirect if the user is already on the token entry page
            return None

        oath_required = request.session.get(constants.OATH_REQUIRED, False)
        if oath_required and not request.user.oath_verified():
            # Redirect the user to the oath input form
            return shortcuts.redirect(
                "%s?%s" % (
                    oath_path,
                    http.urlencode({
                        REDIRECT_FIELD_NAME: request.get_full_path(),
                    })
                )
            )
        return None

    def decorate_oath_user(self, request, user):
        """Decorate the user with oath data."""
        user._oath_required = request.session.get(
            constants.OATH_REQUIRED, False)
        user._oath_time = None

        user.oath_time = lambda: user._oath_time
        user.oath_verified = lambda: user._oath_time is not None
        user.oath_required = lambda: user._oath_required

        if user.is_authenticated() and user.oath_required():
            oath_data = request.session.get(constants.OATH_INFO)
            if oath_data is not None:
                if oath_data['user'] != user.ldapname:
                    del request.session[constants.OATH_INFO]
                else:
                    user._oath_time = oath_data['time']
        return user
