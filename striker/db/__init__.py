# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 Wikimedia Foundation and contributors.
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
"""Custom MySQL/MariaDB backend.

Extension of the standard Django MySQL database backend that adds
'ROW_FORMAT=dynamic' to generated CREATE TABLE declarations to support
indexes of more than 767 bytes. This allows the use of MySQL's utf8mb4
character encoding on CharField columns longer than 191 characters.

Proper usage requires that the MySQL server is configured with:
  * innodb_file_per_table = 1
  * innodb_file_format    = barracuda
  * innodb_large_prefix   = 1

See also:
  * https://bd808.com/blog/2017/04/17/making-django-migrations-that-work-with-mysql-55-and-utf8mb4/ # noqa
  * https://github.com/wikimedia/debmonitor/commit/6219784ec0187a5f4465dd368931bfb8c77e2f50 # noqa
"""
