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
from django.core import validators
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from dal import autocomplete
from parsley.decorators import parsleyfy

from striker import phabricator
from striker.tools import utils
from striker.tools.models import AccessRequest
from striker.tools.models import Maintainer
from striker.tools.models import SoftwareLicense
from striker.tools.models import ToolInfo
from striker.tools.models import ToolInfoTag
from striker.tools.models import ToolUser


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
                        'Briefly explain how you will use Toolforge '
                        'to benefit the Wikimedia movement.'
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
            'tags': _('Tags'),
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
            'tags': autocomplete.ModelSelect2Multiple(
                url='tools:tags_autocomplete',
            ),
            'authors': autocomplete.ModelSelect2Multiple(
                url='tools:api:author',
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


@parsleyfy
class ToolCreateForm(forms.Form):
    # Unix username regex suggested by useradd(8).
    # We don't allow a leading '_' or trailing '$' however.
    RE_NAME = r'^[a-z][a-z0-9_-]{0,31}$'
    NAME_ERR_MSG = _(
        'Must start with a-z, and can only contain '
        'lowercase a-z, 0-9, _, and - characters.'
    )

    name = forms.CharField(
        label=_('Unique tool name'),
        help_text=_(
            "The tool name is used as part of the URL for the tool's "
            "webservice."
        ),
        widget=forms.TextInput(
            attrs={
                'autofocus': 'autofocus',
                'placeholder': _('A unique name for your tool'),
                # Parsley gets confused if {value} is url encoded, so wrap in
                # mark_safe().
                # FIXME: I tried everything I could think of to use
                # urlresolvers.reverse_lazy and I just couldn't get it to work
                # with mark_safe(). I would get either the URL encoded
                # property value or the __str__ of a wrapper object.
                'data-parsley-remote': mark_safe(
                    '/tools/api/toolname/{value}'),
                'data-parsley-trigger': 'focusin focusout input',
                'data-parsley-remote-message': _(
                    'Tool name is already in use or invalid.'),
                'data-parsley-pattern': RE_NAME,
                'data-parsley-pattern-message': NAME_ERR_MSG,
                'data-parsley-debounce': '500',
            }
        ),
        max_length=32,
        validators=[
            validators.RegexValidator(regex=RE_NAME, message=NAME_ERR_MSG),
        ]
    )
    title = forms.CharField(
        label=_('Title'),
        widget=forms.TextInput(
            attrs={
                'placeholder': _('A descriptive title for your tool'),
            },
        ),
    )
    description = forms.CharField(
        label=_('Description of tool'),
        widget=forms.Textarea(
            attrs={
                'placeholder': _(
                    'A short summary of what your tool will do'
                ),
                'rows': 5,
            },
        ),
    )
    license = forms.ModelChoiceField(
        queryset=SoftwareLicense.objects.filter(
            osi_approved=True).order_by('-recommended', 'slug'),
        empty_label=_('-- Choose your software license --'),
        label=_('Default software license'),
        help_text=_(
            'Need help choosing a license? '
            'Try <a href="{choose_a_license}">choosealicense.com</a>.'
        ).format(choose_a_license='https://choosealicense.com/'),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=ToolInfoTag.objects.all().order_by('name'),
        widget=autocomplete.ModelSelect2Multiple(
            url='tools:tags_autocomplete',
        ),
        required=False,
    )

    def clean_name(self):
        """Validate that name is available."""
        name = self.cleaned_data['name']
        if not utils.toolname_available(name):
            raise forms.ValidationError(_('Tool name is already in use.'))

        # Check that it isn't banned by some abusefilter type rule
        check = utils.check_toolname_create(name)
        if check['ok'] is False:
            raise forms.ValidationError(check['error'])

        return name


class MaintainerChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.cn


@parsleyfy
class MaintainersForm(forms.Form):
    maintainers = MaintainerChoiceField(
        queryset=Maintainer.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='tools:api:maintainer',
        ),
    )
    tools = forms.ModelMultipleChoiceField(
        queryset=ToolUser.objects.all(),
        widget=autocomplete.ModelSelect2Multiple(
            url='tools:api:tooluser',
        ),
        help_text=_(
            'Adding another tool as a maintainer will allow all '
            'maintainers of that tool to access this tool. '
            'It will also allow access to maintainers of any tool added to '
            'that tool, and so on. Make sure you trust everyone and know what '
            'you are doing before selecting anything in the "Tools" section.'
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        tool = kwargs.pop('tool')
        initial = kwargs.pop('initial', {})
        initial['maintainers'] = tool.maintainer_ids()
        initial['tools'] = tool.tool_member_ids()
        kwargs['initial'] = initial
        super(MaintainersForm, self).__init__(*args, **kwargs)
