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

import re

from django import forms
from django.utils.translation import ugettext_lazy as _

from parsley.decorators import parsleyfy

from striker import phabricator
from striker.tools.models import AccessRequest
from striker.tools.models import SoftwareLicense
from striker.tools.models import ToolInfo


phab = phabricator.Client.default_client()


class RepoCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tool = kwargs.pop('tool')
        super(RepoCreateForm, self).__init__(*args, **kwargs)
        default_name = 'tool-{0}'.format(tool.name)
        self.fields['repo_name'] = forms.RegexField(
            label=_("Repository name"),
            regex=r'^{0}'.format(re.escape(default_name)),
            initial=default_name,
            help_text=_("Repository name must begin with {prefix}.".format(
                prefix=default_name)),
            min_length=len(default_name),
            max_length=255)

    def clean_repo_name(self):
        name = self.cleaned_data.get('repo_name')
        try:
            phab.get_repository(name)
            # If get_repository doesn't raise an exception then its a dup
            raise forms.ValidationError(
                _('Repository "%(name)s" exists.'),
                params={'name': name},
                code='duplicate')
        except KeyError:
            return name


class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields = ('reason',)
        widgets = {
            'reason': forms.Textarea(
                attrs={
                    'placeholder': _(
                        'Briefly explain how you will use Tool '
                        'Labs to benefit the Wikimedia movement.'
                    ),
                    'rows': 5,
                },
            ),
        }


class AccessRequestAdminForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields = ('admin_notes', 'status', 'suppressed')
        widgets = {
            'admin_notes': forms.Textarea(
                attrs={
                    'rows': 5,
                },
            ),
        }


@parsleyfy
class ToolInfoForm(forms.ModelForm):
    comment = forms.CharField(
        label=_('Edit summary'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _(
                    'Description of the changes you are making to '
                    'this toolinfo record.'
                ),
            },
        ),
        help_text=_(
            'By saving changes, you agree to the '
            '<a href="{terms_of_use}">Terms of Use</a>, '
            '<a href="{code_of_conduct}">Code of Conduct</a>, '
            'and you irrevocably agree to release your contribution under '
            'the <a href="{cc_by_sa}">Creative Commons Attribution-ShareAlike '
            '3.0 Unported License</a>. You agree that a hyperlink or URL is '
            'sufficient attribution under the Creative Commons license.'
        ).format(
            terms_of_use='https://wikimediafoundation.org/wiki/Terms_of_Use',
            code_of_conduct='https://www.mediawiki.org/wiki/Code_of_Conduct',
            cc_by_sa='https://creativecommons.org/licenses/by-sa/3.0/',
        ),
    )

    def __init__(self, *args, **kwargs):
        super(ToolInfoForm, self).__init__(*args, **kwargs)
        if 'license' in self.fields:
            license = self.fields['license']
            license.empty_label = _(
                '-- Choose your software license --')
            license.queryset = SoftwareLicense.objects.filter(
                osi_approved=True).order_by('-recommended', 'slug')

    class Meta:
        model = ToolInfo
        exclude = ('tool',)
        labels = {
            'name': _('Unique tool name'),
            'title': _('Title'),
            'description': _('Description of tool'),
            'license': _('Default software license'),
            'authors': _('Authors'),
            'repository': _('Source code repository'),
            'issues': _('Issue tracker'),
            'docs': _('Documentation'),
            'is_webservice': _('This is a webservice'),
            'suburl': _('Path to tool below main webservice'),
        }
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': _('A globally unique name for your tool'),
                },
            ),
            'title': forms.TextInput(
                attrs={
                    'placeholder': _('A descriptive title for your tool'),
                },
            ),
            'description': forms.Textarea(
                attrs={
                    'placeholder': _(
                        'A short summary of what your tool does'
                    ),
                    'rows': 5,
                },
            ),
            'repository': forms.TextInput(
                attrs={
                    'placeholder': _("URL to your tool's source code"),
                },
            ),
            'issues': forms.TextInput(
                attrs={
                    'placeholder': _("URL to your tool's issue tracker"),
                },
            ),
            'docs': forms.TextInput(
                attrs={
                    'placeholder': _("URL to your tool's documentation"),
                },
            ),
        }
        help_texts = {
            'license': _(
                'Need help choosing a license? '
                'Try <a href="{choose_a_license}">choosealicense.com</a>.'
            ).format(choose_a_license='https://choosealicense.com/'),
        }


@parsleyfy
class ToolInfoPublicForm(ToolInfoForm):
    class Meta(ToolInfoForm.Meta):
        exclude = ('name', 'tool', 'license', 'authors', 'is_webservice')
