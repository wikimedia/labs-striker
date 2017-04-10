# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tools', '0002_auto_20160719_0436'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessRequest',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('reason', models.TextField()),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, blank=True, editable=False, db_index=True)),
                ('admin_notes', models.TextField(blank=True, null=True)),
                ('status', models.CharField(default='p', max_length=1, choices=[('p', 'Pending'), ('a', 'Approved'), ('d', 'Declined')], db_index=True)),
                ('resolved_date', models.DateTimeField(blank=True, null=True)),
                ('resolved_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='resolver+', blank=True, null=True)),
                ('user', models.ForeignKey(related_name='requestor+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
