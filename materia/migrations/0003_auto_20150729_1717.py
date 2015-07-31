# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0002_auto_20150729_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='despachoinicial',
            name='numero_ordem',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='ano',
            field=models.PositiveSmallIntegerField(verbose_name='Ano'),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='ano_origem_externa',
            field=models.PositiveSmallIntegerField(blank=True, verbose_name='Ano', null=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='dias_prazo',
            field=models.PositiveIntegerField(blank=True, verbose_name='Dias Prazo', null=True),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='numero',
            field=models.PositiveIntegerField(verbose_name='Número'),
        ),
        migrations.AlterField(
            model_name='materialegislativa',
            name='numero_protocolo',
            field=models.PositiveIntegerField(blank=True, verbose_name='Núm. Protocolo', null=True),
        ),
        migrations.AlterField(
            model_name='numeracao',
            name='ano_materia',
            field=models.PositiveSmallIntegerField(verbose_name='Ano'),
        ),
        migrations.AlterField(
            model_name='numeracao',
            name='numero_ordem',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='proposicao',
            name='numero_proposicao',
            field=models.PositiveIntegerField(blank=True, verbose_name='Número', null=True),
        ),
        migrations.AlterField(
            model_name='tipomaterialegislativa',
            name='quorum_minimo_votacao',
            field=models.PositiveIntegerField(),
        ),
    ]
