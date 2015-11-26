# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0007_auto_20151123_1258'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parlamentar',
            name='cod_casa',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Cód. Casa'),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='nome_parlamentar',
            field=models.CharField(default=1, verbose_name='Nome Parlamentar', max_length=50),
            preserve_default=False,
        ),
    ]
