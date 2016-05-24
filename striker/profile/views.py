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

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from striker import phabricator
import logging


logger = logging.getLogger(__name__)


@login_required
def phab(req):
    if not req.user.phid:
        client = phabricator.Client.default_client()
        try:
            r = client.user_ldapquery([req.user.ldapname])[0]
        except phabricator.APIError:
            logger.exception('phab.user_ldapquery failed')
            messages.error(req, _("Error contacting Phabricator."))
        except KeyError, e:
            logger.debug(e)
            messages.error(req, _("No matching Phabricator account found."))
        else:
            req.user.phid = r['phid']
            req.user.phabname = r['userName']
            req.user.phabrealname = r['realName']
            req.user.phaburl = r['uri']
            req.user.phabimage = r['image']
            req.user.save()
    return shortcuts.render(req, 'profile/settings/phabricator.html')
