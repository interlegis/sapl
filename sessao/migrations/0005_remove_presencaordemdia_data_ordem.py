# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0004_auto_20150806_1614'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='presencaordemdia',
            name='data_ordem',
        ),
    ]
