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

import functools
import logging

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import paginator
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _

from striker import phabricator
from striker.tools.forms import RepoCreateForm
from striker.tools.models import DiffusionRepo
from striker.tools.models import Tool


logger = logging.getLogger(__name__)
phab = phabricator.Client.default_client()


def inject_tool(f):
    """Inject a Tool into the wrapped function in place of a 'tool' kwarg."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'tool' in kwargs:
            name = kwargs['tool']
            try:
                kwargs['tool'] = Tool.objects.get(cn='tools.{0}'.format(name))
            except ObjectDoesNotExist:
                req = args[0]
                messages.error(
                    req, _('Tool {tool} not found').format(tool=name))
                return shortcuts.redirect(
                    urlresolvers.reverse('tools:index'))
        return f(*args, **kwargs)
    return decorated


def tool_member(tool, user):
    if user.is_anonymous():
        return False
    return user.ldap_dn in tool.members


def index(req):
    ctx = {
        'my_tools': [],
        'query': req.GET.get('q', ''),
    }
    if not req.user.is_anonymous():
        # TODO: do we need to paginate the user's tools too? Magnus has 60!
        ctx['my_tools'] = Tool.objects.filter(
            members__contains=req.user.ldap_dn).order_by('cn')

    page = req.GET.get('p')
    if ctx['query'] == '':
        tool_list = Tool.objects.all()
    else:
        tool_list = Tool.objects.filter(cn__icontains=ctx['query'])
    tool_list = tool_list.order_by('cn')
    pager = paginator.Paginator(tool_list, 10)
    try:
        tools = pager.page(page)
    except paginator.PageNotAnInteger:
        tools = pager.page(1)
    except paginator.EmptyPage:
        tools = pager.page(pager.num_pages)
    ctx['all_tools'] = tools

    return shortcuts.render(req, 'tools/index.html', ctx)


@inject_tool
def tool(req, tool):
    return shortcuts.render(req, 'tools/tool.html', {
        'tool': tool,
        'repos': DiffusionRepo.objects.filter(tool=tool.name),
        'can_edit': tool_member(tool, req.user),
    })


@login_required
@inject_tool
def repo_create(req, tool):
    """Create a new Diffusion repo."""
    if not tool_member(tool, req.user):
        messages.error(
            req, _('You are not a member of {tool}').format(tool=tool.name))
        return shortcuts.redirect(urlresolvers.reverse('tools:index'))

    form = RepoCreateForm(req.POST or None, req.FILES or None, tool=tool)
    if req.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data['repo_name']
            # FIXME: error handling!
            # * You can not select this edit policy, because you would no
            #   longer be able to edit the object. (ERR-CONDUIT-CORE)
            # Convert list of maintainers to list of phab users
            maintainers = [m.full_name for m in tool.maintainers()]
            try:
                phab_maintainers = [m['phid'] for m in phab.user_ldapquery(
                    maintainers)]
            except KeyError:
                messages.error(
                    req, 'No Phabricator accounts found for tool maintainers.')
            else:
                # Create repo
                # FIXME: error handling!
                repo = phab.create_repository(name, phab_maintainers)
                # Save a local association between the repo and the tool.
                repo_model = DiffusionRepo(
                    tool=tool.name, name=name, phid=repo['phid'],
                    created_by=req.user)
                try:
                    repo_model.save()
                    # Redirect to repo view
                    return shortcuts.redirect(
                        urlresolvers.reverse('tools:repo_view', kwargs={
                            'tool': tool.name,
                            'repo': name,
                        }))
                except DatabaseError:
                    logger.exception('repo_model.save failed')
                    messages.error(
                        req,
                        _("Error updating database. [req id: {id}]").format(
                            id=req.id))

    return shortcuts.render(req, 'tools/repo/create.html', {
        'tool': tool, 'form': form})


@inject_tool
def repo_view(req, tool, repo):
    ctx = {
        'tool': tool,
        'repo': repo,
        'repo_id': None,
        'status': 'unknown',
        'urls': [],
        'policy': {'view': None, 'edit': None, 'push': None},
        'phab_url': settings.PHABRICATOR_URL,
    }
    try:
        repository = phab.get_repository(repo)
        ctx['repo_id'] = repository['id']
        ctx['status'] = repository['fields']['status']
        ctx['urls'] = [
            u['fields']['uri']['display'] for u in
            repository['attachments']['uris']['uris']
            if u['fields']['display']['effective'] == 'always'
        ]

        # Lookup policy details
        policy = repository['fields']['policy']
        policies = phab.get_policies(list(set(policy.values())))
        ctx['policy']['view'] = policies[policy['view']]
        ctx['policy']['edit'] = policies[policy['edit']]
        ctx['policy']['push'] = policies[policy['diffusion.push']]

        # Lookup phid details for custom rules
        phids = []
        for p in policies.values():
            if p['type'] == 'custom':
                for r in p['rules']:
                    phids.extend(r['value'])
        ctx['phids'] = phab.get_phids(list(set(phids)))
    except KeyError:
        pass
    except phabricator.APIError as e:
        logger.error(e)

    return shortcuts.render(req, 'tools/repo.html', ctx)
