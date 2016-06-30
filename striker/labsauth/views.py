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

import logging

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _
from ratelimitbackend import views as ratelimit_views
import mwoauth

from striker.labsauth import forms
from striker.labsauth import utils

NEXT_PAGE = 'striker.oauth.next_page'
REQUEST_TOKEN_KEY = 'striker.oauth.request_token'
ACCESS_TOKEN_KEY = 'striker.oauth.access_token'

logger = logging.getLogger(__name__)


def login(req):
    resp = ratelimit_views.login(
        request=req,
        template_name='labsauth/login.html',
        authentication_form=forms.LabsAuthenticationForm)
    if 'remember_me' in req.POST:
        req.session.set_expiry(1209600)  # 2 weeks
        req.session.save()
    return resp


def logout(req):
    auth_views.logout(req)
    return shortcuts.redirect(urlresolvers.reverse('index'))


def oauth_initiate(req):
    """Initiate an OAuth login."""
    next_page = req.GET.get('next', None)
    if next_page is not None:
        req.session[NEXT_PAGE] = next_page
    consumer_token = mwoauth.ConsumerToken(
        settings.OAUTH_CONSUMER_KEY, settings.OAUTH_CONSUMER_SECRET)
    try:
        redirect, request_token = mwoauth.initiate(
            settings.OAUTH_MWURL,
            consumer_token,
            req.build_absolute_uri(
                urlresolvers.reverse('labsauth:oauth_callback')))
    except Exception:
        # FIXME: get upstream to use a narrower exception class
        logger.exception('mwoauth.initiate failed')
        messages.error(req, _("OAuth handshake failed."))
        return shortcuts.redirect(next_page or '/')
    else:
        # Convert to unicode for session storage
        req.session[REQUEST_TOKEN_KEY] = utils.tuple_to_unicode(request_token)
        return shortcuts.redirect(redirect)


def oauth_callback(req):
    """OAuth handshake callback."""
    serialized_token = req.session.get(REQUEST_TOKEN_KEY, None)
    if serialized_token is None:
        messages.error(req, _("Session invalid."))
        return shortcuts.redirect(
            urlresolvers.reverse('labsauth:oauth_initiate'))
    # Convert from unicode stored in session to bytes expected by mwoauth
    serialized_token = utils.tuple_to_bytes(serialized_token)

    consumer_token = mwoauth.ConsumerToken(
        settings.OAUTH_CONSUMER_KEY, settings.OAUTH_CONSUMER_SECRET)
    request_token = mwoauth.RequestToken(*serialized_token)
    access_token = mwoauth.complete(
        settings.OAUTH_MWURL,
        consumer_token,
        request_token,
        req.META['QUERY_STRING'])
    # Convert to unicode for session storage
    req.session[ACCESS_TOKEN_KEY] = utils.tuple_to_unicode(access_token)
    req.user.set_accesstoken(access_token)

    sul_user = mwoauth.identify(
        settings.OAUTH_MWURL, consumer_token, access_token)
    req.user.sulname = sul_user['username']
    req.user.sulemail = sul_user['email']
    req.user.realname = sul_user['realname']
    req.user.save()

    return shortcuts.redirect(req.session.get(NEXT_PAGE, '/'))
