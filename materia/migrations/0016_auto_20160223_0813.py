# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0015_auto_20160216_1015'),
    ]

    operations = [
        migrations.AddField(
            model_name='acompanhamentomateria',
            name='data_cadastro',
            field=models.DateField(auto_now_add=True, default=datetime.datetime(2016, 2, 23, 11, 13, 25, 362112, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='acompanhamentomateria',
            name='usuario',
            field=models.CharField(max_length=50, default=''),
            preserve_default=False,
        ),
    ]
