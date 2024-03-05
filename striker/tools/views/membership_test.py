# -*- coding: utf-8 -*-
#
# Copyright (c) 2024 Wikimedia Foundation and contributors.
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

import pytest
from django.contrib.auth import user_logged_in
from django.contrib.auth.models import Group

import striker.tools.templatetags.membership
from striker.goals import GOALS
from striker.goals.signals.handlers import on_user_login
from striker.labsauth.models import LabsUser
from striker.tools import GOALS_REQUIRED_FOR_MEMBERSHIP_APPLICATION
from striker.tools.models import AccessRequest


@pytest.fixture()
def mock_things_for_tests(settings, monkeypatch):
    # Mock a bunch of things so that we can run tests.
    # TODO: make this less of a hack and also much more reusable.

    settings.AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

    real_create_superuser = LabsUser._default_manager.create_superuser

    def create_superuser(**fields):
        fields["username"] = fields["ldapname"]
        del fields["ldapname"]
        return real_create_superuser(**fields)

    monkeypatch.setattr(LabsUser._default_manager, "create_superuser", create_superuser)

    monkeypatch.setattr(
        striker.tools.templatetags.membership, "tools_admin", lambda user: True
    )

    assert user_logged_in.disconnect(
        on_user_login, dispatch_uid="striker.goals.signals.handlers"
    )

    yield

    user_logged_in.connect(on_user_login, dispatch_uid="striker.goals.signals.handlers")


def test_apply_redirects_logged_out(client):
    response = client.get("/tools/membership/apply")
    assert response.status_code == 302
    assert response.url == "/auth/login/?next=/tools/membership/apply"


def test_apply_already_member(
    mock_things_for_tests, settings, admin_user, admin_client
):
    group, _ = Group.objects.get_or_create(name=settings.TOOLS_TOOL_LABS_GROUP_NAME)
    admin_user.groups.add(group)

    response = admin_client.get("/tools/membership/apply")
    assert response.status_code == 303
    assert response.url == "/tools/"


def test_apply_redirects_with_open_app(mock_things_for_tests, admin_user, admin_client):
    access_request = AccessRequest.objects.create(
        user=admin_user,
        reason="weee",
        status=AccessRequest.PENDING,
    )

    response = admin_client.get("/tools/membership/apply")
    assert response.status_code == 303
    assert response.url == f"/tools/membership/status/{access_request.id}"


def test_apply_errors_without_goals(mock_things_for_tests, admin_user, admin_client):
    response = admin_client.get("/tools/membership/apply")
    assert b"finish setting up your account" in response.content


def test_apply_shows_form(mock_things_for_tests, admin_user, admin_client):
    # Closed access requests are ignored.
    AccessRequest.objects.create(
        user=admin_user,
        reason="weee",
        status=AccessRequest.DECLINED,
    )

    for goal in GOALS_REQUIRED_FOR_MEMBERSHIP_APPLICATION:
        admin_user.milestones.recordMilestone(GOALS[goal])

    response = admin_client.get("/tools/membership/apply")
    assert response.status_code == 200
    assert b"Request Toolforge project membership" in response.content
    assert (
        b'<input class="btn btn-success" type="submit" value="Join" />'
        in response.content
    )
