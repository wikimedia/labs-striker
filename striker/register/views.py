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

from django import shortcuts
from django.contrib import messages
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _


logger = logging.getLogger(__name__)


def index(req):
    ctx = {}
    if not req.user.is_anonymous():
        messages.error(
            req, _('Logged in users can not create new accounts.'))
        return shortcuts.redirect(urlresolvers.reverse('index'))

    return shortcuts.render(req, 'register/index.html', ctx)
