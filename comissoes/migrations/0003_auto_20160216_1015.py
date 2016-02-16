# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0002_auto_20150729_1310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comissao',
            name='agenda_reuniao',
            field=models.CharField(verbose_name='Data/Hora Reunião', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='apelido_temp',
            field=models.CharField(verbose_name='Apelido', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='email',
            field=models.CharField(verbose_name='E-mail', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='endereco_secretaria',
            field=models.CharField(verbose_name='Endereço Secretaria', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='fax_secretaria',
            field=models.CharField(verbose_name='Fax Secretaria', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='finalidade',
            field=models.TextField(verbose_name='Finalidade', blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='local_reuniao',
            field=models.CharField(verbose_name='Local Reunião', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='secretario',
            field=models.CharField(verbose_name='Secretário', max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='telefone_reuniao',
            field=models.CharField(verbose_name='Tel. Sala Reunião', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='comissao',
            name='telefone_secretaria',
            field=models.CharField(verbose_name='Tel. Secretaria', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='participacao',
            name='motivo_desligamento',
            field=models.CharField(verbose_name='Motivo Desligamento', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='participacao',
            name='observacao',
            field=models.CharField(verbose_name='Observação', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='tipocomissao',
            name='dispositivo_regimental',
            field=models.CharField(verbose_name='Dispositivo Regimental', max_length=50, blank=True),
        ),
    ]
