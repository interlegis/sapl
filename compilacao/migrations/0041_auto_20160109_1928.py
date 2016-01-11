# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0040_auto_20160106_1956'),
    ]

    operations = [
        migrations.RenameField(
            model_name='publicacao',
            old_name='publicacao',
            new_name='data',
        ),
        migrations.AddField(
            model_name='publicacao',
            name='ano',
            field=models.PositiveIntegerField(null=True, verbose_name='Pg. Início', blank=True),
        ),
        migrations.AddField(
            model_name='publicacao',
            name='edicao',
            field=models.PositiveIntegerField(null=True, verbose_name='Pg. Início', blank=True),
        ),
        migrations.AddField(
            model_name='publicacao',
            name='numero',
            field=models.PositiveIntegerField(null=True, verbose_name='Pg. Início', blank=True),
        ),
        migrations.AddField(
            model_name='publicacao',
            name='url_externa',
            field=models.CharField(max_length=1024, verbose_name='Link para Versão Eletrônica', blank=True),
        ),
    ]
