# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0002_auto_20150908_1818'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronometro',
            name='counter',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
