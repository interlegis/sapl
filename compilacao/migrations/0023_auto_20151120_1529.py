# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0022_auto_20151120_1503'),
    ]

    operations = [
        migrations.AddField(
            model_name='vide',
            name='created',
            field=models.DateTimeField(verbose_name='created', auto_now_add=True, default=datetime.datetime(2015, 11, 20, 17, 29, 27, 32283, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vide',
            name='modified',
            field=models.DateTimeField(verbose_name='modified', auto_now=True, default=datetime.datetime(2015, 11, 20, 17, 29, 31, 856683, tzinfo=utc)),
            preserve_default=False,
        ),
    ]
