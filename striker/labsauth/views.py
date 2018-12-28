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
from django import urls
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import views as auth_views
from django.db.utils import DatabaseError
from django.db.utils import IntegrityError
from django.utils.six.moves.urllib.parse import urlparse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from ratelimitbackend import views as ratelimit_views
import mwoauth

from striker.labsauth import constants
from striker.labsauth import forms
from striker.labsauth import utils


logger = logging.getLogger(__name__)


@sensitive_post_parameters()
@never_cache
def login(req):
    resp = ratelimit_views.login(
        request=req,
        template_name='labsauth/login.html',
        authentication_form=forms.LabsAuthenticationForm)

    if 'remember_me' in req.POST:
        req.session.set_expiry(settings.REMEMBER_ME_TTL)
        req.session.save()

    if req.user.is_authenticated():
        # Flag the session with OATH status and expect that OathMiddleware is
        # installed to force the user to provide validation if needed
        req.session[constants.OATH_REQUIRED] = utils.oath_enabled(req.user)

    return resp


@sensitive_post_parameters()
@never_cache
def oath(req):
    redirect_to = req.POST.get(
        REDIRECT_FIELD_NAME, req.GET.get(REDIRECT_FIELD_NAME, ''))
    if req.method == 'POST':
        form = forms.OathVerifyForm(data=req.POST, request=req)
        if form.is_valid():
            netloc = urlparse(redirect_to)[1]
            if not redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL
            elif netloc and netloc != req.get_host():
                redirect_to = settings.LOGIN_REDIRECT_URL
            return shortcuts.redirect(redirect_to)
    else:
        form = forms.OathVerifyForm()
    return shortcuts.render(req, 'labsauth/oath.html', {'form': form})


def logout(req):
    auth_views.logout(req)
    return shortcuts.redirect(urls.reverse('index'))


@never_cache
def oauth_initiate(req):
    """Initiate an OAuth login."""
    next_page = req.GET.get('next', None)
    if next_page is not None:
        req.session[constants.NEXT_PAGE] = next_page
    consumer_token = mwoauth.ConsumerToken(
        settings.OAUTH_CONSUMER_KEY, settings.OAUTH_CONSUMER_SECRET)
    try:
        redirect, request_token = mwoauth.initiate(
            settings.OAUTH_MWURL,
            consumer_token,
            req.build_absolute_uri(
                urls.reverse('labsauth:oauth_callback')))
    except Exception:
        # FIXME: get upstream to use a narrower exception class
        logger.exception('mwoauth.initiate failed')
        messages.error(req, _("OAuth handshake failed."))
        return shortcuts.redirect(next_page or '/')
    else:
        # Convert to unicode for session storage
        req.session[constants.REQUEST_TOKEN_KEY] = utils.tuple_to_unicode(
            request_token)
        return shortcuts.redirect(redirect)


@never_cache
def oauth_callback(req):
    """OAuth handshake callback."""
    serialized_token = req.session.get(constants.REQUEST_TOKEN_KEY, None)
    if serialized_token is None:
        messages.error(req, _("Session invalid."))
        return shortcuts.redirect(
            urls.reverse('labsauth:oauth_initiate'))
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
    req.session[constants.ACCESS_TOKEN_KEY] = utils.tuple_to_unicode(
        access_token)
    sul_user = mwoauth.identify(
        settings.OAUTH_MWURL, consumer_token, access_token)
    req.session[constants.OAUTH_USERNAME_KEY] = sul_user['username']
    req.session[constants.OAUTH_EMAIL_KEY] = sul_user['email']
    req.session[constants.OAUTH_REALNAME_KEY] = sul_user['realname']

    if req.user.is_authenticated():
        req.user.set_accesstoken(access_token)
        req.user.sulname = sul_user['username']
        req.user.sulemail = sul_user['email']
        req.user.realname = sul_user['realname']
        try:
            req.user.save()
            messages.info(
                req, _("Updated OAuth credentials for {user}".format(
                    user=sul_user['username'])))
        except IntegrityError:
            logger.exception('user.save failed')
            messages.error(
                req,
                _(
                    'Wikimedia account "{sul}" is already attached '
                    'to another LDAP account.'
                ).format(sul=sul_user['username']))
        except DatabaseError:
            logger.exception('user.save failed')
            messages.error(
                req,
                _("Error saving OAuth credentials. [req id: {id}]").format(
                    id=req.id))
    else:
        messages.info(
            req, _("Authenticated as OAuth user {user}".format(
                user=sul_user['username'])))

    return shortcuts.redirect(req.session.get(constants.NEXT_PAGE, '/'))
