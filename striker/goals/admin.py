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

import django.contrib.admin

import striker.admin
from striker.goals import models


@django.contrib.admin.register(models.Milestone, site=striker.admin.site)
class MilestoneAdmin(django.contrib.admin.ModelAdmin):
    list_display = ("goal", "name", "user", "completed_date")
    list_filter = ("completed_date", "goal", "user")
    ordering = ("-completed_date", "user", "goal")
