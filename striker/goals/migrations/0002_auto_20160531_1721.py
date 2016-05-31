# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goals', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='milestone',
            old_name='completedDate',
            new_name='completed_date',
        ),
    ]
