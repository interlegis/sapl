# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0023_auto_20151120_1529'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nota',
            name='data_criacao',
        ),
        migrations.RemoveField(
            model_name='vide',
            name='data_criacao',
        ),
        migrations.AddField(
            model_name='nota',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2015, 11, 20, 20, 13, 57, 385520, tzinfo=utc), verbose_name='created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='nota',
            name='modified',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 11, 20, 20, 14, 3, 360297, tzinfo=utc), verbose_name='modified'),
            preserve_default=False,
        ),
    ]
