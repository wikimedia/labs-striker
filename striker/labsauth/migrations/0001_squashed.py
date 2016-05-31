# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import striker.labsauth.models


class Migration(migrations.Migration):

    replaces = [(b'labsauth', '0001_initial'), (b'labsauth', '0002_auto_20160508_0419')]

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabsUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('ldapname', models.CharField(unique=True, max_length=255, verbose_name='LDAP username')),
                ('ldapemail', models.EmailField(max_length=254, verbose_name='LDAP email address', blank=True)),
                ('shellname', models.CharField(max_length=32, unique=True, null=True, verbose_name='shellname', blank=True)),
                ('sulname', models.CharField(max_length=255, unique=True, null=True, verbose_name='SUL username', blank=True)),
                ('sulemail', models.EmailField(max_length=254, null=True, verbose_name='SUL email address', blank=True)),
                ('realname', models.CharField(max_length=255, null=True, verbose_name='real name', blank=True)),
                ('oauthtoken', models.CharField(max_length=127, null=True, verbose_name='OAuth token', blank=True)),
                ('oauthsecret', models.CharField(max_length=127, null=True, verbose_name='OAuth secret', blank=True)),
                ('authhash', models.CharField(default=striker.labsauth.models.make_authhash, verbose_name='authhash', max_length=128, editable=False)),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to=b'auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
                ('phabimage', models.CharField(max_length=255, null=True, verbose_name='image', blank=True)),
                ('phabname', models.CharField(max_length=255, unique=True, null=True, verbose_name='Phabricator username', blank=True)),
                ('phabrealname', models.CharField(max_length=255, null=True, verbose_name='Phabricator real name', blank=True)),
                ('phaburl', models.CharField(max_length=255, null=True, verbose_name='Phabricator url', blank=True)),
                ('phid', models.CharField(max_length=255, null=True, verbose_name='phid', blank=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
        ),
    ]
