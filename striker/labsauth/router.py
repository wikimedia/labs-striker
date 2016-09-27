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

import ldapdb.router


class CustomLdapRouter(ldapdb.router.Router):
    """Custom database router needed until ldapdb releases a version including
    their 4c9b4fb commit."""

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if 'model' in hints and ldapdb.router.is_ldap_model(hints['model']):
            return False
        return None
