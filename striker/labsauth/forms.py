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

from ratelimitbackend.forms import AuthenticationForm
import mwclient

from striker.labsauth import utils
import striker.labsauth.models


class LabsUserCreationForm(forms.ModelForm):
    class Meta:
        model = striker.labsauth.models.LabsUser
        fields = ('ldapname',)


class LabsUserChangeForm(forms.ModelForm):
    class Meta:
        model = striker.labsauth.models.LabsUser
        fields = '__all__'


class LabsAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LabsAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(
            attrs={'autofocus': ''})


class OathVerifyForm(forms.Form):
    token = forms.CharField(
        label=_('Two-factor authentication code'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _('Authentication code'),
                'autofocus': 'autofocus',
                'autocomplete': 'off',
            }
        ),
        max_length=255,
        required=True,
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super(OathVerifyForm, self).__init__(*args, **kwargs)

    def clean(self):
        token = self.cleaned_data.get('token')
        user = self.request.user

        if user.is_authenticated and token:
            try:
                valid = utils.oath_validate_token(user, token)
            except mwclient.APIError as ex:
                if ex.code == 'ratelimited':
                    raise forms.ValidationError(
                        _('You have exceeded your rate limit. '
                          'Please wait some time and try again.'),
                        code='ratelimited'
                    )
                raise ex

            if not valid:
                raise forms.ValidationError(
                    _('The two-factor authentication token '
                      'provided was invalid.'),
                    code='token_invalid'
                )
            else:
                utils.oath_save_validation(user, self.request)
        return self.cleaned_data
