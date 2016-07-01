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

import random
import string

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.crypto import salted_hmac
from django.utils.translation import ugettext_lazy as _
import mwoauth


class LabsUserManager(BaseUserManager):
    def create_user(self, username, **extra_fields):
        if not username:
            raise ValueError('Users must have a valid username.')
        user = self.model(username, **extra_fields)
        user.save()
        return user

    def create_superuser(self, username, **extra_fields):
        return self.create_user(username, is_superuser=True, **extra_fields)


def make_authhash():
    """Make a random string."""
    return ''.join(
        random.SystemRandom().choice(string.printable) for _ in range(128))


class LabsUser(AbstractBaseUser, PermissionsMixin):
    """Custom user class that is a better match for a Wikimedia account."""
    ldapname = models.CharField(
        _('LDAP username'), max_length=255, unique=True)
    ldapemail = models.EmailField(_('LDAP email address'), blank=True)
    shellname = models.CharField(
        _('shellname'), max_length=32, unique=True, blank=True, null=True)

    sulname = models.CharField(
        _('SUL username'), max_length=255, unique=True, blank=True, null=True)
    sulemail = models.EmailField(_('SUL email address'), blank=True, null=True)
    realname = models.CharField(
        _('real name'), max_length=255, blank=True, null=True)
    oauthtoken = models.CharField(
            _('OAuth token'), max_length=127, blank=True, null=True)
    oauthsecret = models.CharField(
            _('OAuth secret'), max_length=127, blank=True, null=True)

    phabname = models.CharField(
        _('Phabricator username'), max_length=255, unique=True,
        blank=True, null=True)
    phid = models.CharField(
        _('phid'), max_length=255, blank=True, null=True)
    phabrealname = models.CharField(
        _('Phabricator real name'), max_length=255, blank=True, null=True)
    phaburl = models.CharField(
        _('Phabricator url'), max_length=255, blank=True, null=True)
    phabimage = models.CharField(
        _('image'), max_length=255, blank=True, null=True)

    authhash = models.CharField(
        _('authhash'), max_length=128, editable=False, default=make_authhash)

    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LabsUserManager()

    USERNAME_FIELD = 'ldapname'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def set_password(self, raw_password):
        """Can't change password."""
        return

    def check_password(self, raw_password):
        """Can't be used directly for authn."""
        return False

    def set_unusable_password(self):
        return

    def has_usable_password(self):
        return False

    def get_full_name(self):
        return (self.realname or
                self.phabrealname or
                self.sulname or
                self.ldapname)

    def get_short_name(self):
        return self.sulname or self.ldapname

    def get_session_auth_hash(self):
        return salted_hmac(LabsUser.__name__, self.authhash).hexdigest()

    def set_accesstoken(self, token):
        self.oauthtoken = token.key.decode('utf-8')
        self.oauthsecret = token.secret.decode('utf-8')

    def get_accesstoken(self):
        return mwoauth.AccessToken(
            self.oauthtoken.encode('utf-8'), self.oauthsecret.encode('utf-8'))

    @property
    def ldap_dn(self):
        # DN template uses legacy ('%') style string formatting
        dn = settings.AUTH_LDAP_USER_DN_TEMPLATE % {'user': self.ldapname}
        return dn
