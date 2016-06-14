# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0005_auto_20151008_0744'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoacessorioadministrativo',
            name='assunto',
            field=models.TextField(verbose_name='Assunto', blank=True),
        ),
        migrations.AlterField(
            model_name='documentoacessorioadministrativo',
            name='autor',
            field=models.CharField(verbose_name='Autor', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='documentoacessorioadministrativo',
            name='indexacao',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='interessado',
            field=models.CharField(verbose_name='Interessado', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='observacao',
            field=models.TextField(verbose_name='Observação', blank=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='assunto_ementa',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='interessado',
            field=models.CharField(verbose_name='Interessado', max_length=60, blank=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='ip_anulacao',
            field=models.CharField(max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='justificativa_anulacao',
            field=models.CharField(max_length=60, blank=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='observacao',
            field=models.TextField(verbose_name='Observação', blank=True),
        ),
        migrations.AlterField(
            model_name='protocolo',
            name='user_anulacao',
            field=models.CharField(max_length=20, blank=True),
        ),
        migrations.AlterField(
            model_name='tramitacaoadministrativo',
            name='texto',
            field=models.TextField(verbose_name='Texto da Ação', blank=True),
        ),
    ]
