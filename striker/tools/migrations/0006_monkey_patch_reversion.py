# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class AddRemoteField(migrations.AddField):
    """From https://stackoverflow.com/a/27160571/8171"""

    def __init__(self, remote_app, *args, **kwargs):
        super(AddRemoteField, self).__init__(*args, **kwargs)
        self.remote_app = remote_app

    def state_forwards(self, app_label, *args, **kwargs):
        super(AddRemoteField, self).state_forwards(self.remote_app, *args, **kwargs)

    def database_forwards(self, app_label, *args, **kwargs):
        super(AddRemoteField, self).database_forwards(self.remote_app, *args, **kwargs)

    def database_backwards(self, app_label, *args, **kwargs):
        super(AddRemoteField, self).database_backwards(self.remote_app, *args, **kwargs)


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0005_toolinfo"),
        ("reversion", "0001_squashed_0004_auto_20160611_1202"),
    ]

    operations = [
        # HACK! Add monkey patched field to reversion_version
        AddRemoteField(
            remote_app="reversion",
            model_name="version",
            name="suppressed",
            field=models.BooleanField(blank=True, default=False, db_index=True),
            preserve_default=True,
        ),
    ]
