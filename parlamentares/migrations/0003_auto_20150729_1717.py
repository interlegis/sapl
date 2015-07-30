# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0002_auto_20150729_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coligacao',
            name='numero_votos',
            field=models.PositiveIntegerField(blank=True, verbose_name='Nº Votos Recebidos', null=True),
        ),
        migrations.AlterField(
            model_name='mandato',
            name='tipo_causa_fim_mandato',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='mandato',
            name='votos_recebidos',
            field=models.PositiveIntegerField(blank=True, verbose_name='Votos Recebidos', null=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='cod_casa',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='sessaolegislativa',
            name='numero',
            field=models.PositiveIntegerField(verbose_name='Número'),
        ),
    ]
