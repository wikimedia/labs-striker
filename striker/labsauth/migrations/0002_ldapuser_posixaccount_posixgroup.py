# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ldapdb.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("labsauth", "0001_squashed"),
    ]

    operations = [
        migrations.CreateModel(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name="LdapUser",
            fields=[
                ("dn", models.CharField(max_length=200)),
                (
                    "uid",
                    ldapdb.models.fields.CharField(
                        primary_key=True,
                        serialize=False,
                        db_column="uid",
                        max_length=200,
                    ),
                ),
                (
                    "cn",
                    ldapdb.models.fields.CharField(
                        unique=True, db_column="cn", max_length=200
                    ),
                ),
                (
                    "uid_number",
                    ldapdb.models.fields.IntegerField(
                        unique=True, db_column="uidNumber"
                    ),
                ),
                (
                    "gid_number",
                    ldapdb.models.fields.IntegerField(db_column="gidNumber"),
                ),
                (
                    "home_dir",
                    ldapdb.models.fields.CharField(
                        db_column="homeDirectory", max_length=200
                    ),
                ),
                (
                    "login_shell",
                    ldapdb.models.fields.CharField(
                        db_column="loginShell", max_length=200
                    ),
                ),
                (
                    "password",
                    ldapdb.models.fields.CharField(
                        db_column="userPassword", max_length=200
                    ),
                ),
                (
                    "sn",
                    ldapdb.models.fields.CharField(
                        unique=True, db_column="sn", max_length=200
                    ),
                ),
                (
                    "mail",
                    ldapdb.models.fields.CharField(db_column="mail", max_length=200),
                ),
                ("ssh_keys", ldapdb.models.fields.ListField(db_column="sshPublicKey")),
            ],
            options={
                "managed": False,
            },
        ),
        migrations.CreateModel(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name="PosixAccount",
            fields=[
                ("dn", models.CharField(max_length=200)),
                (
                    "uid",
                    ldapdb.models.fields.CharField(
                        primary_key=True,
                        serialize=False,
                        db_column="uid",
                        max_length=200,
                    ),
                ),
                (
                    "cn",
                    ldapdb.models.fields.CharField(
                        unique=True, db_column="cn", max_length=200
                    ),
                ),
                (
                    "uid_number",
                    ldapdb.models.fields.IntegerField(
                        unique=True, db_column="uidNumber"
                    ),
                ),
                (
                    "gid_number",
                    ldapdb.models.fields.IntegerField(db_column="gidNumber"),
                ),
                (
                    "home_directory",
                    ldapdb.models.fields.CharField(
                        db_column="homeDirectory", max_length=200
                    ),
                ),
            ],
            options={
                "managed": False,
            },
        ),
        migrations.CreateModel(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name="PosixGroup",
            fields=[
                ("dn", models.CharField(max_length=200)),
                (
                    "cn",
                    ldapdb.models.fields.CharField(
                        primary_key=True,
                        serialize=False,
                        db_column="cn",
                        max_length=200,
                    ),
                ),
                (
                    "gid_number",
                    ldapdb.models.fields.IntegerField(
                        unique=True, db_column="gidNumber"
                    ),
                ),
                ("members", ldapdb.models.fields.ListField(db_column="member")),
            ],
            options={
                "managed": False,
            },
        ),
    ]
