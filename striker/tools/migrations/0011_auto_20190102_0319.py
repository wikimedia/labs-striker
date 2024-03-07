# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0010_T168027"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrequest",
            name="suppressed",
            field=models.BooleanField(blank=True, db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name="toolinfo",
            name="license",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="tools.SoftwareLicense"
            ),
        ),
    ]
