# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0018_auto_20151119_1052'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilestruturaltextosnormativos',
            name='sigla',
            field=models.CharField(max_length=10, verbose_name='Sigla', default='LC95'),
            preserve_default=False,
        ),
    ]
