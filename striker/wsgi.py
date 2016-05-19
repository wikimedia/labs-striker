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

import os
from django.core.wsgi import get_wsgi_application


def bootstrap_env(wsgi_env, start_resp):
    """Bootstrap environment using wsgi provided environment values.

    Inspired by http://stackoverflow.com/a/32416606/8171
    """
    global application
    for key in ['DJANGO_SETTINGS_MODULE', 'DJANGO_LOG_LEVEL']:
        try:
            os.environ[key] = wsgi_env[key]
        except KeyError:
            pass
    # Replace self in global scope with Django's handler
    application = get_wsgi_application()
    # Handle initial request
    return application(wsgi_env, start_resp)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'striker.settings')
application = bootstrap_env
