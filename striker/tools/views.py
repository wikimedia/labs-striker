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
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.utils import DatabaseError
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from dal import autocomplete
from notifications.signals import notify
import reversion
import reversion.models
import reversion_compare.views

from striker import mediawiki
from striker import openstack
from striker import phabricator
from striker.labsauth.models import LabsUser
from striker.tools import cache
from striker.tools import utils
from striker.tools.forms import AccessRequestAdminForm
from striker.tools.forms import AccessRequestForm
from striker.tools.forms import MantainersForm
from striker.tools.forms import RepoCreateForm
from striker.tools.forms import ToolCreateForm
from striker.tools.forms import ToolInfoForm
from striker.tools.forms import ToolInfoPublicForm
from striker.tools.models import AccessRequest
from striker.tools.models import DiffusionRepo
from striker.tools.models import Maintainer
from striker.tools.models import Tool
from striker.tools.models import ToolInfo
from striker.tools.models import ToolInfoTag
from striker.tools.models import ToolUser


WELCOME_MSG = "== Welcome to Toolforge! ==\n{{subst:ToolsGranted}}"
WELCOME_SUMMARY = 'Welcome to Toolforge!'

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


def member_or_admin(tool, user):
    """Is the given user a member of the given tool or a global admin?"""
    if user.is_anonymous():
        return False
    if user.ldap_dn in tool.members:
        return True
    return user.ldap_dn in Tool.objects.get(cn='tools.admin').members


def project_member(user):
    groups = user.groups.values_list('name', flat=True)
    return settings.TOOLS_TOOL_LABS_GROUP_NAME in groups


def require_tools_member(f):
    """Ensure that the active user is a member of the tools project."""
    @functools.wraps(f)
    def decorated(request, *args, **kwargs):
        if project_member(request.user):
            return f(request, *args, **kwargs)
        raise PermissionDenied
    return decorated


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
        'toolinfo': tool.toolinfo(),
        'repos': DiffusionRepo.objects.filter(tool=tool.name),
        'can_edit': member_or_admin(tool, req.user),
    })


@reversion.views.create_revision()
@login_required
@inject_tool
def info_create(req, tool):
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
            except DatabaseError:
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
def info_read(req, tool, info_id):
    """View a ToolInfo record."""
    toolinfo = shortcuts.get_object_or_404(ToolInfo, pk=info_id, tool=tool)
    ctx = {
        'tool': tool,
        'toolinfo': toolinfo,
    }
    return shortcuts.render(req, 'tools/info/read.html', ctx)


@reversion.views.create_revision()
@login_required
@inject_tool
def info_edit(req, tool, info_id):
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


class ToolInfoHistoryView(reversion_compare.views.HistoryCompareDetailView):
    model = ToolInfo
    pk_url_kwarg = 'info_id'
    template_name = 'tools/info/history.html'

    def get_queryset(self):
        qs = super(ToolInfoHistoryView, self).get_queryset()
        return qs.filter(tool=self.kwargs['tool'])

    def _get_action_list(self):
        actions = super(ToolInfoHistoryView, self)._get_action_list()
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

        ctx = super(ToolInfoHistoryView, self).get_context_data(**kwargs)
        ctx['toolinfo'] = kwargs['object']
        ctx['tool'] = tool
        ctx['show_suppressed'] = member_or_admin(tool, user)
        return ctx


@inject_tool
def info_revision(req, tool, info_id, version_id):
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


@login_required
@inject_tool
def repo_create(req, tool):
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
            req, _('You are already a member of Toolforge'))
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
                    req, _("Toolforge membership request submitted"))
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
                        cache.purge_openstack_users()

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
                    req, _("Toolforge membership request updated"))
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


class ToolInfoTagAutocomplete(autocomplete.Select2QuerySetView):
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


def toolinfo(req):
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


@require_tools_member
@login_required
def tool_create(req):
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
                        toolinfo.authors.add(req.user)
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
    form = MantainersForm(req.POST or None, req.FILES or None, tool=tool)
    if req.method == 'POST':
        if form.is_valid():
            old_members = set(tool.members)
            new_members = set(
                m.dn for m in itertools.chain(
                    form.cleaned_data['maintainers'],
                    form.cleaned_data['tools']
                )
            )
            tool.members = new_members
            tool.save()

            maintainers, created = Group.objects.get_or_create(name=tool.cn)
            added_maintainers = list(new_members - old_members)
            removed_maintainers = list(old_members - new_members)
            for dn in added_maintainers:
                uid = dn.split(',')[0][4:]
                logging.info('Added %s', uid)
                try:
                    added = LabsUser.objects.get(shellname=uid)
                except ObjectDoesNotExist:
                    # No local user for this account
                    logging.info('No LabsUser found for %s', uid)
                    pass
                else:
                    # Add user to the mirrored group
                    added.groups.add(maintainers.id)
                    # Do not set tool as the notification target because the
                    # framework does not understand LDAP models.
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
                logging.info('Removed %s', uid)
                try:
                    removed = LabsUser.objects.get(shellname=uid)
                except ObjectDoesNotExist:
                    # No local user for this account
                    logging.info('No LabsUser found for %s', uid)
                    pass
                else:
                    # Add user to the mirrored group
                    removed.groups.remove(maintainers.id)
                    # Do not set tool as the notification target because the
                    # framework does not understand LDAP models.
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
        if not self.request.user.is_authenticated():
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
        if not self.request.user.is_authenticated():
            return ToolUser.objects.none()
        qs = ToolUser.objects.all()
        if self.q:
            qs = qs.filter(uid__icontains=self.q)
        qs.order_by('uid')
        return qs

    def get_result_label(self, result):
        return result.name
