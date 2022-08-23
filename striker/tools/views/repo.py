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
from django import urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _

from notifications.signals import notify

from striker import gitlab
from striker.tools.forms import RepoCreateForm
from striker.tools.models import GitlabRepo
from striker.tools.utils import member_or_admin
from striker.tools.views.decorators import inject_tool


logger = logging.getLogger(__name__)
gitlab = gitlab.Client.default_client()


@login_required
@inject_tool
def create(req, tool):
    """Create a new GitLab repo."""
    if not member_or_admin(tool, req.user):
        messages.error(
            req, _('You are not a member of {tool}').format(tool=tool.name))
        return shortcuts.redirect(urls.reverse('tools:index'))

    form = RepoCreateForm(req.POST or None, req.FILES or None, tool=tool)
    if req.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data['repo_name']
            # FIXME: error handling!
            # Verify that at least one maintainer has a GitLab account setup
            maintainers = [m.uid for m in tool.maintainers()]
            gitlab_maintainers = gitlab.user_lookup(maintainers)

            if gitlab_maintainers:
                # Create repo
                # FIXME: error handling!
                repo = gitlab.create_repository(name, maintainers)

                # Save a local association between the repo and the tool.
                repo_model = GitlabRepo(
                    tool=tool.name,
                    name=name,
                    repo_id=repo['id'],
                    created_by=req.user,
                )
                try:
                    repo_model.save()
                    try:
                        tool_group = Group.objects.get(name=tool.cn)
                    except ObjectDoesNotExist:
                        # Can't find group for the tool
                        pass
                    else:
                        notify.send(
                            recipient=tool_group,
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
                        urls.reverse('tools:repo_view', kwargs={
                            'tool': tool.name,
                            'repo': name,
                        }))
                except DatabaseError:
                    logger.exception('repo_model.save failed')
                    messages.error(
                        req,
                        _("Error updating database. [req id: {id}]").format(
                            id=req.id))
            else:
                messages.error(
                    req, 'No GitLab accounts found for tool maintainers.')

    ctx = {
        'tool': tool,
        'form': form,
    }
    return shortcuts.render(req, 'tools/repo/create.html', ctx)


@inject_tool
def view(req, tool, repo):
    ctx = {
        'tool': tool,
        'repo_id': None,
        'name': repo,
        'urls': [],
        'web_url': None,
    }
    try:
        repository = gitlab.get_repository_by_name(repo)
        ctx['repo_id'] = repository['id']
        ctx['urls'] = [
            repository['http_url_to_repo'],
            repository['ssh_url_to_repo'],
        ]
        ctx['web_url'] = repository['web_url']

        # FIXME: Lookup membership details & add to ctx

    except KeyError:
        pass
    except gitlab.APIError as e:
        logger.error(e)

    return shortcuts.render(req, 'tools/repo.html', ctx)
