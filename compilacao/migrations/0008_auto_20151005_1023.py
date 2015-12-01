# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0007_auto_20150924_1131'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipodispositivo',
            name='dispositivo_de_articulacao',
            field=models.BooleanField(verbose_name='Dispositivo de Articulação (Sem Texto)', default=False, choices=[
                                      (True, 'Sim'), (False, 'Não')]),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao01',
            field=models.CharField(
                verbose_name='Separador entre Numeração e Variação 1', default='-', max_length=1),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao12',
            field=models.CharField(
                verbose_name='Separador entre Variação 1 e Variação 2', default='-', max_length=1),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao23',
            field=models.CharField(
                verbose_name='Separador entre Variação 2 e Variação 3', default='-', max_length=1),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao34',
            field=models.CharField(
                verbose_name='Separador entre Variação 3 e Variação 4', default='-', max_length=1),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao45',
            field=models.CharField(
                verbose_name='Separador entre Variação 4 e Variação 5', default='-', max_length=1),
        ),
    ]
