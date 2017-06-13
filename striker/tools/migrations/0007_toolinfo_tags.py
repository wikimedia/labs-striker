# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0006_monkey_patch_reversion'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToolInfoTag',
            options={'ordering': ('name',)},
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('slug', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='toolinfo',
            name='tags',
            field=models.ManyToManyField(blank=True, to='tools.ToolInfoTag'),
        ),
    ]
