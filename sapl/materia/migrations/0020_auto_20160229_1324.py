# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0019_auto_20160229_1321'),
    ]

    operations = [
        migrations.AlterField(
            model_name='materialegislativa',
            name='data_apresentacao',
            field=models.DateField(default=datetime.datetime(2016, 2, 29, 16, 24, 24, 963568, tzinfo=utc), verbose_name='Data Apresentação'),
            preserve_default=False,
        ),
    ]
