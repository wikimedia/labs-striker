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
