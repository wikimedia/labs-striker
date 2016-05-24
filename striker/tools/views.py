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

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# FIXME add tool membership validation
# from django.contrib.auth.decorators import user_passes_test
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from striker import phabricator
from striker.tools.forms import RepoCreateForm
from striker.tools.models import DiffusionRepo
from striker.tools.models import Tool
import functools
import logging


logger = logging.getLogger(__name__)
phab = phabricator.Client.default_client()


def inject_tool(f):
    """Inject a Tool into the wrapped function in place of a 'tool' kwarg."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'tool' in kwargs:
            name = kwargs['tool']
            try:
                kwargs['tool'] = Tool.objects.get(group_name='tools.%s' % name)
            except ObjectDoesNotExist:
                req = args[0]
                messages.error(
                    req, _('Tool %(tool)s not found') % {'tool': name})
                return shortcuts.redirect(
                    urlresolvers.reverse('tools:index'))
        return f(*args, **kwargs)
    return decorated


@login_required
def index(req):
    # FIXME: Should we do this with the Tools model instead? probably.
    tools = sorted(name[6:] for name in req.user.groups.filter(
        name__startswith='tools.').values_list(
            'name', flat=True))
    return shortcuts.render(req, 'tools/index.html', {'tools': tools})


@login_required
@inject_tool
def tool(req, tool):
    return shortcuts.render(req, 'tools/tool.html', {
        'tool': tool,
        'repos': DiffusionRepo.objects.filter(tool=tool.name),
    })


@login_required
@inject_tool
def repo_create(req, tool):
    """Create a new Diffusion repo."""
    form = RepoCreateForm(req.POST or None, req.FILES or None, tool=tool)
    if req.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data['repo_name']
            # FIXME: ensure that repo doesn't already exist (in form?)
            # FIXME: error handling!
            # Convert list of maintainers to list of phab users
            maintainers = [m.full_name for m in tool.maintainers()]
            phab_maintainers = [m['phid'] for m in phab.user_ldapquery(
                maintainers)]
            logger.debug(phab_maintainers)
            # Create repo
            repo = phab.create_repository(name, phab_maintainers)
            logger.debug(repo)
            # Save a local association between the repo and the tool.
            repo_model = DiffusionRepo(
                tool=tool.name, name=name, phid=repo['phid'])
            repo_model.save()
            # Redirect to repo view
            return shortcuts.redirect(
                urlresolvers.reverse('tools:repo_edit', kwargs={
                    'tool':tool.name,
                    'name': name,
            }))

    return shortcuts.render(req, 'tools/repo/create.html', {
        'tool': tool, 'form': form})


@login_required
@inject_tool
def repo_edit(req, tool, name):
    try:
        repo = phab.get_repository(name)
    except KeyError:
        repo = None
    return shortcuts.render(req, 'tools/repo.html', {
        'tool': tool, 'repo_name': name, 'repo': repo})
