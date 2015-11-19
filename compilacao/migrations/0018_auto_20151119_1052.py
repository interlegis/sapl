# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0017_auto_20151119_1035'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tipodispositivo',
            name='quantidade_permitida',
        ),
        migrations.AddField(
            model_name='tipodispositivorelationship',
            name='quantidade_permitida',
            field=models.IntegerField(default=-1, verbose_name='Quantidade permitida nesta relação'),
        ),
    ]
