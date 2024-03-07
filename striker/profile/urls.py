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

from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import TemplateView

from striker.profile import views

app_name = "profile"
urlpatterns = [
    path(
        "nojs/",
        login_required(TemplateView.as_view(template_name="profile/nojs.html")),
        name="nojs",
    ),
    path(
        "settings/",
        include(
            [
                path("accounts/", views.accounts, name="accounts"),
                path(
                    "phabricator/",
                    include(
                        [
                            path(
                                "attach", views.phab_attach, name="phabricator_attach"
                            ),
                        ]
                    ),
                ),
                path(
                    "ssh-keys/",
                    include(
                        [
                            path("", views.ssh_keys, name="ssh_keys"),
                            path("delete", views.ssh_key_delete, name="ssh_key_delete"),
                            path("add", views.ssh_key_add, name="ssh_key_add"),
                        ]
                    ),
                ),
                path("change_password/", views.change_password, name="change_password"),
            ]
        ),
    ),
]
