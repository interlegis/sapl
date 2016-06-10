# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0041_auto_20160109_1928'),
    ]

    operations = [
        migrations.AddField(
            model_name='publicacao',
            name='hora',
            field=models.TimeField(default=datetime.datetime(
                2016, 1, 10, 18, 20, 1, 151209, tzinfo=utc), verbose_name='Horário de Publicação'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='publicacao',
            name='ano',
            field=models.PositiveIntegerField(
                verbose_name='Ano', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publicacao',
            name='data',
            field=models.DateField(verbose_name='Data de Publicação'),
        ),
        migrations.AlterField(
            model_name='publicacao',
            name='edicao',
            field=models.PositiveIntegerField(
                verbose_name='Edição', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='publicacao',
            name='numero',
            field=models.PositiveIntegerField(
                verbose_name='Número', blank=True, null=True),
        ),
    ]
