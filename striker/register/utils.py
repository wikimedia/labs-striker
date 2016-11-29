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

from striker.tools.models import Maintainer
from striker.labsauth.models import LabsUser


logger = logging.getLogger(__name__)


def sul_available(name):
    try:
        LabsUser.objects.get(sulname=name)
    except LabsUser.DoesNotExist:
        return True
    else:
        return False


def username_available(name):
    try:
        Maintainer.objects.get(full_name=name)
    except Maintainer.DoesNotExist:
        return True
    else:
        return False


def shellname_available(name):
    try:
        Maintainer.objects.get(username=name)
    except Maintainer.DoesNotExist:
        return True
    else:
        return False
