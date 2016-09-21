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
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from striker.register import utils


logger = logging.getLogger(__name__)


class LDAPUsername(forms.Form):
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(
            attrs={'placeholder': _('Enter your desired username')}
        ),
        max_length=255,
        required=True,
        # Ultimately we will validate the account name using the MediaWiki
        # API, but these rules will give the user quicker feedback on easy to
        # catch errors.
        validators=[
            validators.RegexValidator(
                regex='^\S',
                message=_('Must not start with whitespace')
            ),
            validators.RegexValidator(
                regex='\S$',
                message=_('Must not end with whitespace')
            ),
            # See MediaWikiTitleCodec::getTitleInvalidRegex()
            validators.RegexValidator(
                regex=(
                    # Any char that is not in $wgLegalTitleChars
                    r'[^'
                    r''' %!"$&'()*,\-./0-9:;=?@A-Z\^_`a-z~'''
                    '\x80-\xFF'
                    r'+]'
                    # URL percent encoding sequences
                    r'|%[0-9A-Fa-f]{2}'
                    # XML/HTML entities
                    '|&([A-Za-z0-9\x80-\xff]+|#([0-9]+|x[0-9A-Fa-f]+));'
                ),
                inverse_match=True,
                message=_(
                    'Value contains illegal characters or character sequences.'
                )
            )
        ]
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if not utils.username_available(username):
            raise forms.ValidationError(_('Username is already in use.'))
        # TODO: check that it isn't banned by some abusefilter type rule
        return username


class ShellUsername(forms.Form):
    shellname = forms.CharField(
        label=_('Shell account'),
        widget=forms.TextInput(
            attrs={'placeholder': _('Enter your desired shell account name')}
        ),
        max_length=32,
        required=True,
        validators=[
            validators.RegexValidator(
                # Unix username regex suggested by useradd(8).
                # We don't allow a leading '_' or trailing '$' however.
                regex=r'^[a-z][a-z0-9_-]{0,31}$',
                message=_(
                    'Must start with a-z, and can only contain '
                    'lowercase a-z, 0-9, _, and - characters.')
            )
        ]
    )

    def clean_shellname(self):
        shellname = self.cleaned_data['shellname']
        if not utils.shellname_available(shellname):
            raise forms.ValidationError(_('Shell account is already in use.'))
        # TODO: check that it isn't banned by some abusefilter type rule
        return shellname


class Email(forms.Form):
    email = forms.EmailField(
        label=_('Email address'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Enter a valid email address'),
                'type': 'email'
            }
        ),
        max_length=255,
        required=True
    )


class Password(forms.Form):
    passwd = forms.CharField(
        label=_('Password'),
        min_length=10,
        required=True,
        widget=forms.PasswordInput(render_value=True)
    )
    confirm = forms.CharField(
        label=_('Confirm password'),
        required=True,
        widget=forms.PasswordInput
    )

    def clean_password(self):
        # TODO: complexity checks?
        pass

    def clean(self):
        super(Password, self).clean()
        passwd = self.cleaned_data.get('passwd')
        confirm = self.cleaned_data.get('confirm')
        if passwd != confirm:
            self.add_error(
                'confirm', ValidationError(_('Passwords do not match.')))
