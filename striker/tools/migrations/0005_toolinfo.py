# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


def fix_toolinfo_row_format(apps, schema_editor):
    if not schema_editor.connection.vendor == 'mysql':
        return
    migrations.RunSQL('ALTER TABLE tools_toolinfo ROW_FORMAT = DYNAMIC;')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tools', '0004_accessrequest_suppress'),
    ]

    operations = [
        migrations.CreateModel(
            name='SoftwareLicense',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('slug', models.CharField(unique=True, max_length=32)),
                ('name', models.CharField(max_length=255)),
                ('url', models.CharField(max_length=2047)),
                ('family', models.CharField(max_length=32, db_index=True)),
                ('osi_approved', models.BooleanField()),
                ('recommended', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='ToolInfo',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(unique=True, max_length=128)),
                ('tool', models.CharField(max_length=64, db_index=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('suburl', models.CharField(null=True, max_length=2047, blank=True)),
                ('repository', models.CharField(null=True, max_length=2047, blank=True)),
                ('issues', models.CharField(null=True, max_length=2047, blank=True)),
                ('docs', models.CharField(null=True, max_length=2047, blank=True)),
                ('authors', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='_toolinfo_authors_+')),
                ('license', models.ForeignKey(to='tools.SoftwareLicense', on_delete=models.CASCADE)),
                ('is_webservice', models.BooleanField()),
            ],
        ),
        # HACK! I really hate making django work with utf8mb4
        migrations.RunPython(fix_toolinfo_row_format),
        migrations.AlterField(
            model_name='toolinfo',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
        migrations.AlterModelOptions(
            name='toolinfo',
            options={'verbose_name': 'Toolinfo', 'verbose_name_plural': 'Toolinfo'},
        ),
    ]
