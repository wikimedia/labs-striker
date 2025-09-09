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

import ldap
from django import shortcuts, urls
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.utils import DatabaseError, IntegrityError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.views.decorators.debug import sensitive_post_parameters

from striker import decorators, phabricator
from striker.profile import forms, utils

logger = logging.getLogger(__name__)


@login_required
def accounts(req):
    ctx = {
        "phab_url": settings.PHABRICATOR_URL,
    }
    return shortcuts.render(req, "profile/settings/accounts.html", ctx)


@login_required
def phab_attach(req):
    client = phabricator.Client.default_client()
    try:
        r = client.user_external_lookup([req.user.ldapname], [req.user.sulname])[0]
    except phabricator.APIError:
        logger.exception("phabricator.user_external_lookup failed")
        messages.error(req, _("Error contacting Phabricator."))
    except (KeyError, IndexError):
        messages.warning(req, _("No related Phabricator accounts found."))
    else:
        req.user.phid = r["phid"]
        req.user.phabname = r["userName"]
        req.user.phabrealname = r["realName"]
        req.user.phaburl = r["uri"]
        req.user.phabimage = r["image"]
        try:
            req.user.save()
            messages.info(req, _("Attached Phabricator account."))
        except IntegrityError:
            logger.exception("user.save failed")
            messages.error(
                req,
                _(
                    'Phabricator account "{phab}" is already attached '
                    "to another Developer account."
                ).format(phab=r["userName"]),
            )
        except DatabaseError:
            logger.exception("user.save failed")
            messages.error(
                req, _("Error updating database. [req id: {id}]").format(id=req.id)
            )

    next_page = req.GET.get("next", urls.reverse("profile:accounts"))
    return shortcuts.redirect(next_page)


@login_required
def ssh_keys(req):
    ldapuser = req.user.ldapuser
    ctx = {
        "ssh_keys": [],
        "new_key": forms.SshKeyForm(),
    }
    invalids = 0
    for key in ldapuser.ssh_keys:
        pkey = utils.parse_ssh_key(key)
        if pkey:
            pkey.form = forms.SshKeyDeleteForm(initial={"key_hash": pkey.hash_sha256()})
        else:
            # T174112: handle invalid keys
            invalids += 1
            khash = utils.invalid_key_hash(key)
            pkey = {
                "comment": _("Invalid key"),
                "bits": _("0"),
                "type_name": _("UNKNOWN"),
                "hash_md5": khash,
                "hash_sha256": "",
                "keydata": key,
                "form": forms.SshKeyDeleteForm(initial={"key_hash": khash}),
            }
        ctx["ssh_keys"].append(pkey)
    if invalids:
        messages.error(
            req,
            ngettext(
                "Invalid ssh key detected.",
                "{count} invalid ssh keys detected.",
                invalids,
            ).format(count=invalids),
        )
    return shortcuts.render(req, "profile/settings/ssh-keys.html", ctx)


@login_required
@decorators.confirm_required("profile/settings/ssh-keys/delete-confirm.html")
def ssh_key_delete(req):
    if req.method == "POST":
        form = forms.SshKeyDeleteForm(data=req.POST, request=req)
        if form.is_valid():
            key_hash = form.cleaned_data.get("key_hash")
            ldapuser = req.user.ldapuser
            ldapuser.ssh_keys = form.cleaned_keys
            ldapuser.save()
            messages.info(
                req, _("Deleted SSH key {key_hash}").format(key_hash=key_hash)
            )
        else:
            messages.error(req, _("Key not found."))
    return shortcuts.redirect(urls.reverse("profile:ssh_keys"))


@login_required
def ssh_key_add(req):
    if req.method == "POST":
        ldapuser = req.user.ldapuser
        keys = ldapuser.ssh_keys
        form = forms.SshKeyForm(data=req.POST, keys=keys)
        if form.is_valid():
            keys.append(form.cleaned_data.get("public_key"))
            ldapuser.ssh_keys = keys
            try:
                ldapuser.save()
                messages.info(
                    req,
                    _("Added SSH key {key_hash}").format(
                        key_hash=form.key.hash_sha256()
                    ),
                )
            except ldap.TYPE_OR_VALUE_EXISTS:
                logger.exception("Failed to add ssh key")
                messages.error(
                    req, _("Error saving ssh key. [req id: {id}]").format(id=req.id)
                )
        else:
            # Pull the error message out of the form's errors
            messages.error(req, form.errors["public_key"][0])
    return shortcuts.redirect(urls.reverse("profile:ssh_keys"))


@sensitive_post_parameters()
@login_required
def change_password(req):
    if req.method == "POST":
        form = forms.PasswordChangeForm(data=req.POST, user=req.user)
        if form.is_valid():
            form.save()
            messages.info(req, _("Password changed"))
            # We do not need to mess with update_session_auth_hash because
            # LDAP passwords are detached from the normal Django session
            # management methods.
            return shortcuts.redirect(urls.reverse("profile:change_password"))
    else:
        form = forms.PasswordChangeForm(user=req.user)
    ctx = {
        "change_password_form": form,
    }
    return shortcuts.render(req, "profile/settings/change-password.html", ctx)
