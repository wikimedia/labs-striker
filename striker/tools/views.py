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
from django.contrib.auth.models import Group
from django.core import paginator
from django.core import urlresolvers
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import DatabaseError
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from notifications.signals import notify

from striker import mediawiki
from striker import openstack
from striker import phabricator
from striker.tools.forms import AccessRequestForm
from striker.tools.forms import AccessRequestAdminForm
from striker.tools.forms import RepoCreateForm
from striker.tools.models import AccessRequest
from striker.tools.models import DiffusionRepo
from striker.tools.models import Tool


WELCOME_MSG = "== Welcome to Tool Labs! ==\n{{subst:ToolsGranted}}"
WELCOME_SUMMARY = 'Welcome to Tool Labs!'

logger = logging.getLogger(__name__)
phab = phabricator.Client.default_client()
openstack = openstack.Client.default_client()


class HttpResponseSeeOther(HttpResponseRedirect):
    """HTTP redirect response with 303 status code"""
    status_code = 303


def see_other(to, *args, **kwargs):
    """Redirect to another page with 303 status code."""
    return HttpResponseSeeOther(shortcuts.resolve_url(to, *args, **kwargs))


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


def project_member(user):
    groups = user.groups.values_list('name', flat=True)
    return settings.TOOLS_TOOL_LABS_GROUP_NAME in groups


def index(req):
    ctx = {
        'my_tools': [],
        'query': req.GET.get('q', ''),
        'member': False,
    }
    if not req.user.is_anonymous():
        # TODO: do we need to paginate the user's tools too? Magnus has 60!
        ctx['my_tools'] = Tool.objects.filter(
            members__contains=req.user.ldap_dn).order_by('cn')
        ctx['member'] = project_member(req.user)

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
                    notify.send(
                        recipient=Group.objects.get(name=tool.cn),
                        sender=req.user,
                        verb=_('created'),
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


def membership(req):
    """Show access requests."""
    ctx = {
        'o': req.GET.get('o', '-created_date'),
        'cols': [
            {'field': 'created_date', 'label': 'Created'},
            {'field': 'user', 'label': 'User'},
            {'field': 'status', 'label': 'Status'},
        ],
    }
    if req.user.is_staff:
        all_requests = AccessRequest.objects.all()
    else:
        all_requests = AccessRequest.objects.filter(suppressed=False)
    all_requests = all_requests.order_by(ctx['o'])
    pager = paginator.Paginator(all_requests, 25)
    page = req.GET.get('p', 1)
    try:
        access_requests = pager.page(page)
    except paginator.PageNotAnInteger:
        access_requests = pager.page(1)
    except paginator.EmptyPage:
        access_requests = pager.page(pager.num_pages)
    ctx['access_requests'] = access_requests
    return shortcuts.render(req, 'tools/membership.html', ctx)


@login_required
def membership_apply(req):
    """Request membership in the Tools project."""
    if project_member(req.user):
        messages.error(
            req, _('You are already a member of Tool Labs'))
        return see_other(urlresolvers.reverse('tools:index'))

    pending = AccessRequest.objects.filter(
            user=req.user, status=AccessRequest.PENDING)
    if pending:
        return see_other(
            urlresolvers.reverse(
                'tools:membership_status', args=[pending[0].id]))

    form = AccessRequestForm(req.POST or None, req.FILES or None)
    if req.method == 'POST':
        if form.is_valid():
            try:
                request = form.save(commit=False)
                request.user = req.user
                request.save()
                notify.send(
                    recipient=Group.objects.get(name='tools.admin'),
                    sender=req.user,
                    verb=_('created'),
                    target=request,
                    public=False,
                    description=request.reason,
                    level='info',
                    actions=[
                        {
                            'title': _('View request'),
                            'href': request.get_absolute_url(),
                        },
                    ],
                )
                messages.info(
                    req, _("Tool Labs membership request submitted"))
                return shortcuts.redirect(urlresolvers.reverse('tools:index'))
            except DatabaseError:
                logger.exception('AccessRequest.save failed')
                messages.error(
                    req,
                    _("Error updating database. [req id: {id}]").format(
                        id=req.id))
    return shortcuts.render(req, 'tools/membership/apply.html', {'form': form})


def membership_status(req, app_id):
    """Show access request status and allow editing if authorized."""
    request = shortcuts.get_object_or_404(AccessRequest, pk=app_id)
    form = None
    as_admin = False
    if req.user == request.user and request.status == AccessRequest.PENDING:
        # An applicant can amend their own request while it is pending
        form = AccessRequestForm(
                req.POST or None, req.FILES or None, instance=request)
    elif req.user.is_staff:
        # TODO: guard condition will need changing if/when striker handles
        # more than tools
        as_admin = True
        form = AccessRequestAdminForm(
                req.POST or None, req.FILES or None, instance=request)

    if form is not None and req.method == 'POST':
        if form.is_valid() and form.has_changed():
            try:
                request = form.save(commit=False)
                if as_admin:
                    if request.status == AccessRequest.APPROVED:
                        openstack.grant_role(
                            settings.OPENSTACK_USER_ROLE,
                            request.user.shellname,
                        )
                        mwapi = mediawiki.Client.default_client()
                        talk = mwapi.user_talk_page(request.user.ldapname)
                        msg = '{}\n{}'.format(
                            talk.text(), WELCOME_MSG).strip()
                        talk.save(msg, summary=WELCOME_SUMMARY, bot=False)

                    if request.status != AccessRequest.PENDING:
                        request.resolved_by = req.user
                        request.resolved_date = timezone.now()
                    else:
                        request.resolved_by = None
                        request.resolved_date = None
                request.save()

                if as_admin:
                    recipient = request.user
                    verb = _('commented on')
                    description = request.admin_notes
                    level = 'info'
                    if request.status != AccessRequest.PENDING:
                        verb = request.get_status_display().lower()
                        if request.status == AccessRequest.APPROVED:
                            level = 'success'
                        else:
                            level = 'warning'
                else:
                    recipient = Group.objects.get(name='tools.admin')
                    verb = _('updated')
                    description = request.reason
                    level = 'info'

                notify.send(
                    recipient=recipient,
                    sender=req.user,
                    verb=verb,
                    target=request,
                    public=False,
                    description=description,
                    level=level,
                    actions=[
                        {
                            'title': _('View request'),
                            'href': request.get_absolute_url(),
                        },
                    ],
                )

                messages.info(
                    req, _("Tool Labs membership request updated"))
                return shortcuts.redirect(
                    urlresolvers.reverse(
                        'tools:membership_status', args=[request.id]))
            except DatabaseError:
                logger.exception('AccessRequest.save failed')
                messages.error(
                    req,
                    _("Error updating database. [req id: {id}]").format(
                        id=req.id))
    ctx = {
        'app': request,
        'form': form,
        'wikitech': settings.WIKITECH_URL,
        'meta': settings.OAUTH_MWURL,
    }
    return shortcuts.render(req, 'tools/membership/status.html', ctx)
