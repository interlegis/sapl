# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0021_auto_20151119_1617'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='publicacao',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='publicacao',
            name='created',
            field=models.DateTimeField(verbose_name='created', auto_now_add=True, default=datetime.datetime(2015, 11, 20, 17, 3, 45, 347063, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='publicacao',
            name='modified',
            field=models.DateTimeField(verbose_name='modified', default=datetime.datetime(2015, 11, 20, 17, 3, 51, 67108, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
