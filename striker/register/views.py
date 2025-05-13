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

import collections
import functools
import logging
import re

from django import shortcuts, urls
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from formtools.wizard.views import NamedUrlSessionWizardView

from striker.labsauth.models import LabsUser
from striker.labsauth.utils import add_ldap_user, oauth_from_session
from striker.register import forms, utils

logger = logging.getLogger(__name__)


def oauth_required(f):
    """Decorator to ensure that OAuth data is present in session."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        req = args[0]
        oauth = oauth_from_session(req.session)
        if oauth["username"] is None:
            messages.error(req, _("Please login with your Wikimedia account"))
            return shortcuts.redirect(urls.reverse("register:index"))
        return f(*args, **kwargs)

    return decorated


def anon_required(f):
    """Decorator to ensure that user is not logged in."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        req = args[0]
        if not req.user.is_anonymous:
            messages.error(req, _("Logged in users can not create new accounts."))
            return shortcuts.redirect(urls.reverse("index"))
        return f(*args, **kwargs)

    return decorated


def check_ip(f):
    """Decorator to ensure that remote ip is not blocked."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        req = args[0]
        block = utils.check_ip_blocked_from_create(req.META["REMOTE_ADDR"])
        if block is not False:
            messages.error(
                req,
                _(
                    "Your IP address has been blocked from creating accounts. "
                    'The reason given was: "%(reason)s"'
                )
                % {"reason": block},
            )
            return shortcuts.redirect(urls.reverse("index"))
        return f(*args, **kwargs)

    return decorated


@anon_required
@check_ip
def index(req):
    ctx = {}
    if settings.FEATURE_ACCOUNT_CREATE:
        templ = "register/index.html"
    else:
        templ = "register/disabled.html"
    return shortcuts.render(req, templ, ctx)


@anon_required
@check_ip
@oauth_required
def oauth(req):
    oauth = oauth_from_session(req.session)
    try:
        # TODO: change to LdapUser once T148048 is done
        user = LabsUser.objects.get(Q(sulname=oauth["username"]) | Q(sulid=oauth["id"]))

        messages.error(
            req,
            _("Wikimedia account in use by existing Developer account %(user)s.")
            % {
                "user": user,
            },
        )
        return shortcuts.redirect(urls.reverse("register:index"))
    except LabsUser.DoesNotExist:
        # Expected case. OAuth identity has no Developer account
        return shortcuts.redirect(
            urls.reverse("register:wizard", kwargs={"step": "ldap"})
        )


@never_cache
def username_available(req, name):
    """JSON callback for parsley validation of username.

    Kind of gross, but it returns a 406 status code when the name is not
    available. This is to work with the limited choice of default response
    validators in parsley.
    """
    available = utils.username_valid(name)
    if available:
        available = utils.username_available(name)
    if available:
        available = utils.check_username_create(name)["ok"]
    status = 200 if available else 406
    return JsonResponse(
        {
            "available": available,
        },
        status=status,
    )


@never_cache
def shellname_available(req, name):
    """JSON callback for parsley validation of shell username.

    Kind of gross, but it returns a 406 status code when the name is not
    available. This is to work with the limited choice of default response
    validators in parsley.
    """
    available = utils.shellname_available(name)
    if available:
        available = utils.check_username_create(name)["ok"]
    status = 200 if available else 406
    return JsonResponse(
        {
            "available": available,
        },
        status=status,
    )


class AccountWizard(NamedUrlSessionWizardView):
    """Class based view that handles the forms for collecting account info."""

    form_list = [
        ("ldap", forms.LDAPUsername),
        ("shell", forms.ShellUsername),
        ("email", forms.Email),
        ("password", forms.Password),
        ("confirm", forms.Confirm),
    ]

    @method_decorator(anon_required)
    @method_decorator(check_ip)
    @method_decorator(oauth_required)
    def dispatch(self, *args, **kwargs):
        return super(AccountWizard, self).dispatch(*args, **kwargs)

    def get_template_names(self):
        return ["register/%s.html" % self.steps.current]

    def get_form_initial(self, step):
        oauth = oauth_from_session(self.request.session)
        if step == "ldap":
            # Suggest SUL username as LDAP username
            return {
                "username": oauth["username"],
            }
        elif step == "shell":
            # Suggest a munged version of SUL username as shell username
            uname = oauth["username"]
            return {"shellname": re.sub(r"[^a-z0-9-]", "", uname.lower())}
        elif step == "email":
            # Suggest SUL email as LDAP email
            return {
                "email": oauth["email"],
            }
        else:
            return {}

    def _get_all_forms(self):
        forms = collections.OrderedDict()
        for k in self.get_form_list():
            forms[k] = self.get_form(step=k, data=self.storage.get_step_data(k))
            forms[k].is_valid()
        return forms

    def get_context_data(self, form, **kwargs):
        context = super(AccountWizard, self).get_context_data(form=form, **kwargs)
        oauth = oauth_from_session(self.request.session)
        if self.steps.current in ["password", "confirm"]:
            context.update(
                {
                    "forms": self._get_all_forms(),
                    "sul": {
                        "username": oauth["username"],
                    },
                }
            )
        return context

    def done(self, form_list, form_dict, **kwargs):
        oauth = oauth_from_session(self.request.session)
        ldap_user = add_ldap_user(
            form_dict["ldap"].cleaned_data["username"],
            form_dict["shell"].cleaned_data["shellname"],
            form_dict["password"].cleaned_data["passwd"],
            form_dict["email"].cleaned_data["email"],
        )

        LabsUser.objects.create_from_ldap_user(
            ldap_user,
            sulid=oauth["id"],
            sulname=oauth["username"],
            sulemail=oauth["email"],
            realname=oauth["realname"],
            oauthtoken=oauth["token"],
            oauthsecret=oauth["secret"],
        )
        messages.success(self.request, _("Account created. Login to continue."))
        return shortcuts.redirect(urls.reverse("labsauth:login"))


account_wizard = AccountWizard.as_view(url_name="register:wizard")
