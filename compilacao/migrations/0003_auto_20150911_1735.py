# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0002_auto_20150907_2334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_pai',
            field=models.ForeignKey(blank=True, null=True, verbose_name='Dispositivo Pai', to='compilacao.Dispositivo', related_name='filhos', default=None),
        ),
    ]
