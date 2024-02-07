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
from django.conf import settings
from django.core import validators
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from dal import autocomplete
from parsley.decorators import parsleyfy

from striker import gitlab
from striker import phabricator
from striker.tools import utils
from striker.tools.models import AccessRequest
from striker.tools.models import Maintainer
from striker.tools.models import SoftwareLicense
from striker.tools.models import Tool
from striker.tools.models import ToolInfo
from striker.tools.models import ToolInfoTag
from striker.tools.models import ToolUser


gitlab = gitlab.Client.default_client()
phab = phabricator.Client.default_client()


class RepoCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        NAME_ERR_MSG = _(
            "Repository name must begin with {prefix}, and can only contain "
            "a-z, A-Z, 0-9, _, and - characters."
        )
        tool = kwargs.pop('tool')
        super(RepoCreateForm, self).__init__(*args, **kwargs)
        default_name = tool.name
        self.fields['repo_name'] = forms.RegexField(
            label=_("Repository name"),
            regex=r'^{0}[-a-zA-Z0-9_]*$'.format(re.escape(default_name)),
            initial=default_name,
            help_text=NAME_ERR_MSG.format(prefix=default_name),
            min_length=len(default_name),
            max_length=255)

        toolinfo = tool.toolinfo().all()
        if len(toolinfo) == 1 and not toolinfo[0].repository:
            self.fields['mark_as_toolinfo_repository'] = forms.BooleanField(
                label=_(
                    'Set source code repository in toolinfo to this repository'
                ),
                help_text=_(
                    'If selected, the created repository will be marked as '
                    'the source code repository in the toolinfo '
                    'entry. (Recommended if all of the tool code is in a '
                    'single repository.)'
                ),
                initial=True,
            )

    def clean_repo_name(self):
        name = self.cleaned_data.get('repo_name')
        try:
            gitlab.get_repository_by_name(name)
            # If get_repository_by_name doesn't raise a KeyError then its
            # a duplicate name (404 expected for new names)
            raise forms.ValidationError(
                _('Repository "%(name)s" exists.'),
                params={'name': name},
                code='duplicate')
        except KeyError:
            return name


class ProjectCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        NAME_ERR_MSG = _(
            "Must start with {prefix}, and can only contain "
            "a-z, A-Z, 0-9, _, and - characters."
        )
        tool = kwargs.pop('tool')
        super(ProjectCreateForm, self).__init__(*args, **kwargs)
        default_name = 'Tool-{0}'.format(tool.name)
        self.fields['project_name'] = forms.RegexField(
            label=_("Project name"),
            regex=r'^{0}[-a-zA-Z0-9_]*$'.format(re.escape(default_name)),
            initial=default_name,
            help_text=NAME_ERR_MSG.format(prefix=default_name),
            min_length=len(default_name),
            max_length=255
        )

        toolinfo = tool.toolinfo().all()
        if len(toolinfo) == 1:
            if toolinfo[0].description:
                self.fields['project_description'].initial = (
                    toolinfo[0].description
                )

            if not toolinfo[0].issues:
                field = forms.BooleanField(
                    label=_('Set issue tracker in toolinfo to this project'),
                    help_text=_(
                        'If selected, the created Phabricator project will be '
                        'marked as the issue tracker in the toolinfo '
                        'entry. (Recommended)'
                    ),
                    initial=True,
                )
                self.fields['mark_as_toolinfo_issue_tracker'] = field

            if toolinfo[0].repository:
                self.fields['source_code_repository'].initial = (
                    toolinfo[0].repository
                )

        # This needs to be done manually since project_name is added
        # dynamically in the constructor, but needs to appear first.
        self.order_fields(['project_name', 'project_description'])

    project_description = forms.CharField(
        label=_("Project description"),
        widget=forms.Textarea(
            attrs={
                'placeholder': _(
                    'The first sentence is important and will show up in the '
                    '"Browse Project" results. Avoid "Project to keep track '
                    'of..." or "This project tag is meant to collect tasks '
                    'about..." etc. Go straight to the point.'
                ),
                'rows': 4,
            },
        ),
        help_text=_(
            'Phabricator is a public place. Describe the tool in a way that '
            'allows anybody, also outside of the community, to clearly '
            'understand what the project is about. '
            '<a href="{project_details}">More details.</a>'
        ).format(
            project_details=(
                'https://www.mediawiki.org/wiki/Phabricator/'
                'Creating_and_renaming_projects'
                '#Good_practices_for_name_and_description'
            ),
        ),
    )

    source_code_repository = forms.URLField(
        label=_('Source code repository'),
        help_text=_(
            'Optional: URL of the source code repository shown on the project '
            'details page.'
        ),
        required=False,
    )

    def clean_project_name(self):
        name = self.cleaned_data.get('project_name')
        try:
            phab.get_project(name)
            # If get_project doesn't raise an exception then its a dup
            raise forms.ValidationError(
                _('Project "%(name)s" exists.'),
                params={'name': name},
                code='duplicate')
        except KeyError:
            return name


class AccessRequestForm(forms.ModelForm):
    """Form for creating a new access request."""
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


class AccessRequestCommentForm(AccessRequestForm):
    """Form for commenting on an access request."""
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'placeholder': _('Add a publicly visible comment'),
                'rows': 2,
            },
        ),
        required=True,
    )

    class Meta(AccessRequestForm.Meta):
        fields = ('comment',)


class AccessRequestAdminForm(AccessRequestCommentForm):
    """Form for approving/denying an access request."""

    def __init__(self, *args, **kwargs):
        super(AccessRequestAdminForm, self).__init__(*args, **kwargs)
        self.fields['comment'].required = False
        self.fields['comment'].widget.is_required = False

    class Meta(AccessRequestCommentForm.Meta):
        fields = ('status', 'comment', 'suppressed')
        labels = {
            'suppressed': _(
                'Suppress this request (hide from non-admin users)'),
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
        instance = getattr(self, "instance", None)
        if instance and instance.name:
            self.fields['name'].widget.attrs["readonly"] = True

    class Meta:
        model = ToolInfo
        exclude = ('tool',)
        labels = {
            'name': _('Unique toolinfo record name'),
            'title': _('Title'),
            'description': _('Description of tool'),
            'tags': _('Tags'),
            'license': _('Default software license'),
            'authors': _('Authors'),
            'repository': _('Source code repository'),
            'issues': _('Issue tracker'),
            'docs': _('Documentation'),
            'is_webservice': _('This is a webservice'),
            'suburl': _('Path to tool below main webservice.'),
        }
        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': 5,
                },
            ),
            'tags': autocomplete.ModelSelect2Multiple(
                url='tools:tags_autocomplete',
            ),
            'authors': autocomplete.ModelSelect2Multiple(
                url='tools:api:author',
            ),
        }
        help_texts = {
            "name": _("A globally unique toolinfo record name for your tool"),
            "title": _("A descriptive title for this tool"),
            "description": _("A short summary of what this tool does"),
            'license': _(
                'Need help choosing a license? '
                'Try <a href="{choose_a_license}">choosealicense.com</a>.'
            ).format(choose_a_license='https://choosealicense.com/'),
            "authors": _("Authors and maintainers of this tool"),
            "tags": _("Keywords related to this tool and what it does"),
            "repository": _("URL to this tool's source code"),
            "issues": _("URL to this tool's issue tracker"),
            "docs": _("URL to this tool's documentation"),
            "is_webservice": _(
                "If unchecked: toolinfo record in Toolhub and other "
                "directories will link to this tool's documentation URL. If "
                "checked: toolinfo record will link to webservice URL. "
            ),
            "suburl": _(
                "Leave path blank unless you are creating multiple "
                "toolinfo records for a single tool account."
            ),
        }


@parsleyfy
class ToolInfoPublicForm(ToolInfoForm):
    class Meta(ToolInfoForm.Meta):
        exclude = ('name', 'tool', 'license', 'authors', 'is_webservice')


@parsleyfy
class ToolCreateForm(forms.Form):
    # Intersection of username regex suggested by useradd(8)
    # and the RFC 1035 definition of a DNS_LABEL.
    RE_NAME = r'^[a-z]([-a-z0-9]{0,30}[a-z0-9])?$'
    NAME_ERR_MSG = _(
        'Must start with a-z, end with a-z or 0-9, be 1-32 characters long, '
        'and can only contain lowercase a-z, 0-9, and - characters.'
    )

    name = forms.CharField(
        label=_('Tool name'),
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
                # urls.reverse_lazy and I just couldn't get it to work
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
        queryset=SoftwareLicense.objects.none(),
        empty_label=_('-- Choose your software license --'),
        label=_('Default software license'),
        help_text=_(
            'Need help choosing a license? '
            'Try <a href="{choose_a_license}">choosealicense.com</a>.'
        ).format(choose_a_license='https://choosealicense.com/'),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=ToolInfoTag.objects.none(),
        widget=autocomplete.ModelSelect2Multiple(
            url='tools:tags_autocomplete',
        ),
        help_text=_("Keywords related to this tool and what it does"),
        required=False,
    )
    is_webservice = forms.BooleanField(
        label=_("This is a webservice"),
        help_text=_(
            "If unchecked: toolinfo record in Toolhub and other "
            "directories will link to this tool's documentation URL. If "
            "checked: toolinfo record will link to webservice URL. "
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ToolCreateForm, self).__init__(*args, **kwargs)
        self.fields['license'].queryset = SoftwareLicense.objects.filter(
            osi_approved=True).order_by('-recommended', 'slug')
        self.fields['tags'].queryset = ToolInfoTag.objects.all().order_by(
            'name')

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
        queryset=Maintainer.objects.none(),
        widget=autocomplete.ModelSelect2Multiple(
            url='tools:api:maintainer',
        ),
    )
    tools = forms.ModelMultipleChoiceField(
        queryset=ToolUser.objects.none(),
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
        self.fields['maintainers'].queryset = Maintainer.objects.all()
        self.fields['tools'].queryset = ToolUser.objects.all()


class ToolDisableForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tool = kwargs.pop('tool')
        super(ToolDisableForm, self).__init__(*args, **kwargs)
        self.fields['name'] = forms.CharField(
            initial=tool,
            widget=forms.HiddenInput(),
            required=True,
        )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        toolname = '{0}.{1!s}'.format(settings.OPENSTACK_PROJECT, name)
        try:
            Tool.objects.get(cn=toolname)
        except Tool.DoesNotExist:
            raise forms.ValidationError(_('Unknown tool'), code='unknown_tool')
        return name
