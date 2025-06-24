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

import mwoauth
from django import shortcuts, urls
from django.conf import settings
from django.contrib import messages
from django.db.utils import DatabaseError, IntegrityError
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from ratelimitbackend import views as ratelimit_views

from striker.labsauth import constants, forms

logger = logging.getLogger(__name__)


@sensitive_post_parameters()
@never_cache
def login(req):
    resp = ratelimit_views.login(
        request=req,
        template_name="labsauth/login.html",
        authentication_form=forms.LabsAuthenticationForm,
        extra_context={
            "password_reset_url": settings.AUTH_LDAP_PASSWORD_RESET_URL,
        },
    )

    if "remember_me" in req.POST:
        req.session.set_expiry(settings.REMEMBER_ME_TTL)
        req.session.save()

    return resp


@never_cache
def oauth_initiate(req):
    """Initiate an OAuth login."""
    next_page = req.GET.get("next", None)
    if next_page is not None:
        req.session[constants.NEXT_PAGE] = next_page
    consumer_token = mwoauth.ConsumerToken(
        settings.OAUTH_CONSUMER_KEY, settings.OAUTH_CONSUMER_SECRET
    )
    try:
        redirect, request_token = mwoauth.initiate(
            settings.OAUTH_MWURL,
            consumer_token,
            req.build_absolute_uri(urls.reverse("labsauth:oauth_callback")),
        )
    except Exception:
        # FIXME: get upstream to use a narrower exception class
        logger.exception("mwoauth.initiate failed")
        messages.error(req, _("OAuth handshake failed."))
        return shortcuts.redirect(next_page or "/")
    else:
        # Convert to unicode for session storage
        req.session[constants.REQUEST_TOKEN_KEY] = request_token
        return shortcuts.redirect(redirect)


@never_cache
def oauth_callback(req):
    """OAuth handshake callback."""
    serialized_token = req.session.get(constants.REQUEST_TOKEN_KEY, None)
    if serialized_token is None:
        messages.error(req, _("Session invalid."))
        return shortcuts.redirect(urls.reverse("labsauth:oauth_initiate"))

    consumer_token = mwoauth.ConsumerToken(
        settings.OAUTH_CONSUMER_KEY, settings.OAUTH_CONSUMER_SECRET
    )
    request_token = mwoauth.RequestToken(*serialized_token)
    access_token = mwoauth.complete(
        settings.OAUTH_MWURL, consumer_token, request_token, req.META["QUERY_STRING"]
    )
    req.session[constants.ACCESS_TOKEN_KEY] = access_token
    sul_user = mwoauth.identify(settings.OAUTH_MWURL, consumer_token, access_token)
    req.session[constants.OAUTH_ID_KEY] = sul_user["sub"]
    req.session[constants.OAUTH_USERNAME_KEY] = sul_user["username"]
    req.session[constants.OAUTH_EMAIL_KEY] = sul_user["email"]

    if req.user.is_authenticated:
        req.user.set_accesstoken(access_token)
        req.user.sulid = sul_user["sub"]
        req.user.sulname = sul_user["username"]
        req.user.sulemail = sul_user["email"]
        try:
            req.user.save()
            messages.info(
                req,
                _(
                    "Updated OAuth credentials for {user}".format(
                        user=sul_user["username"]
                    )
                ),
            )
        except IntegrityError:
            logger.exception("user.save failed")
            messages.error(
                req,
                _(
                    'Wikimedia account "{sul}" is already attached '
                    "to another LDAP account."
                ).format(sul=sul_user["username"]),
            )
        except DatabaseError:
            logger.exception("user.save failed")
            messages.error(
                req,
                _("Error saving OAuth credentials. [req id: {id}]").format(id=req.id),
            )
    else:
        messages.info(
            req,
            _("Authenticated as OAuth user {user}".format(user=sul_user["username"])),
        )

    return shortcuts.redirect(req.session.get(constants.NEXT_PAGE, "/"))
