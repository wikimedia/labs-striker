"""Template tags relating to user Toolforge membership and admin status."""

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

from django import template

from striker.tools.models import AccessRequest
from striker.tools.utils import tools_admin

register = template.Library()


@register.filter()
def is_admin(user):
    return tools_admin(user)


@register.simple_tag()
def open_access_requests():
    # This excludes FEEDBACK by design.
    return AccessRequest.objects.filter(status=AccessRequest.PENDING).count()
