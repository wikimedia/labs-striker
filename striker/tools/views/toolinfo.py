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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from dal import autocomplete
import reversion
import reversion.models
import reversion_compare.views

from striker.tools.forms import ToolInfoForm
from striker.tools.forms import ToolInfoPublicForm
from striker.tools.models import Author
from striker.tools.models import Tool
from striker.tools.models import ToolInfo
from striker.tools.models import ToolInfoTag
from striker.tools.utils import member_or_admin
from striker.tools.views.decorators import inject_tool


logger = logging.getLogger(__name__)


@login_required
@inject_tool
def create(req, tool):
    """Create a ToolInfo record."""
    if not member_or_admin(tool, req.user):
        messages.error(
            req, _('You are not a member of {tool}').format(tool=tool.name))
        return shortcuts.redirect(tool.get_absolute_url())

    initial_values = {
        'name': tool.name,
        'author': req.user,
    }
    if ToolInfo.objects.filter(tool=tool.name).count():
        initial_values['name'] = '{}-'.format(tool.name)
    form = ToolInfoForm(
        req.POST or None, req.FILES or None, initial=initial_values)
    if req.method == 'POST':
        if form.is_valid():
            try:
                with reversion.create_revision():
                    reversion.set_comment(form.cleaned_data['comment'])
                    toolinfo = form.save(commit=False)
                    toolinfo.tool = tool.name
                    toolinfo.save()
                    form.save_m2m()
                    reversion.add_to_revision(toolinfo)
                messages.info(
                    req, _("Toolinfo {} created".format(toolinfo.title)))
                return shortcuts.redirect(
                    urlresolvers.reverse('tools:tool', kwargs={
                        'tool': tool.name,
                    }))
            except DatabaseError as dbe:
                logger.exception('ToolInfo.save failed')
                messages.error(
                    req,
                    _("Error updating database. [req id: {id}]").format(
                        id=req.id))
    ctx = {
        'tool': tool,
        'form': form,
    }
    return shortcuts.render(req, 'tools/info/create.html', ctx)


@inject_tool
def read(req, tool, info_id):
    """View a ToolInfo record."""
    toolinfo = shortcuts.get_object_or_404(ToolInfo, pk=info_id, tool=tool)
    ctx = {
        'tool': tool,
        'toolinfo': toolinfo,
    }
    return shortcuts.render(req, 'tools/info/read.html', ctx)


@login_required
@inject_tool
def edit(req, tool, info_id):
    """Create a ToolInfo record."""
    toolinfo = shortcuts.get_object_or_404(ToolInfo, pk=info_id, tool=tool)
    if member_or_admin(tool, req.user):
        form = ToolInfoForm(
            req.POST or None, req.FILES or None, instance=toolinfo)
    else:
        form = ToolInfoPublicForm(
            req.POST or None, req.FILES or None, instance=toolinfo)

    if req.method == 'POST':
        if form.is_valid():
            try:
                with reversion.create_revision():
                    reversion.set_comment(form.cleaned_data['comment'])
                    toolinfo = form.save()
                    reversion.add_to_revision(toolinfo)
                messages.info(
                    req, _("Toolinfo {} updated".format(toolinfo.title)))
                return shortcuts.redirect(
                    urlresolvers.reverse('tools:tool', kwargs={
                        'tool': tool.name,
                    }))
            except DatabaseError:
                logger.exception('ToolInfo.save failed')
                messages.error(
                    req,
                    _("Error updating database. [req id: {id}]").format(
                        id=req.id))
    ctx = {
        'tool': tool,
        'toolinfo': toolinfo,
        'form': form,
    }
    return shortcuts.render(req, 'tools/info/update.html', ctx)


class HistoryView(reversion_compare.views.HistoryCompareDetailView):
    model = ToolInfo
    pk_url_kwarg = 'info_id'
    template_name = 'tools/info/history.html'

    def get_queryset(self):
        qs = super(HistoryView, self).get_queryset()
        return qs.filter(tool=self.kwargs['tool'])

    def _get_action_list(self):
        actions = super(HistoryView, self)._get_action_list()
        for action in actions:
            action['url'] = urlresolvers.reverse(
                'tools:info_revision',
                kwargs={
                    'tool': self.kwargs['tool'],
                    'info_id': self.kwargs['info_id'],
                    'version_id': action['version'].pk,
                },
            )
        return actions

    def get_context_data(self, **kwargs):
        user = self.request.user
        tool = Tool.objects.get(cn='tools.{0}'.format(kwargs['object'].tool))

        ctx = super(HistoryView, self).get_context_data(**kwargs)
        ctx['toolinfo'] = kwargs['object']
        ctx['tool'] = tool
        ctx['show_suppressed'] = member_or_admin(tool, user)
        return ctx


@inject_tool
def revision(req, tool, info_id, version_id):
    """View/revert/suppress a particular version of a ToolInfo model."""
    tool = shortcuts.get_object_or_404(Tool, cn='tools.{}'.format(tool))
    toolinfo = shortcuts.get_object_or_404(ToolInfo, pk=info_id, tool=tool)
    version = shortcuts.get_object_or_404(
        reversion.models.Version, pk=version_id, object_id=info_id)

    can_revert = member_or_admin(tool, req.user)
    can_suppress = member_or_admin(tool, req.user)

    history_url = urlresolvers.reverse(
        'tools:info_history',
        kwargs={
            'tool': tool.name,
            'info_id': info_id,
        })

    if req.method == 'POST' and (
            '_hide' in req.POST or
            '_show' in req.POST
    ):
        if can_suppress:
            try:
                version.suppressed = '_hide' in req.POST
                version.save()
                if version.suppressed:
                    msg = _("Revision {id} hidden")
                else:
                    msg = _("Revision {id} shown")
                messages.info(req, msg.format(id=version_id))
            except DatabaseError:
                logger.exception('Revision.suppress failed')
                messages.error(
                    req,
                    _("Error updating database. [req id: {id}]").format(
                        id=req.id))
        else:
            messages.error(req, _("Tool membership required"))
        return shortcuts.redirect(history_url)

    try:
        # This try/except block is pretty gross, but its the way that
        # django-reversion provides to get a historic model. We start a db
        # transaction, revert the revision, grab the model from the db, render
        # it to a response, and then wrap that rendered response in an
        # exception. We raise the exception to trigger a rollback of the
        # transaction (gross), and then catch the exception and return the
        # wrapped response.
        with transaction.atomic(using=version.db):
            version.revision.revert()
            # Fetch the toolinfo again now that it hav been reverted
            toolinfo = shortcuts.get_object_or_404(
                ToolInfo, pk=info_id, tool=tool.name)

            if req.method == 'POST':
                if '_revert' in req.POST:
                    if not can_revert:
                        messages.error(req, _("Tool membership required"))
                        raise reversion.views._RollBackRevisionView(None)
                    try:
                        with reversion.create_revision():
                            dt = version.revision.date_created.strftime(
                                '%Y-%m-%dT%H:%M:%S%z')
                            reversion.set_user(req.user)
                            reversion.set_comment(
                                '{} reverted to version saved on {}'.format(
                                    req.user,
                                    dt))
                            toolinfo.save()
                            messages.info(
                                req,
                                _("Toolinfo {} reverted to {}".format(
                                    toolinfo.title,
                                    dt)))
                            # Return instead of raise so transactions are
                            # committed
                            return shortcuts.redirect(history_url)
                    except DatabaseError:
                        logger.exception('ToolInfo.revert failed')
                        messages.error(
                            req,
                            _(
                                "Error updating database. [req id: {id}]"
                            ).format(id=req.id))
                        raise reversion.views._RollBackRevisionView(None)

            ctx = {
                'tool': tool,
                'toolinfo': toolinfo,
                'version': version,
                'can_revert': can_revert,
                'can_suppress': can_suppress,
            }
            resp = shortcuts.render(req, 'tools/info/revision.html', ctx)
            raise reversion.views._RollBackRevisionView(resp)
    except reversion.errors.RevertError:
        logger.exception('ToolInfo.revert failed')
        return shortcuts.redirect(history_url)

    except reversion.views._RollBackRevisionView as ex:
        if ex.response:
            return ex.response
        else:
            return shortcuts.redirect(history_url)


class TagAutocomplete(autocomplete.Select2QuerySetView):
    create_field = 'name'

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return ToolInfoTag.objects.none()
        qs = ToolInfoTag.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        qs.order_by('name')
        return qs

    def has_add_permission(self, request):
        return request.user.is_authenticated()

    def create_object(self, text):
        return ToolInfoTag.objects.create(name=text, slug=slugify(text))


class AuthorAutocomplete(autocomplete.Select2QuerySetView):
    create_field = 'name'

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Author.objects.none()
        qs = Author.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        qs.order_by('name')
        return qs

    def has_add_permission(self, request):
        return request.user.is_authenticated()

    def create_object(self, text):
        return Author.objects.create(name=text)


def json_v1(req):
    class PrettyPrintJSONEncoder(DjangoJSONEncoder):
        def __init__(self, *args, **kwargs):
            kwargs['indent'] = 2
            kwargs['separators'] = (',', ':')
            super(PrettyPrintJSONEncoder, self).__init__(*args, **kwargs)

    return JsonResponse(
        [
            info.toolinfo()
            for info in ToolInfo.objects.all().order_by('name')
        ],
        encoder=PrettyPrintJSONEncoder,
        safe=False,
    )
