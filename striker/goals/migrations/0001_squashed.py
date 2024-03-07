# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    replaces = [("goals", "0001_initial"), ("goals", "0002_auto_20160531_1721")]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Milestone",
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
                ("goal", models.SmallIntegerField()),
                (
                    "completedDate",
                    models.DateTimeField(
                        default=timezone.now, editable=False, blank=True
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="milestones",
                        to=settings.AUTH_USER_MODEL,
                        on_delete=models.CASCADE,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="milestone",
            unique_together=set([("user", "goal")]),
        ),
        migrations.RenameField(
            model_name="milestone",
            old_name="completedDate",
            new_name="completed_date",
        ),
    ]
