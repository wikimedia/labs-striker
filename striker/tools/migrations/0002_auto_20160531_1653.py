# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
from striker.labsauth.models import LabsUser
import datetime


class Migration(migrations.Migration):
    # semi-randomly pick a user to give existing repos to
    default_user = LabsUser.objects.all()[0].id

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tools', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='diffusionrepo',
            name='created_by',
            field=models.ForeignKey(default=default_user, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='diffusionrepo',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime.now, editable=False, blank=True),
        ),
    ]
