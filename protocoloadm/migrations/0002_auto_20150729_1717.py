# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='ano',
            field=models.PositiveSmallIntegerField(verbose_name='Ano'),
        ),
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='dias_prazo',
            field=models.PositiveIntegerField(blank=True, verbose_name='Dias Prazo', null=True),
        ),
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='numero',
            field=models.PositiveIntegerField(verbose_name='Número'),
        ),
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='numero_protocolo',
            field=models.PositiveIntegerField(blank=True, verbose_name='Núm. Protocolo', null=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='ano',
            field=models.PositiveSmallIntegerField(),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='numero',
            field=models.PositiveIntegerField(blank=True, verbose_name='Número do Protocolo', null=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='numero_paginas',
            field=models.PositiveIntegerField(blank=True, verbose_name='Número de Páginas', null=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='tipo_processo',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='tipo_protocolo',
            field=models.PositiveIntegerField(verbose_name='Tipo de Protocolo'),
        ),
    ]
