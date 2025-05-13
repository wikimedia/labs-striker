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
import django.contrib.auth.admin
from django.utils.translation import gettext_lazy as _

import striker.admin
import striker.labsauth.forms
import striker.labsauth.models


@django.contrib.admin.register(
    striker.labsauth.models.LabsUser, site=striker.admin.site
)
class LabsUserAdmin(django.contrib.auth.admin.UserAdmin):
    fieldsets = (
        (None, {"fields": ("ldapname",)}),
        (_("LDAP info"), {"fields": ("ldapemail", "shellname")}),
        (_("SUL info"), {"fields": ("sulid", "sulname", "sulemail", "realname")}),
        (
            _("Phabricator info"),
            {"fields": ("phabname", "phid", "phabrealname", "phaburl", "phabimage")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("ldapname",),
            },
        ),
    )
    form = striker.labsauth.forms.LabsUserChangeForm
    add_form = striker.labsauth.forms.LabsUserCreationForm
    list_display = (
        "ldapname",
        "ldapemail",
        "shellname",
        "sulid",
        "sulname",
        "is_staff",
    )
    search_fields = ("ldapname", "ldapemail", "shellname", "sulname")
    ordering = ("ldapname",)
    filter_horizontal = ("groups",)
    readonly_fields = ("groups",)


@django.contrib.admin.register(
    django.contrib.admin.models.LogEntry, site=striker.admin.site
)
class LogEntryAdmin(django.contrib.admin.ModelAdmin):
    # From http://stackoverflow.com/a/5516987/8171
    list_display = (
        "action_time",
        "user",
        "content_type",
        "change_message",
        "is_addition",
        "is_change",
        "is_deletion",
    )
    list_filter = ["action_time", "user", "content_type"]
    ordering = ("-action_time",)
    readonly_fields = [
        "user",
        "content_type",
        "object_id",
        "object_repr",
        "action_flag",
        "change_message",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
