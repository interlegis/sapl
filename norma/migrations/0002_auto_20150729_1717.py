# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='normajuridica',
            name='ano',
            field=models.PositiveSmallIntegerField(verbose_name='Ano'),
        ),
        migrations.AlterField(
            model_name='normajuridica',
            name='numero',
            field=models.PositiveIntegerField(verbose_name='Número'),
        ),
        migrations.AlterField(
            model_name='normajuridica',
            name='pagina_fim_publicacao',
            field=models.PositiveIntegerField(blank=True, verbose_name='Pg. Fim', null=True),
        ),
        migrations.AlterField(
            model_name='normajuridica',
            name='pagina_inicio_publicacao',
            field=models.PositiveIntegerField(blank=True, verbose_name='Pg. Início', null=True),
        ),
    ]
