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
import re


class RepoCreateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        tool = kwargs.pop('tool')
        super(RepoCreateForm, self).__init__(*args, **kwargs)
        default_name = 'tool-%s' % tool.name
        self.fields['repo_name'] = forms.RegexField(
            label=_("Repository name"),
            regex=r'^%s' % re.escape(default_name),
            initial=default_name,
            help_text=_("Repository name must begin with %(str)s." % {
                'str': default_name}),
            min_length=len(default_name),
            max_length=50)