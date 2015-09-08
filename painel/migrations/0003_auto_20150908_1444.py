# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0002_auto_20150908_1435'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cronometro',
            name='data',
            field=models.DateField(verbose_name='Data cronômetro', default=datetime.datetime(2015, 9, 8, 17, 44, 1, 708326, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='painel',
            name='data_painel',
            field=models.DateField(verbose_name='Data painel'),
        ),
    ]
