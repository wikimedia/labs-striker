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

from django import forms
from django.utils.translation import ugettext_lazy as _

from parsley.decorators import parsleyfy

from striker.profile import utils


class SshKeyDeleteForm(forms.Form):
    key_hash = forms.CharField(
        label=_('SHA512 hash of ssh key'),
        widget=forms.HiddenInput(),
        required=True,
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.cleaned_keys = None
        super(SshKeyDeleteForm, self).__init__(*args, **kwargs)

    def clean_key_hash(self):
        key_hash = self.cleaned_data.get('key_hash')
        hashes = utils.ssh_keys_by_hash(self.request.user)
        if key_hash not in hashes:
            raise forms.ValidationError(
                _('SSH key not found.'), code='key_not_found')
        self.cleaned_keys = [
            key for (hash, key) in hashes.items()
            if hash != key_hash
        ]
        return key_hash


class SshKeyForm(forms.Form):
    public_key = forms.CharField(
        label=_('Public key'),
        widget=forms.Textarea(
            attrs={
                'placeholder': _(
                    "Begins with 'ssh-rsa', 'ssh-dss', 'ssh-ed25519', "
                    "'ecdsa-sha2-nistp256', 'ecdsa-sha2-nistp384', or "
                    "'ecdsa-sha2-nistp521'"
                ),
            }
        ),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.keys = kwargs.pop('keys', [])
        super(SshKeyForm, self).__init__(*args, **kwargs)

    def clean_public_key(self):
        pub_key = self.cleaned_data.get('public_key').strip()
        key = utils.parse_ssh_key(pub_key)
        if key is None:
            # TODO: Try to cleanup the data and parse it again?
            # OpenStackManager checks for PuTTY's weird key format and tries
            # to extract the public key from that. I don't think that code in
            # OSM actually works though. OSM also passes the key data through
            # `ssh-keygen -i` for validation. This would have the side effect
            # of extracting the public key from an unencrypted private key.
            raise forms.ValidationError(
                _('Invalid public key.'), code='key_invalid')
        if pub_key in self.keys:
            raise forms.ValidationError(
                _('Public key {hash} already in use.').format(
                    hash=key.hash_sha256()),
                code='key_duplicate')
        self.key = key
        return pub_key


@parsleyfy
class PasswordChangeForm(forms.Form):
    class Meta:
        parsley_extras = {
            'confirm': {
                'equalto': 'passwd',
                'error-message': _('Passwords do not match.'),
            }
        }

    old_password = forms.CharField(
        label=_('Old password'),
        widget=forms.PasswordInput(
            attrs={
                'autofocus': 'autofocus',
            }
        )
    )
    passwd = forms.CharField(
        label=_('New password'),
        min_length=10,
        widget=forms.PasswordInput(
            attrs={
                'class': 'check-password-strength-input',
            }
        )
    )
    confirm = forms.CharField(
        label=_('Confirm new password'),
        widget=forms.PasswordInput
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                _('Your old password was entered incorrectly. '
                  'Please enter it again.'),
                code='password_incorrect')
        return old_password

    def clean_confirm(self):
        """Validate that both password entries match."""
        passwd = self.cleaned_data.get('passwd')
        confirm = self.cleaned_data.get('confirm')
        if passwd != confirm:
            raise forms.ValidationError(_('Passwords do not match.'))
        return confirm

    def save(self):
        self.user.set_password(self.cleaned_data['passwd'])
        return self.user
