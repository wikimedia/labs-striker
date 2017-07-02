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

from django.core.cache import cache

from striker import openstack


OPENSTACK_USERS_CACHE_KEY = 'openstack_users_by_role'


def get_openstack_users():
    users = cache.get(OPENSTACK_USERS_CACHE_KEY)
    if users is None:
        client = openstack.Client.default_client()
        users = client.users_by_role()
        cache.set(OPENSTACK_USERS_CACHE_KEY, users, 3600)
    return users


def purge_openstack_users():
    cache.delete(OPENSTACK_USERS_CACHE_KEY)
