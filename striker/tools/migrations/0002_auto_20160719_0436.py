# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0001_squashed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diffusionrepo",
            name="phid",
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name="diffusionrepo",
            name="tool",
            field=models.CharField(max_length=64),
        ),
    ]
