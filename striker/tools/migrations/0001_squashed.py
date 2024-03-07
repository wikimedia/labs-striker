# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import ldapdb.models.fields
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    replaces = [("tools", "0001_initial"), ("tools", "0002_auto_20160531_1653")]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DiffusionRepo",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("tool", models.CharField(max_length=255)),
                ("name", models.CharField(max_length=255)),
                ("phid", models.CharField(max_length=255)),
                (
                    "created_by",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        on_delete=models.SET_NULL,
                    ),
                ),
                (
                    "created_date",
                    models.DateTimeField(
                        default=timezone.now, editable=False, blank=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Maintainer",
            fields=[
                (
                    "dn",
                    models.CharField(primary_key=True, serialize=False, max_length=200),
                ),
                (
                    "uid",
                    ldapdb.models.fields.CharField(
                        max_length=200, unique=True, db_column="uid"
                    ),
                ),
                ("cn", ldapdb.models.fields.CharField(max_length=200, db_column="cn")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Tool",
            fields=[
                (
                    "dn",
                    models.CharField(primary_key=True, serialize=False, max_length=200),
                ),
                (
                    "cn",
                    ldapdb.models.fields.CharField(
                        max_length=200, unique=True, db_column="cn"
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
                "abstract": False,
            },
        ),
    ]
