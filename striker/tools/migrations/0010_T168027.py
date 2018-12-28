# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tools', '0009_toolinfo_authors'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessRequestComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, db_index=True, editable=False, blank=True)),
                ('comment', models.TextField()),
            ],
            options={
                'ordering': ('created_date', 'user'),
            },
        ),
        migrations.AlterField(
            model_name='accessrequest',
            name='status',
            field=models.CharField(choices=[('p', 'Pending'), ('f', 'Feedback needed'), ('a', 'Approved'), ('d', 'Declined')], max_length=1, default='p', db_index=True),
        ),
        migrations.AddField(
            model_name='accessrequestcomment',
            name='request',
            field=models.ForeignKey(related_name='comments', to='tools.AccessRequest', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='accessrequestcomment',
            name='user',
            field=models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
