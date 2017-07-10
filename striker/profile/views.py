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
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.db.utils import DatabaseError
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.translation import ugettext_lazy as _

import ldap

from striker import decorators
from striker import phabricator
from striker.profile import forms
from striker.profile import utils


logger = logging.getLogger(__name__)


@login_required
def accounts(req):
    ctx = {
        'phab_url': settings.PHABRICATOR_URL,
    }
    return shortcuts.render(req, 'profile/settings/accounts.html', ctx)


@login_required
def phab_attach(req):
    client = phabricator.Client.default_client()
    try:
        r = client.user_external_lookup(
            [req.user.ldapname], [req.user.sulname])[0]
    except phabricator.APIError:
        logger.exception('phabricator.user_external_lookup failed')
        messages.error(req, _("Error contacting Phabricator."))
    except (KeyError, IndexError):
        messages.warning(req, _("No related Phabricator accounts found."))
    else:
        req.user.phid = r['phid']
        req.user.phabname = r['userName']
        req.user.phabrealname = r['realName']
        req.user.phaburl = r['uri']
        req.user.phabimage = r['image']
        try:
            req.user.save()
            messages.info(req, _("Attached Phabricator account."))
        except DatabaseError:
            logger.exception('user.save failed')
            messages.error(
                req, _("Error updating database. [req id: {id}]").format(
                    id=req.id))

    next_page = req.GET.get(
        'next', urlresolvers.reverse('profile:accounts'))
    return shortcuts.redirect(next_page)


@login_required
def ssh_keys(req):
    ldapuser = req.user.ldapuser
    ctx = {
        'ssh_keys': [utils.parse_ssh_key(key) for key in ldapuser.ssh_keys],
        'new_key': forms.SshKeyForm(),
    }
    for key in ctx['ssh_keys']:
        key.form = forms.SshKeyDeleteForm(
            initial={'key_hash': key.hash_sha256()})
    return shortcuts.render(req, 'profile/settings/ssh-keys.html', ctx)


@login_required
@decorators.confirm_required('profile/settings/ssh-keys/delete-confirm.html')
def ssh_key_delete(req):
    if req.method == 'POST':
        form = forms.SshKeyDeleteForm(data=req.POST, request=req)
        if form.is_valid():
            key_hash = form.cleaned_data.get('key_hash')
            ldapuser = req.user.ldapuser
            ldapuser.ssh_keys = form.cleaned_keys
            ldapuser.save()
            messages.info(
                req,
                _("Deleted SSH key {key_hash}").format(key_hash=key_hash))
        else:
            messages.error(req, _('Key not found.'))
    return shortcuts.redirect(urlresolvers.reverse('profile:ssh_keys'))


@login_required
def ssh_key_add(req):
    if req.method == 'POST':
        ldapuser = req.user.ldapuser
        keys = ldapuser.ssh_keys
        form = forms.SshKeyForm(data=req.POST, keys=keys)
        if form.is_valid():
            keys.append(form.cleaned_data.get('public_key'))
            ldapuser.ssh_keys = keys
            try:
                ldapuser.save()
                messages.info(
                    req,
                    _('Added SSH key {key_hash}').format(
                        key_hash=form.key.hash_sha256()))
            except ldap.TYPE_OR_VALUE_EXISTS as e:
                logger.exception('Failed to add ssh key')
                messages.error(
                    req,
                    _('Error saving ssh key. [req id: {id}]').format(
                        id=req.id))
        else:
            # Pull the error message out of the form's errors
            messages.error(req, form.errors['public_key'][0])
    return shortcuts.redirect(urlresolvers.reverse('profile:ssh_keys'))


@sensitive_post_parameters()
@login_required
def change_password(req):
    if req.method == 'POST':
        form = forms.PasswordChangeForm(data=req.POST, user=req.user)
        if form.is_valid():
            form.save()
            messages.info(req, _('Password changed'))
            # We do not need to mess with update_session_auth_hash because
            # LDAP passwords are detached from the normal Django session
            # management methods.
            return shortcuts.redirect(
                urlresolvers.reverse('profile:change_password'))
    else:
        form = forms.PasswordChangeForm(user=req.user)
    ctx = {
        'change_password_form': form,
    }
    return shortcuts.render(
        req, 'profile/settings/change-password.html', ctx)
