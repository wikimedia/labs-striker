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

from django import forms
from django.core import validators
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from parsley.decorators import parsleyfy

from striker.register import utils

logger = logging.getLogger(__name__)


@parsleyfy
class LDAPUsername(forms.Form):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Enter your desired username"),
                "autofocus": "autofocus",
                # Parsley gets confused if {value} is url encoded, so wrap in
                # mark_safe().
                # FIXME: I tried everything I could think of to use
                # urls.reverse_lazy and I just couldn't get it to work
                # with mark_safe(). I would get either the URL encoded
                # property value or the __str__ of a wrapper object.
                "data-parsley-remote": mark_safe("/register/api/username/{value}"),
                "data-parsley-trigger": "focusin focusout input",
                "data-parsley-remote-message": _(
                    "Username is already in use or invalid."
                ),
            }
        ),
        max_length=255,
        required=True,
        # Ultimately we will validate the account name using the MediaWiki
        # API, but these rules will give the user quicker feedback on easy to
        # catch errors.
        validators=[
            validators.RegexValidator(
                regex=r"^\S", message=_("Must not start with whitespace")
            ),
            validators.RegexValidator(
                regex=r"\S$", message=_("Must not end with whitespace")
            ),
            validators.RegexValidator(
                regex=utils.get_username_invalid_regex(),
                inverse_match=True,
                message=_("Value contains illegal characters or character sequences."),
            ),
        ],
    )

    def clean_username(self):
        """Validate that username is available."""
        # Make sure that username is capitalized like MW's Title would do.
        # If we get to the check_username_create() call below we will fetch an
        # actually sanitized username from MediaWiki.
        username = self.cleaned_data["username"].strip()
        username = username[0].upper() + username[1:]
        if not utils.username_available(username):
            raise forms.ValidationError(_("Username is already in use."))

        # Check that it isn't banned by some abusefilter type rule
        user = utils.check_username_create(username)
        if user["ok"] is False:
            raise forms.ValidationError(user["error"])

        # Return the canonicalized username from our MW api request
        return user["name"]


@parsleyfy
class ShellUsername(forms.Form):
    # Unix username regex suggested by useradd(8).
    # We don't allow a leading '_' or trailing '$' however.
    RE_NAME = r"^[a-z][a-z0-9_-]{0,31}$"
    NAME_ERR_MSG = _(
        "Must start with a-z, and can only contain "
        "lowercase a-z, 0-9, _, and - characters."
    )

    shellname = forms.CharField(
        label=_("Shell username"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Enter your desired UNIX shell username"),
                "autofocus": "autofocus",
                # Parsley gets confused if {value} is url encoded, so wrap in
                # mark_safe().
                # FIXME: I tried everything I could think of to use
                # urls.reverse_lazy and I just couldn't get it to work
                # with mark_safe(). I would get either the URL encoded
                # property value or the __str__ of a wrapper object.
                "data-parsley-remote": mark_safe("/register/api/shellname/{value}"),
                "data-parsley-trigger": "focusin focusout input",
                "data-parsley-remote-message": _(
                    "Shell username is already in use or invalid."
                ),
                "data-parsley-pattern": RE_NAME,
                "data-parsley-pattern-message": NAME_ERR_MSG,
            }
        ),
        max_length=32,
        validators=[
            validators.RegexValidator(regex=RE_NAME, message=NAME_ERR_MSG),
        ],
    )

    def clean_shellname(self):
        """Validate that shellname is available."""
        shellname = self.cleaned_data["shellname"]
        if not utils.shellname_available(shellname):
            raise forms.ValidationError(_("UNIX shell username is already in use."))

        # Check that it isn't banned by some abusefilter type rule
        user = utils.check_username_create(shellname)
        if user["ok"] is False:
            raise forms.ValidationError(user["error"])

        return shellname


@parsleyfy
class Email(forms.Form):
    email = forms.EmailField(
        label=_("Email address"),
        widget=forms.TextInput(
            attrs={
                "placeholder": _("Enter a valid email address"),
                "type": "email",
                "autofocus": "autofocus",
            }
        ),
        max_length=255,
    )

    def clean_email(self):
        """Normalize email domain to lowercase."""
        email = self.cleaned_data["email"]
        email_name, domain_part = email.strip().rsplit("@", 1)
        return "@".join([email_name, domain_part.lower()])


@parsleyfy
class Password(forms.Form):
    class Meta:
        parsley_extras = {
            "confirm": {
                "equalto": "passwd",
                "error-message": _("Passwords do not match."),
            }
        }

    passwd = forms.CharField(
        label=_("Password"),
        min_length=10,
        widget=forms.PasswordInput(
            attrs={
                "autofocus": "autofocus",
                "class": "check-password-strength-input",
            }
        ),
    )
    confirm = forms.CharField(label=_("Confirm password"), widget=forms.PasswordInput)

    def clean_confirm(self):
        """Validate that both password entries match."""
        passwd = self.cleaned_data.get("passwd")
        confirm = self.cleaned_data.get("confirm")
        if passwd != confirm:
            raise forms.ValidationError(_("Passwords do not match."))
        return confirm


@parsleyfy
class Confirm(forms.Form):
    agree = forms.BooleanField(
        label=_("I agree to comply with the Terms of Use and Code of Conduct")
    )
