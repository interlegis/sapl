# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sessao.models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0003_remove_sessaoplenaria_tipo_expediente'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expedientemateria',
            name='numero_ordem',
            field=models.PositiveIntegerField(verbose_name='Nº Ordem'),
        ),
        migrations.AlterField(
            model_name='expedientemateria',
            name='tipo_votacao',
            field=models.PositiveIntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], verbose_name='Tipo de votação'),
        ),
        migrations.AlterField(
            model_name='orador',
            name='numero_ordem',
            field=models.PositiveIntegerField(verbose_name='Ordem de pronunciamento'),
        ),
        migrations.AlterField(
            model_name='oradorexpediente',
            name='numero_ordem',
            field=models.PositiveIntegerField(verbose_name='Ordem de pronunciamento'),
        ),
        migrations.AlterField(
            model_name='ordemdia',
            name='numero_ordem',
            field=models.PositiveIntegerField(verbose_name='Nº Ordem'),
        ),
        migrations.AlterField(
            model_name='ordemdia',
            name='tipo_votacao',
            field=models.PositiveIntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], verbose_name='Tipo de votação'),
        ),
        migrations.AlterField(
            model_name='registrovotacao',
            name='numero_abstencoes',
            field=models.PositiveIntegerField(verbose_name='Abstenções'),
        ),
        migrations.AlterField(
            model_name='registrovotacao',
            name='numero_votos_nao',
            field=models.PositiveIntegerField(verbose_name='Não'),
        ),
        migrations.AlterField(
            model_name='registrovotacao',
            name='numero_votos_sim',
            field=models.PositiveIntegerField(verbose_name='Sim'),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='cod_andamento_sessao',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='numero',
            field=models.PositiveIntegerField(verbose_name='Número'),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='upload_ata',
            field=models.FileField(blank=True, upload_to=sessao.models.ata_upload_path, null=True, verbose_name='Ata da Sessão'),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='upload_pauta',
            field=models.FileField(blank=True, upload_to=sessao.models.pauta_upload_path, null=True, verbose_name='Pauta da Sessão'),
        ),
        migrations.AlterField(
            model_name='tiposessaoplenaria',
            name='quorum_minimo',
            field=models.PositiveIntegerField(verbose_name='Quórum mínimo'),
        ),
    ]
