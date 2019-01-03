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

import itertools
import logging

from django import shortcuts
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from dal import autocomplete
from notifications.signals import notify
import reversion
import reversion.models

from striker.labsauth.models import LabsUser
from striker.tools import utils
from striker.tools.forms import MaintainersForm
from striker.tools.forms import ToolCreateForm
from striker.tools.models import Author
from striker.tools.models import DiffusionRepo
from striker.tools.models import Maintainer
from striker.tools.models import ToolInfo
from striker.tools.models import ToolUser
from striker.tools.utils import member_or_admin
from striker.tools.views.decorators import inject_tool
from striker.tools.views.decorators import require_tools_member


logger = logging.getLogger(__name__)


@inject_tool
def view(req, tool):
    return shortcuts.render(req, 'tools/tool.html', {
        'tool': tool,
        'toolinfo': tool.toolinfo(),
        'repos': DiffusionRepo.objects.filter(tool=tool.name),
        'can_edit': member_or_admin(tool, req.user),
        'can_revert': False,
        'can_suppress': False,
    })


@login_required
@require_tools_member
def create(req):
    form = ToolCreateForm(req.POST or None, req.FILES or None)
    if req.method == 'POST':
        if form.is_valid():
            try:
                tool = utils.create_tool(form.cleaned_data['name'], req.user)
            except Exception:
                logger.exception('utils.create_tool failed')
                messages.error(
                    req,
                    _("Error creating tool. [req id: {id}]").format(
                        id=req.id))
            else:
                messages.info(
                    req, _("Tool {} created".format(tool.name)))
                try:
                    with reversion.create_revision():
                        toolinfo = ToolInfo(
                            name='toolforge.{}'.format(
                                form.cleaned_data['name']),
                            tool=form.cleaned_data['name'],
                            title=form.cleaned_data['title'],
                            description=form.cleaned_data['description'],
                            license=form.cleaned_data['license'],
                            is_webservice=False,
                        )
                        reversion.set_user(req.user)
                        reversion.set_comment('Tool created')
                        toolinfo.save()
                        founder, created = Author.objects.get_or_create(
                            name=req.user.get_full_name())
                        toolinfo.authors.add(founder)
                        if form.cleaned_data['tags']:
                            toolinfo.tags.add(*form.cleaned_data['tags'])
                except Exception:
                    logger.exception('ToolInfo create failed')
                    messages.error(
                        req,
                        _("Error creating toolinfo. [req id: {id}]").format(
                            id=req.id))
                try:
                    maintainers = Group.objects.get(name=tool.cn)
                except ObjectDoesNotExist:
                    # Can't find group for the tool
                    pass
                else:
                    # Do not set tool as the notification target because the
                    # framework does not understand LDAP models.
                    notify.send(
                        recipient=maintainers,
                        sender=req.user,
                        verb=_('created tool {}').format(tool.name),
                        public=True,
                        level='info',
                        actions=[
                            {
                                'title': _('View tool'),
                                'href': tool.get_absolute_url(),
                            },
                        ],
                    )

                return shortcuts.redirect(tool.get_absolute_url())
    ctx = {
        'form': form,
    }
    return shortcuts.render(req, 'tools/create.html', ctx)


@never_cache
def toolname_available(req, name):
    """JSON callback for parsley validation of tool name.

    Kind of gross, but it returns a 406 status code when the name is not
    available. This is to work with the limited choice of default response
    validators in parsley.
    """
    available = utils.toolname_available(name)
    if available:
        available = utils.check_toolname_create(name)['ok']
    status = 200 if available else 406
    return JsonResponse({
        'available': available,
    }, status=status)


@login_required
@inject_tool
def maintainers(req, tool):
    """Manage the maintainers list for a tool"""
    if not member_or_admin(tool, req.user):
        messages.error(
            req, _('You are not a member of {tool}').format(tool=tool.name))
        return shortcuts.redirect(tool.get_absolute_url())
    form = MaintainersForm(req.POST or None, req.FILES or None, tool=tool)
    if req.method == 'POST':
        if form.is_valid():
            old_members = set(tool.members)
            new_members = set(
                m.dn for m in itertools.chain(
                    form.cleaned_data['maintainers'],
                    form.cleaned_data['tools']
                )
            )

            # LDAP doesn't like it when we change the list to be the same
            # list, so make sure there is some delta before saving
            if old_members == new_members:
                messages.warning(req, _('Maintainers unchanged'))
                return shortcuts.redirect(tool.get_absolute_url())

            tool.members = sorted(new_members)
            tool.save()

            maintainers, created = Group.objects.get_or_create(name=tool.cn)
            added_maintainers = list(new_members - old_members)
            removed_maintainers = list(old_members - new_members)
            for dn in added_maintainers:
                uid = dn.split(',')[0][4:]
                logger.info('Added %s', uid)
                try:
                    added = LabsUser.objects.get(shellname=uid)
                except ObjectDoesNotExist:
                    # No local user for this account
                    logger.info('No LabsUser found for %s', uid)
                    pass
                else:
                    # Add user to the mirrored group
                    added.groups.add(maintainers.id)
                    # Do not set tool as the notification target because
                    # the framework does not understand LDAP models.
                    notify.send(
                        recipient=added,
                        sender=req.user,
                        verb=_(
                            'added you as a maintainer of {}'
                        ).format(tool.name),
                        public=True,
                        level='info',
                        actions=[
                            {
                                'title': _('View tool'),
                                'href': tool.get_absolute_url(),
                            },
                        ],
                    )

            for dn in removed_maintainers:
                uid = dn.split(',')[0][4:]
                logger.info('Removed %s', uid)
                try:
                    removed = LabsUser.objects.get(shellname=uid)
                except ObjectDoesNotExist:
                    # No local user for this account
                    logger.info('No LabsUser found for %s', uid)
                    pass
                else:
                    # Add user to the mirrored group
                    removed.groups.remove(maintainers.id)
                    # Do not set tool as the notification target because
                    # the framework does not understand LDAP models.
                    notify.send(
                        recipient=removed,
                        sender=req.user,
                        verb=_(
                            'removed you from the maintainers of {}'
                        ).format(tool.name),
                        public=True,
                        level='info',
                        actions=[
                            {
                                'title': _('View tool'),
                                'href': tool.get_absolute_url(),
                            },
                        ],
                    )

            messages.info(req, _('Maintainers updated'))
            return shortcuts.redirect(tool.get_absolute_url())

    ctx = {
        'tool': tool,
        'form': form,
    }
    return shortcuts.render(req, 'tools/maintainers.html', ctx)


class MaintainerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Maintainer.objects.none()
        qs = Maintainer.objects.all()
        if self.q:
            qs = qs.filter(cn__icontains=self.q)
        qs.order_by('cn')
        return qs

    def get_result_label(self, result):
        return result.cn


class ToolUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ToolUser.objects.none()
        qs = ToolUser.objects.all()
        if self.q:
            qs = qs.filter(uid__icontains=self.q)
        qs.order_by('uid')
        return qs

    def get_result_label(self, result):
        return result.name
