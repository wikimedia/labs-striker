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

from django.conf import settings
from django.db import models
from ldapdb.models import fields
import ldapdb.models


class Maintainer(ldapdb.models.Model):
    """A tool maintainer."""
    base_dn = settings.TOOLS_MAINTAINER_BASE_DN
    object_classes = ['posixAccount']

    username = fields.CharField(db_column='uid', primary_key=True)
    full_name = fields.CharField(db_column='cn')

    def __str__(self):
        return self.username

    def __unicode__(self):
        return self.username


class ToolManager(models.Manager):
    def get_queryset(self):
        return super(ToolManager, self).get_queryset().filter(
            group_name__startswith='tools.')


class Tool(ldapdb.models.Model):
    """A tool is a specially named LDAP group."""
    base_dn = settings.TOOLS_TOOL_BASE_DN
    object_classes = ['posixGroup', 'groupOfNames']

    objects = ToolManager()

    group_name = fields.CharField(
        db_column='cn', max_length=200, primary_key=True)
    gid = fields.IntegerField(db_column='gidNumber', unique=True)
    maintainer_ids = fields.ListField(db_column='member')

    @property
    def name(self):
        return self.group_name[6:]

    @name.setter
    def name(self, value):
        self.group_name = 'tools.%s' % value

    def maintainers(self):
        # OMG, this is horrible. You can't search LDAP by dn.
        return Maintainer.objects.filter(
            username__in=(
                dn.split(',')[0].split('=')[1] for dn in self.maintainer_ids))

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class DiffusionRepo(models.Model):
    """Associate diffusion repos with Tools."""
    # FIXME: find real length limits
    tool = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phid = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name
