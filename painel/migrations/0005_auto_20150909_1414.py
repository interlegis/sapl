# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0004_auto_20150908_1858'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cronometro',
            old_name='data_painel',
            new_name='data_cronometro',
        ),
        migrations.RemoveField(
            model_name='cronometro',
            name='time',
        ),
    ]
