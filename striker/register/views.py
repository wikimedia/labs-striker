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

import functools
import logging
import re

from django import shortcuts
from django.contrib import messages
from django.core import urlresolvers
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from formtools.wizard.views import NamedUrlSessionWizardView

from striker.labsauth.views import OAUTH_EMAIL_KEY
from striker.labsauth.views import OAUTH_USERNAME_KEY
from striker.register import forms
from striker.register import utils


logger = logging.getLogger(__name__)


def oauth_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        req = args[0]
        if req.session.get(OAUTH_USERNAME_KEY, None) is None:
            messages.error(
                req, _('Please login with your Wikimedia unified account'))
            return shortcuts.redirect(urlresolvers.reverse('register:index'))
        return f(*args, **kwargs)
    return decorated


def index(req):
    ctx = {}
    if not req.user.is_anonymous():
        messages.error(
            req, _('Logged in users can not create new accounts.'))
        return shortcuts.redirect(urlresolvers.reverse('index'))
    return shortcuts.render(req, 'register/index.html', ctx)


@oauth_required
def oauth(req):
    if not utils.sul_available(req.session[OAUTH_USERNAME_KEY]):
        messages.error(
            req, _('Wikimedia unified account is already in use.'))
        return shortcuts.redirect(urlresolvers.reverse('register:index'))
    return shortcuts.redirect(
        urlresolvers.reverse('register:wizard', kwargs={'step': 'ldap'}))


class AccountWizard(NamedUrlSessionWizardView):
    form_list = [
        ('ldap', forms.LDAPUsername),
        ('shell', forms.ShellUsername),
        ('email', forms.Email),
        ('password', forms.Password),
    ]

    @method_decorator(oauth_required)
    def dispatch(self, *args, **kwargs):
        return super(AccountWizard, self).dispatch(*args, **kwargs)

    def get_template_names(self):
        return ['register/%s.html' % self.steps.current]

    def get_form_initial(self, step):
        if step == 'ldap':
            # Suggest SUL username as LDAP username
            return {
                'username': self.request.session[OAUTH_USERNAME_KEY]
            }
        elif step == 'shell':
            # Suggest a munged version of SUL username as shell username
            uname = self.request.session[OAUTH_USERNAME_KEY]
            return {
                'shellname': re.sub(r'[^a-z0-9-]', '', uname.lower())
            }
        elif step == 'email':
            # Suggest SUL email as LDAP email
            return {
                'email': self.request.session[OAUTH_EMAIL_KEY]
            }
        else:
            return {}

    def done(self, form_list, **kwargs):
        # TODO: create account
        messages.success(
            self.request, _('Account created. Login to continue.'))
        return shortcuts.redirect(urlresolvers.reverse('labsauth:login'))
