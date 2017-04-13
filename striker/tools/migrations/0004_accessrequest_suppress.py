# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0003_accessrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='accessrequest',
            name='suppressed',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
