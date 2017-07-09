# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ldapdb.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0007_toolinfo_tags'),
    ]

    operations = [
        migrations.CreateModel(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name='SudoRole',
            fields=[
                ('dn', models.CharField(primary_key=True, serialize=False, max_length=200)),
                ('cn', ldapdb.models.fields.CharField(primary_key=True, db_column='cn', serialize=False, max_length=200)),
                ('users', ldapdb.models.fields.ListField(db_column='sudoUser')),
                ('hosts', ldapdb.models.fields.ListField(db_column='sudoHost')),
                ('commands', ldapdb.models.fields.ListField(db_column='sudoCommand')),
                ('options', ldapdb.models.fields.ListField(db_column='sudoOption')),
                ('runas_users', ldapdb.models.fields.ListField(db_column='sudoRunAsUser')),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name='ToolUser',
            fields=[
                ('dn', models.CharField(primary_key=True, serialize=False, max_length=200)),
                ('uid', ldapdb.models.fields.CharField(primary_key=True, db_column='uid', serialize=False, max_length=200)),
                ('cn', ldapdb.models.fields.CharField(db_column='cn', unique=True, max_length=200)),
                ('sn', ldapdb.models.fields.CharField(db_column='sn', unique=True, max_length=200)),
                ('uid_number', ldapdb.models.fields.IntegerField(db_column='uidNumber', unique=True)),
                ('gid_number', ldapdb.models.fields.IntegerField(db_column='gidNumber')),
                ('home_directory', ldapdb.models.fields.CharField(db_column='homeDirectory', max_length=200)),
                ('login_shell', ldapdb.models.fields.CharField(db_column='loginShell', max_length=64)),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.AlterModelOptions(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name='maintainer',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            # Unmanaged model. This won't actually apply when you run the
            # migration. There's no way to convince Django not to generate
            # these migrations in the first place.
            name='tool',
            options={'managed': False},
        ),
    ]
