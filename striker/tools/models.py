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

import collections
import datetime
import logging

from django import urls
from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ldapdb.models import fields
import ldapdb.models
import reversion

from striker import gitlab
from striker import phabricator
from striker.tools import cache


# Inspiration from https://stackoverflow.com/a/24668215/8171
#
# Add a 'suppressed' field to the reversion Version model.
# This this will be used to allow suppression of malicious changes by an
# admin.
reversion.models.Version.add_to_class(
    'suppressed',
    models.BooleanField(blank=True, default=False, db_index=True)
)


logger = logging.getLogger(__name__)
gitlab_client = gitlab.Client.default_client()
phab = phabricator.Client.default_client()


class MaintainerManager(models.Manager):
    def _get_tool_users(self):
        if settings.TEST_MODE:
            # Hack to keep from trying to talk to openstack API from django
            # test harness
            return []
        users = cache.get_openstack_users()
        return (
            users[settings.OPENSTACK_USER_ROLE] +
            users[settings.OPENSTACK_ADMIN_ROLE]
        )

    def get_queryset(self):
        return super(MaintainerManager, self).get_queryset().filter(
            uid__in=self._get_tool_users()).order_by('cn')


class Maintainer(ldapdb.models.Model):
    """A tool maintainer."""
    base_dn = settings.TOOLS_MAINTAINER_BASE_DN
    object_classes = ['inetOrgPerson', 'posixAccount']

    uid = fields.CharField(db_column='uid', primary_key=True)
    cn = fields.CharField(db_column='cn')
    mail = fields.CharField(db_column='mail')

    objects = MaintainerManager()

    class Meta:
        managed = False

    def __str__(self):
        return self.cn


class ToolManager(models.Manager):
    def get_queryset(self):
        return super(ToolManager, self).get_queryset().filter(
            cn__startswith='{0}.'.format(settings.OPENSTACK_PROJECT))


class Tool(ldapdb.models.Model):
    """A tool is a specially named LDAP group."""
    base_dn = settings.TOOLS_TOOL_BASE_DN
    object_classes = ['posixGroup', 'groupOfNames']

    objects = ToolManager()

    cn = fields.CharField(db_column='cn', max_length=200, primary_key=True)
    gid_number = fields.IntegerField(db_column='gidNumber', unique=True)
    members = fields.ListField(db_column='member')

    class Meta:
        managed = False

    @property
    def name(self):
        return self.cn[len(settings.OPENSTACK_PROJECT) + 1:]

    @name.setter
    def name(self, value):
        self.cn = '{0}.{1!s}'.format(settings.OPENSTACK_PROJECT, value)

    def maintainer_ids(self):
        return [
            dn.split(',')[0].split('=')[1]
            for dn in self.members
            if not dn.startswith('uid={0}.'.format(settings.OPENSTACK_PROJECT))
        ]

    def maintainers(self):
        return Maintainer.objects.filter(uid__in=self.maintainer_ids())

    def tool_member_ids(self):
        return [
            dn.split(',')[0].split('=')[1]
            for dn in self.members
            if dn.startswith('uid={0}.'.format(settings.OPENSTACK_PROJECT))
        ]

    def tool_members(self):
        return ToolUser.objects.filter(uid__in=self.tool_member_ids())

    def toolinfo(self):
        try:
            return ToolInfo.objects.filter(tool=self.name)
        except ToolInfo.DoesNotExist:
            return None

    def service_user(self):
        return ToolUser.objects.get(uid=self.cn)

    def disable(self, delete=False):
        """Mark this tool as disabled."""
        return self.service_user().disable(delete=delete)

    def enable(self):
        """Mark this tool as enabled."""
        return self.service_user().enable()

    def is_disabled(self):
        """Has this tool been marked as disabled?"""
        return self.service_user().is_disabled()

    def get_absolute_url(self):
        return urls.reverse(
            'tools:tool', args=[str(self.name)])

    def __str__(self):
        return self.name


class ToolUser(ldapdb.models.Model):
    """Posix account that a tool runs as."""
    base_dn = 'ou=people,{}'.format(settings.TOOLS_TOOL_BASE_DN)
    object_classes = [
        'shadowAccount',
        'posixAccount',
        'person',
        'top'
    ]

    uid = fields.CharField(db_column='uid', primary_key=True)
    cn = fields.CharField(db_column='cn', unique=True)
    sn = fields.CharField(db_column='sn', unique=True)
    uid_number = fields.IntegerField(db_column='uidNumber', unique=True)
    gid_number = fields.IntegerField(db_column='gidNumber')
    home_directory = fields.CharField(
        db_column='homeDirectory', max_length=200)
    login_shell = fields.CharField(db_column='loginShell', max_length=64)
    locked_time = fields.DateTimeField(db_column='pwdAccountLockedTime')
    password_policy = fields.CharField(db_column='pwdPolicySubentry')

    class Meta:
        managed = False

    @property
    def name(self):
        return self.cn[len(settings.OPENSTACK_PROJECT) + 1:]

    @name.setter
    def name(self, value):
        self.cn = '{0}.{1!s}'.format(settings.OPENSTACK_PROJECT, value)

    def disable(self, delete=False):
        """Mark this tool as disabled."""
        self.login_shell = "/bin/disabledtoolshell"
        self.password_policy = settings.TOOLS_DISABLED_POLICY_ENTRY
        if delete:
            self.locked_time = "000001010000Z"
        else:
            self.locked_time = datetime.datetime.now()
        self.save()

    def enable(self):
        """Mark this tool as enabled."""
        self.login_shell = "/bin/bash"
        self.password_policy = None
        self.locked_time = None
        self.save()

    def is_disabled(self):
        """Has this tool been marked as disabled?"""
        return self.password_policy == settings.TOOLS_DISABLED_POLICY_ENTRY

    def __str__(self):
        return self.name


class SudoRole(ldapdb.models.Model):
    base_dn = 'ou=sudoers,cn=tools,{}'.format(settings.PROJECTS_BASE_DN)
    object_classes = ['sudoRole']

    cn = fields.CharField(db_column='cn', primary_key=True)
    users = fields.ListField(db_column='sudoUser')
    hosts = fields.ListField(db_column='sudoHost')
    commands = fields.ListField(db_column='sudoCommand')
    options = fields.ListField(db_column='sudoOption')
    runas_users = fields.ListField(db_column='sudoRunAsUser')

    class Meta:
        managed = False

    def __str__(self):
        return 'cn=%s,%s' % (self.cn, self.base_dn)


class PhabricatorProject(models.Model):
    """Associate phabricator projects with Tools."""
    tool = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    phid = models.CharField(max_length=64)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return urls.reverse(
            'tools:project_view', args=[self.tool, self.name])


class DiffusionRepo(models.Model):
    """Associate diffusion repos with Tools."""
    tool = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    phid = models.CharField(max_length=64)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)
    # Track migration to GitLab
    gitlab = models.ForeignKey(
        "GitlabRepo",
        null=True,
        on_delete=models.SET_NULL,
        related_name="diffusion",
    )
    is_mirror = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def convert_to_mirror(self):
        """Convert this repo into a mirror of an associated gitlab repo."""
        if not self.gitlab:
            logger.warning(
                "Diffusion repo %s has no GitLab sibling to mirror.",
                self.name,
            )
            return False

        if not self.gitlab.import_finished:
            logger.info(
                "Diffusion repo %s still pennding import in GitLab.",
                self.name,
            )
            return False

        gl_repo = gitlab_client.get_repository_by_id(self.gitlab.repo_id)
        phab.repository_mirror(self.phid, gl_repo["http_url_to_repo"])
        logger.info(
            "Diffusion repo %s set to mirror %s",
            self.name,
            gl_repo["http_url_to_repo"],
        )

        self.is_mirror = True
        self.save()
        return True


class GitlabRepo(models.Model):
    """Associate GitLab repos with Tools."""
    tool = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    repo_id = models.PositiveIntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_date = models.DateTimeField(
        default=timezone.now, blank=True, editable=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return urls.reverse(
            'tools:repo_view',
            kwargs={
                'tool': self.tool,
                'repo_id': self.repo_id,
            }
        )

    def _tool(self):
        return Tool.objects.get(cn="{0}.{1}".format(
            settings.OPENSTACK_PROJECT,
            self.tool,
        ))

    @classmethod
    def create_from_diffusion(cls, diff_repo):
        """Create a new GitlabRepo based on the given DiffusionRepo."""
        gl_name = diff_repo.name
        if gl_name.startswith("tool-"):
            gl_name = gl_name[5:]

        old_repo = phab.get_repository_by_phid(diff_repo.phid)

        # Find the first https URL for the diffusion repo.
        src_url = next(iter([
            u['fields']['uri']['display'] for u in
            old_repo['attachments']['uris']['uris']
            if u['fields']['display']['effective'] == 'always'
            and u['fields']['uri']['display'].startswith('https')
        ]), None)

        # Create a new gitlab repo, no owners yet, clone from src_url
        new_repo = gitlab_client.create_repository(gl_name, [], src_url)

        with transaction.atomic():
            gl_repo = GitlabRepo(
                tool=diff_repo.tool,
                name=gl_name,
                repo_id=new_repo['id'],
                created_by=diff_repo.created_by,
            )
            gl_repo.sync_maintainers_with_gitlab(True)
            gl_repo.save()

            diff_repo.gitlab = gl_repo
            diff_repo.save()
        return gl_repo

    def sync_maintainers_with_gitlab(self, invite_missing=False):
        """Ensure that all maintainers have access to the repo."""
        maintainer_ids = self._tool().maintainer_ids()
        if invite_missing:
            gitlab_maintainers = gitlab_client.user_lookup(maintainer_ids)
            missing = Maintainer.objects.filter(
                uid__in=list(
                    set(maintainer_ids) - set(gitlab_maintainers.keys())
                )
            )
            for user in missing:
                gitlab_client.invite_user(self.repo_id, user)
        try:
            gitlab_client.set_repository_owners(self.repo_id, maintainer_ids)

        except gitlab.APIError:
            logger.exception(
                "Failure updating repo ownership for tool=%s, repo=%s",
                self.tool,
                self.name,
            )

    @property
    def import_finished(self):
        """Check on this repo's import status."""
        r = gitlab_client.import_status(self.repo_id)
        status = r["import_status"]
        if status not in ["none", "finished"]:
            logger.info("[Repo %s] import status: %s", self.name, status)
            for err in r["failed_relations"]:
                logger.error(
                    "[Repo %s] %s: %s %s",
                    self.name,
                    err["relation_name"],
                    err["exception_class"],
                    err["exception_message"],
                )
            return False
        return True


class AccessRequest(models.Model):
    """Request to join Tools project."""
    PENDING = 'p'
    FEEDBACK = 'f'
    APPROVED = 'a'
    DECLINED = 'd'
    STATUS_CHOICES = (
        (PENDING, _('Pending')),
        (FEEDBACK, _('Feedback needed')),
        (APPROVED, _('Approved')),
        (DECLINED, _('Declined')),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='requestor+', db_index=True,
        on_delete=models.CASCADE)
    reason = models.TextField()
    created_date = models.DateTimeField(
        default=timezone.now, blank=True, editable=False, db_index=True)
    admin_notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='resolver+',
        blank=True, null=True, on_delete=models.SET_NULL)
    resolved_date = models.DateTimeField(blank=True, null=True)
    suppressed = models.BooleanField(blank=True, default=False, db_index=True)

    def __str__(self):
        return _('Access request {id}').format(id=self.id)

    def get_absolute_url(self):
        return urls.reverse(
            'tools:membership_status', args=[str(self.id)])

    def closed(self):
        return self.status in [AccessRequest.APPROVED, AccessRequest.DECLINED]

    def open(self):
        return not self.closed()


class AccessRequestComment(models.Model):
    request = models.ForeignKey(
        AccessRequest,
        related_name='comments', db_index=True, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.CASCADE)
    created_date = models.DateTimeField(
        default=timezone.now, blank=True, editable=False, db_index=True)
    comment = models.TextField()

    class Meta:
        ordering = ('created_date', 'user',)

    def __str__(self):
        return '{} --{} {:%Y-%m-%dT%H:%MZ}'.format(
            self.comment, self.user.ldapname, self.created_date)


class SoftwareLicense(models.Model):
    """Describe a software license."""
    slug = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=2047)
    family = models.CharField(max_length=32, db_index=True)
    osi_approved = models.BooleanField()
    recommended = models.BooleanField()

    def __str__(self):
        return "{} - {}".format(self.slug, self.name)


class ToolInfoTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Author(models.Model):
    """Describe an author."""
    name = models.CharField(max_length=128, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('name',)


@reversion.register()
class ToolInfo(models.Model):
    """Metadata about a Tool hosted on Toolforge.

    A single Tool may have 1-to-N metadata records.
    """
    name = models.CharField(max_length=255, unique=True)
    tool = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    license = models.ForeignKey(SoftwareLicense, on_delete=models.PROTECT)
    authors = models.ManyToManyField(Author, related_name='+')
    tags = models.ManyToManyField(ToolInfoTag, blank=True)
    repository = models.CharField(max_length=2047, blank=True, null=True)
    issues = models.CharField(max_length=2047, blank=True, null=True)
    docs = models.CharField(max_length=2047, blank=True, null=True)
    is_webservice = models.BooleanField()
    suburl = models.CharField(max_length=2047, blank=True, null=True)

    class Meta:
        verbose_name = 'Toolinfo'
        verbose_name_plural = 'Toolinfo'

    def __str__(self):
        return self.name

    def get_tool(self):
        try:
            return Tool.objects.get(cn="{0}.{1}".format(
                settings.OPENSTACK_PROJECT,
                self.tool,
            ))
        except Tool.DoesNotExist:
            return None

    def toolinfo_v1(self, request):
        if self.is_webservice:
            url = 'https://{}.toolforge.org/{}'.format(
                self.tool,
                self.suburl or ''
            )
        else:
            url = self.docs
            if not url:
                url = request.build_absolute_uri(
                    urls.reverse('tools:tool', args=[str(self.tool)])
                )

        return collections.OrderedDict([
            ('name', self.name),
            ('title', self.title),
            ('description', self.description),
            ('url', url),
            ('keywords', ", ".join(tag.name for tag in self.tags.all())),
            ('author', ", ".join(a.name for a in self.authors.all())),
            ('repository', self.repository),
        ])

    def toolinfo_v1_2(self, request):
        info = self.toolinfo_v1(request)

        # FIXME: more complete author is possible, but requires fetching
        # maintainers from LDAP which was too slow the last time it was tried
        # at production scale.
        info["author"] = [{"name": a.name} for a in self.authors.all()]

        info["license"] = self.license.slug
        info["technology_used"] = ["Toolforge"]
        if self.is_webservice:
            info["tool_type"] = "web app"
        if self.issues:
            info["bugtracker_url"] = self.issues
        if self.docs:
            info["developer_docs_url"] = {
                "url": self.docs,
                "language": "en",  # FIXME: allow user to specify lang
            }
        info["_schema"] = "/toolinfo/1.2.2"
        return info
