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

from django import shortcuts
from django.contrib import messages
from django.core import urlresolvers
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from formtools.wizard.views import NamedUrlSessionWizardView

from striker.labsauth.models import LabsUser
from striker.labsauth.utils import add_ldap_user
from striker.labsauth.utils import oauth_from_session
from striker.register import forms
from striker.register import utils


logger = logging.getLogger(__name__)


def oauth_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        req = args[0]
        oauth = oauth_from_session(req.session)
        if oauth['username'] is None:
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
    oauth = oauth_from_session(req.session)
    if not utils.sul_available(oauth['username']):
        messages.error(
            req, _('Wikimedia unified account is already in use.'))
        return shortcuts.redirect(urlresolvers.reverse('register:index'))
    return shortcuts.redirect(
        urlresolvers.reverse('register:wizard', kwargs={'step': 'ldap'}))


@never_cache
def username_available(req, name):
    """JSON callback for parsley validation of username.

    Kind of gross, but it returns a 406 status code when the name is not
    available. This is to work with the limited choice of default response
    validators in parsley.
    """
    available = utils.username_available(name)
    if available:
        available = utils.check_username_create(name)['ok']
    status = 200 if available else 406
    return JsonResponse({
        'available': available,
    }, status=status)


@never_cache
def shellname_available(req, name):
    """JSON callback for parsley validation of shell username.

    Kind of gross, but it returns a 406 status code when the name is not
    available. This is to work with the limited choice of default response
    validators in parsley.
    """
    available = utils.shellname_available(name)
    if available:
        available = utils.check_username_create(name)['ok']
    status = 200 if available else 406
    return JsonResponse({
        'available': available,
    }, status=status)


class AccountWizard(NamedUrlSessionWizardView):
    """Class based view that handles the forms for collecting account info."""
    form_list = [
        ('ldap', forms.LDAPUsername),
        ('shell', forms.ShellUsername),
        ('email', forms.Email),
        ('password', forms.Password),
        ('confirm', forms.Confirm),
    ]

    @method_decorator(oauth_required)
    def dispatch(self, *args, **kwargs):
        return super(AccountWizard, self).dispatch(*args, **kwargs)

    def get_template_names(self):
        return ['register/%s.html' % self.steps.current]

    def get_form_initial(self, step):
        oauth = oauth_from_session(self.request.session)
        if step == 'ldap':
            # Suggest SUL username as LDAP username
            return {
                'username': oauth['username'],
            }
        elif step == 'shell':
            # Suggest a munged version of SUL username as shell username
            uname = oauth['username']
            return {
                'shellname': re.sub(r'[^a-z0-9-]', '', uname.lower())
            }
        elif step == 'email':
            # Suggest SUL email as LDAP email
            return {
                'email': oauth['email'],
            }
        else:
            return {}

    def _get_all_forms(self):
        forms = collections.OrderedDict()
        for k in self.get_form_list():
            forms[k] = self.get_form(
                step=k,
                data=self.storage.get_step_data(k)
            )
            forms[k].is_valid()
        return forms

    def get_context_data(self, form, **kwargs):
        context = super(AccountWizard, self).get_context_data(
            form=form, **kwargs)
        oauth = oauth_from_session(self.request.session)
        if self.steps.current == 'confirm':
            context.update({
                'forms': self._get_all_forms(),
                'sul': {
                    'username': oauth['username'],
                }
            })
        return context

    def done(self, form_list, form_dict, **kwargs):
        oauth = oauth_from_session(self.request.session)
        ldap_user = add_ldap_user(
            form_dict['ldap'].cleaned_data['username'],
            form_dict['shell'].cleaned_data['shellname'],
            form_dict['password'].cleaned_data['passwd'],
            form_dict['email'].cleaned_data['email']
        )

        LabsUser.objects.create_from_ldap_user(
            ldap_user,
            sulname=oauth['username'],
            sulemail=oauth['email'],
            realname=oauth['realname'],
            oauthtoken=oauth['token'],
            oauthsecret=oauth['secret'],
        )
        messages.success(
            self.request, _('Account created. Login to continue.'))
        return shortcuts.redirect(urlresolvers.reverse('labsauth:login'))


account_wizard = AccountWizard.as_view(url_name='register:wizard')
