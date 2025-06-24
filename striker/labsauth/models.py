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

import ldap
import ldapdb.models
import mwoauth
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.crypto import salted_hmac
from django.utils.translation import gettext_lazy as _
from django_auth_ldap.backend import LDAPBackend
from ldapdb.models import fields as ldap_fields


class LabsUserManager(BaseUserManager):
    def create_user(self, username, **extra_fields):
        if not username:
            raise ValueError("Users must have a valid username.")
        user = self.model(ldapname=username, **extra_fields)
        user.save()
        return user

    def create_superuser(self, username, **extra_fields):
        return self.create_user(username, is_superuser=True, **extra_fields)

    def create_from_ldap_user(self, ldap_user, **extra_fields):
        return self.create_user(
            ldap_user.cn,
            ldapemail=ldap_user.mail,
            shellname=ldap_user.uid,
            **extra_fields
        )


def make_authhash():
    """Make a random string."""
    return "".join(random.SystemRandom().choice(string.printable) for _ in range(128))


class LabsUser(AbstractBaseUser, PermissionsMixin):
    """Custom user class that is a better match for a Wikimedia account."""

    ldapname = models.CharField(
        _("Developer account username"), max_length=255, unique=True
    )
    ldapemail = models.EmailField(_("Developer account email address"), blank=True)
    shellname = models.CharField(
        _("shellname"), max_length=32, unique=True, blank=True, null=True
    )

    sulid = models.BigIntegerField(_("SUL user ID"), unique=True, blank=True, null=True)
    sulname = models.CharField(
        _("SUL username"), max_length=255, unique=True, blank=True, null=True
    )
    sulemail = models.EmailField(_("SUL email address"), blank=True, null=True)
    oauthtoken = models.CharField(
        _("OAuth token"), max_length=127, blank=True, null=True
    )
    oauthsecret = models.CharField(
        _("OAuth secret"), max_length=127, blank=True, null=True
    )

    phabname = models.CharField(
        _("Phabricator username"), max_length=255, unique=True, blank=True, null=True
    )
    phid = models.CharField(_("phid"), max_length=255, blank=True, null=True)
    phabrealname = models.CharField(
        _("Phabricator real name"), max_length=255, blank=True, null=True
    )
    phaburl = models.CharField(
        _("Phabricator url"), max_length=255, blank=True, null=True
    )
    phabimage = models.CharField(_("image"), max_length=255, blank=True, null=True)

    authhash = models.CharField(
        _("authhash"), max_length=128, editable=False, default=make_authhash
    )

    is_staff = models.BooleanField(_("staff status"), default=False)
    is_active = models.BooleanField(_("active"), default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LabsUserManager()

    USERNAME_FIELD = "ldapname"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def set_password(self, raw_password):
        # Set password by directly manipulating the associated LDAP record.
        # The ldap-auth backend we use does not support password
        # checks/changes.
        ldapuser = self.ldapuser
        ldapuser.password = raw_password
        ldapuser.save()

    def check_password(self, raw_password):
        """Return a boolean of whether the raw_password was correct."""
        # Validate the current password by doing an authbind as the user.
        # The ldap-auth backend we use does not support password
        # checks/changes.
        try:
            con = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
            if settings.AUTH_LDAP_START_TLS:
                con.start_tls_s()
            con.simple_bind_s(self.ldap_dn, raw_password)
        except ldap.INVALID_CREDENTIALS:
            return False
        else:
            con.unbind()
            return True

    def set_unusable_password(self):
        return

    def has_usable_password(self):
        return False

    def get_full_name(self):
        return self.phabrealname or self.sulname or self.ldapname

    def get_short_name(self):
        return self.sulname or self.ldapname

    def get_session_auth_hash(self):
        return salted_hmac(LabsUser.__name__, self.authhash).hexdigest()

    def set_accesstoken(self, token):
        self.oauthtoken = token.key
        self.oauthsecret = token.secret

    def get_accesstoken(self):
        return mwoauth.AccessToken(self.oauthtoken, self.oauthsecret)

    def refresh_from_ldap(self):
        ldap_backend = LDAPBackend()
        ldap_backend.populate_user(self.ldapname)

    @property
    def ldap_dn(self):
        return "uid={0},{1}".format(self.shellname, settings.LABSAUTH_USER_BASE)

    @property
    def ldapuser(self):
        return LdapUser.objects.get(dn=self.ldap_dn)


class PosixGroup(ldapdb.models.Model):
    base_dn = settings.LABSAUTH_GROUP_BASE
    object_classes = ["posixGroup"]

    cn = ldap_fields.CharField(db_column="cn", primary_key=True)
    gid_number = ldap_fields.IntegerField(db_column="gidNumber", unique=True)
    members = ldap_fields.ListField(db_column="member")

    class Meta:
        managed = False

    def __str__(self):
        return "cn=%s,%s" % (self.cn, self.base_dn)


class PosixAccount(ldapdb.models.Model):
    base_dn = settings.LABSAUTH_USER_BASE
    object_classes = ["posixAccount"]

    uid = ldap_fields.CharField(db_column="uid", primary_key=True)
    cn = ldap_fields.CharField(db_column="cn", unique=True)
    uid_number = ldap_fields.IntegerField(db_column="uidNumber", unique=True)
    gid_number = ldap_fields.IntegerField(db_column="gidNumber")
    home_directory = ldap_fields.CharField(db_column="homeDirectory", max_length=200)

    class Meta:
        managed = False

    def __str__(self):
        return "uid=%s,%s" % (self.uid, self.base_dn)


class LdapUser(ldapdb.models.Model):
    """Equivalent of OpenStackNovaUser"""

    base_dn = settings.LABSAUTH_USER_BASE
    object_classes = [
        "person",
        "inetOrgPerson",
        "ldapPublicKey",
        "posixAccount",
    ]

    # posixAccount
    uid = ldap_fields.CharField(db_column="uid", primary_key=True)
    cn = ldap_fields.CharField(db_column="cn", unique=True)
    uid_number = ldap_fields.IntegerField(db_column="uidNumber", unique=True)
    gid_number = ldap_fields.IntegerField(db_column="gidNumber")
    home_dir = ldap_fields.CharField(db_column="homeDirectory")
    login_shell = ldap_fields.CharField(db_column="loginShell")
    password = ldap_fields.CharField(db_column="userPassword")
    # person
    sn = ldap_fields.CharField(db_column="sn", unique=True)
    # inetOrgPerson
    mail = ldap_fields.CharField(db_column="mail")
    # ldapPublicKey
    ssh_keys = ldap_fields.ListField(db_column="sshPublicKey")

    class Meta:
        managed = False

    def __str__(self):
        return "uid=%s,%s" % (self.uid, self.base_dn)
