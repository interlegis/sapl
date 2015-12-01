# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0013_auto_20151106_1843'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipodispositivo',
            name='quantidade_permitida',
            field=models.IntegerField(default=-1, verbose_name='Quantidade permitida dentro de uma Norma'),
        ),
    ]
