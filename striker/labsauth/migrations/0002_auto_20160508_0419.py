# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('labsauth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='labsuser',
            name='phabimage',
            field=models.CharField(max_length=255, null=True, verbose_name='image', blank=True),
        ),
        migrations.AddField(
            model_name='labsuser',
            name='phabname',
            field=models.CharField(max_length=255, unique=True, null=True, verbose_name='Phabricator username', blank=True),
        ),
        migrations.AddField(
            model_name='labsuser',
            name='phabrealname',
            field=models.CharField(max_length=255, null=True, verbose_name='Phabricator real name', blank=True),
        ),
        migrations.AddField(
            model_name='labsuser',
            name='phaburl',
            field=models.CharField(max_length=255, null=True, verbose_name='Phabricator url', blank=True),
        ),
        migrations.AddField(
            model_name='labsuser',
            name='phid',
            field=models.CharField(max_length=255, null=True, verbose_name='phid', blank=True),
        ),
    ]
