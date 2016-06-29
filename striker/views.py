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
import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def csp_report(req):
    # Adapted from https://github.com/adamalton/django-csp-reports/
    resp = HttpResponse('')
    raw_report = req.body
    if isinstance(raw_report, bytes):
        raw_report = raw_report.decode('utf-8')
    try:
        report = json.loads(raw_report)
    except ValueError:
        # Ignore malformed reports
        pass
    else:
        if 'csp-report' not in report:
            return resp

        if 'line-number' not in report['csp-report']:
            return resp

        if report['csp-report']['line-number'] == 1:
            # Ignore reports of errors on line 1. This is a common signature
            # for CSP errors triggered by client controlled code (e.g. browser
            # plugins that inject CSS/JS into all pages).
            return resp

        logger.info('Content Security Policy violation: %s', raw_report)
    return resp
