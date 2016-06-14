# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0005_auto_20150924_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_ordinal',
            field=models.IntegerField(choices=[(-1, 'Numeração Cardinal.'), (0, 'Numeração Ordinal.'), (9, 'Numeração Ordinal até o item nove.')], verbose_name='Tipo de número do rótulo'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_prefixo_texto',
            field=models.CharField(blank=True, max_length=30, verbose_name='Prefixo de Edição do rótulo'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao01',
            field=models.CharField(blank=True, default='-', max_length=1, verbose_name='Separador entre Numeração e Variação 1'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao12',
            field=models.CharField(blank=True, default='-', max_length=1, verbose_name='Separador entre Variação 1 e Variação 2'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao23',
            field=models.CharField(blank=True, default='-', max_length=1, verbose_name='Separador entre Variação 2 e Variação 3'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao34',
            field=models.CharField(blank=True, default='-', max_length=1, verbose_name='Separador entre Variação 3 e Variação 4'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao45',
            field=models.CharField(blank=True, default='-', max_length=1, verbose_name='Separador entre Variação 4 e Variação 5'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_sufixo_texto',
            field=models.CharField(blank=True, max_length=30, verbose_name='Sufixo de Edição do rótulo'),
        ),
    ]
