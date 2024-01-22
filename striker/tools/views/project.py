# -*- coding: utf-8 -*-
#
# Copyright (c) 2020 Wikimedia Foundation and contributors.
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
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.utils.translation import ugettext_lazy as _

import reversion
from notifications.signals import notify

from striker import phabricator
from striker.labsauth.models import LabsUser
from striker.tools.forms import ProjectCreateForm
from striker.tools.models import PhabricatorProject
from striker.tools.utils import member_or_admin
from striker.tools.views.decorators import inject_tool


logger = logging.getLogger(__name__)
phab = phabricator.Client.default_client()


@login_required
@inject_tool
def create(req, tool):
    """Create a new Phabricator project."""
    if not member_or_admin(tool, req.user):
        messages.error(
            req, _('You are not a member of {tool}').format(tool=tool.name))
        return shortcuts.redirect(urls.reverse('tools:index'))
    if tool.is_disabled():
        messages.error(req, _('Tool is disabled.'))
        return shortcuts.redirect(
            urls.reverse('tools:tool', kwargs={'tool': tool.name})
        )

    form = ProjectCreateForm(req.POST or None, req.FILES or None, tool=tool)
    if req.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data['project_name']

            maintainers = [m.cn for m in tool.maintainers()]
            phab_maintainers = []
            try:
                phab_maintainers += [m['phid'] for m in phab.user_ldapquery(
                    maintainers)]
            except KeyError:
                pass
            try:
                phab_maintainers += [
                    m['phid'] for m in phab.user_mediawikiquery(
                        list(LabsUser.objects.filter(
                            ldapname__in=maintainers
                        ).values_list('sulname', flat=True))
                    )
                ]
            except KeyError:
                pass

            if phab_maintainers:
                # Create project
                project = phab.create_project(
                    name,
                    members=list(set(phab_maintainers)),
                    parent=settings.PHABRICATOR_PARENT_PROJECT,
                    description=form.cleaned_data['project_description'],
                )

                # Save a local association between the project and the tool.
                project_model = PhabricatorProject(
                    tool=tool.name, name=name, phid=project['phid'],
                    created_by=req.user)
                try:
                    project_model.save()
                    try:
                        maintainers = Group.objects.get(name=tool.cn)
                    except ObjectDoesNotExist:
                        # Can't find group for the tool
                        pass
                    else:
                        notify.send(
                            recipient=Group.objects.get(name=tool.cn),
                            sender=req.user,
                            verb=_('created new Phabricator project'),
                            target=project_model,
                            public=True,
                            level='info',
                            actions=[
                                {
                                    'title': _('View project'),
                                    'href': project_model.get_absolute_url(),
                                },
                            ],
                        )

                    if form.cleaned_data.get(
                        'mark_as_toolinfo_issue_tracker',
                        False
                    ):
                        toolinfo = tool.toolinfo().get()
                        with reversion.create_revision():
                            reversion.set_user(req.user)
                            reversion.set_comment(
                                'set issue tracker to created Phabricator '
                                'project'
                            )

                            toolinfo.issues = phab.make_project_url(project)
                            toolinfo.save()

                    # Redirect to project view
                    return shortcuts.redirect(
                        urls.reverse('tools:tool', kwargs={
                            'tool': tool.name,
                        }))
                except DatabaseError:
                    logger.exception('project_model.save failed')
                    messages.error(
                        req,
                        _("Error updating database. [req id: {id}]").format(
                            id=req.id))
            else:
                messages.error(
                    req, 'No Phabricator accounts found for tool maintainers.')

    ctx = {
        'tool': tool,
        'form': form,
    }
    return shortcuts.render(req, 'tools/project/create.html', ctx)


@inject_tool
def view(req, tool, project):
    ctx = {
        'tool': tool,
        'project': project,
        'slug': '',
        'project_url': '',
    }

    try:
        project_data = phab.get_project(project)
        ctx['project'] = project_data['fields']['name']
        ctx['slug'] = project_data['fields']['slug']
        ctx['project_url'] = phab.make_project_url(project_data)
    except KeyError:
        pass
    except phabricator.APIError as e:
        logger.error(e)
    return shortcuts.render(req, 'tools/project/view.html', ctx)
