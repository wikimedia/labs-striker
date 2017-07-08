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

from django import shortcuts
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _

from notifications.signals import notify

from striker import phabricator
from striker.tools.forms import RepoCreateForm
from striker.tools.models import DiffusionRepo
from striker.tools.utils import member_or_admin
from striker.tools.views.decorators import inject_tool


logger = logging.getLogger(__name__)
phab = phabricator.Client.default_client()


@login_required
@inject_tool
def create(req, tool):
    """Create a new Diffusion repo."""
    if not member_or_admin(tool, req.user):
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
                    try:
                        maintainers = Group.objects.get(name=tool.cn)
                    except ObjectDoesNotExist:
                        # Can't find group for the tool
                        pass
                    else:
                        notify.send(
                            recipient=Group.objects.get(name=tool.cn),
                            sender=req.user,
                            verb=_('created new repo'),
                            target=repo_model,
                            public=True,
                            level='info',
                            actions=[
                                {
                                    'title': _('View repository'),
                                    'href': repo_model.get_absolute_url(),
                                },
                            ],
                        )
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

    ctx = {
        'tool': tool,
        'form': form,
    }
    return shortcuts.render(req, 'tools/repo/create.html', ctx)


@inject_tool
def view(req, tool, repo):
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
