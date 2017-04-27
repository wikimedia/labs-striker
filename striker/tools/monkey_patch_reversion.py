# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 Wikimedia Foundation and contributors.
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

from django.db import models

from reversion.models import Version


# Inspiration from https://stackoverflow.com/a/24668215/8171
#
# Add a 'suppressed' field to the reversion Version model.
# This this will be used to allow suppression of malicious changes by an
# admin.
Version.add_to_class(
    'suppressed',
    models.BooleanField(blank=True, default=False, db_index=True)
)
