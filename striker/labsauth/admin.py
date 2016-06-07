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

from django.utils.translation import ugettext_lazy as _
import django.contrib.admin
import django.contrib.auth.admin

import striker.labsauth.forms
import striker.labsauth.models


class LabsUserAdmin(django.contrib.auth.admin.UserAdmin):
    fieldsets = (
        (None, {'fields': ('ldapname',)}),
        (_('LDAP info'), {'fields': ('ldapemail', 'shellname')}),
        (_('SUL info'), {'fields': ('sulname', 'sulemail', 'realname')}),
        (_('Phabricator info'), {'fields': (
            'phabname', 'phid', 'phabrealname', 'phaburl', 'phabimage')}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser', 'groups',
            'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('ldapname',),
        }),
    )
    form = striker.labsauth.forms.LabsUserChangeForm
    add_form = striker.labsauth.forms.LabsUserCreationForm
    list_display = (
        'ldapname', 'ldapemail', 'shellname', 'sulname', 'is_staff')
    search_fields = ('ldapname', 'ldapemail', 'shellname', 'sulname')
    ordering = ('ldapname',)
    filter_horizontal = ('groups',)


django.contrib.admin.site.register(
    striker.labsauth.models.LabsUser, LabsUserAdmin)
