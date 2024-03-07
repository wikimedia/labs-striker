# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 Wikimedia Foundation and contributors.
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
import logstash


class CeeFormatter(logstash.LogstashFormatterVersion1):
    """Output logstash v1 json records with CEE cookie.

    Thin wrapper around logstash.LogstashFormatterVersion1 that prepends
    a "@cee:" cookie to the output. The cookie is used by rsyslog's
    normalization module to distinguish json and non-json log events.
    """

    def format(self, record):
        return "@cee: {}".format(
            super(CeeFormatter, self).format(record).decode("utf-8")
        )
