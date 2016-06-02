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

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging


logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def csp_report(req):
    # Ignore a spam report caused by uBlock browser plugin
    # https://github.com/gorhill/uBlock/issues/1170
    if '":root #content > #right > .dose > .doses..."' not in req.body:
        logger.debug('Content Security Policy violation: %s', req.body)
    return HttpResponse('')
