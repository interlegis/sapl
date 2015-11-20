# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0004_auto_20150914_0842'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tipodispositivo',
            options={'verbose_name_plural': 'Tipos de Dispositivo', 'verbose_name': 'Tipo de Dispositivo', 'ordering': ['id']},
        ),
        migrations.RemoveField(
            model_name='tipodispositivo',
            name='rotulo_separadores_variacao',
        ),
        migrations.AddField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao01',
            field=models.CharField(max_length=1, default='-', verbose_name='Separadores entre Numeração e Variação 1', blank=True),
        ),
        migrations.AddField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao12',
            field=models.CharField(max_length=1, default='-', verbose_name='Separadores entre Variação 1 e Variação 2', blank=True),
        ),
        migrations.AddField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao23',
            field=models.CharField(max_length=1, default='-', verbose_name='Separadores entre Variação 2 e Variação 3', blank=True),
        ),
        migrations.AddField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao34',
            field=models.CharField(max_length=1, default='-', verbose_name='Separadores entre Variação 3 e Variação 4', blank=True),
        ),
        migrations.AddField(
            model_name='tipodispositivo',
            name='rotulo_separador_variacao45',
            field=models.CharField(max_length=1, default='-', verbose_name='Separadores entre Variação 4 e Variação 5', blank=True),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='formato_variacao0',
            field=models.CharField(max_length=1, default='1', choices=[('1', '1-Numérico'), ('I', 'I-Romano Maiúsculo'), ('i', 'i-Romano Minúsculo'), ('A', 'A-Alfabético Maiúsculo'), ('a', 'a-Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')], verbose_name='Formato da Numeração'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='formato_variacao1',
            field=models.CharField(max_length=1, default='1', choices=[('1', '1-Numérico'), ('I', 'I-Romano Maiúsculo'), ('i', 'i-Romano Minúsculo'), ('A', 'A-Alfabético Maiúsculo'), ('a', 'a-Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')], verbose_name='Formato da Variação 1'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='formato_variacao2',
            field=models.CharField(max_length=1, default='1', choices=[('1', '1-Numérico'), ('I', 'I-Romano Maiúsculo'), ('i', 'i-Romano Minúsculo'), ('A', 'A-Alfabético Maiúsculo'), ('a', 'a-Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')], verbose_name='Formato da Variação 2'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='formato_variacao3',
            field=models.CharField(max_length=1, default='1', choices=[('1', '1-Numérico'), ('I', 'I-Romano Maiúsculo'), ('i', 'i-Romano Minúsculo'), ('A', 'A-Alfabético Maiúsculo'), ('a', 'a-Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')], verbose_name='Formato da Variação 3'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='formato_variacao4',
            field=models.CharField(max_length=1, default='1', choices=[('1', '1-Numérico'), ('I', 'I-Romano Maiúsculo'), ('i', 'i-Romano Minúsculo'), ('A', 'A-Alfabético Maiúsculo'), ('a', 'a-Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')], verbose_name='Formato da Variação 4'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='formato_variacao5',
            field=models.CharField(max_length=1, default='1', choices=[('1', '1-Numérico'), ('I', 'I-Romano Maiúsculo'), ('i', 'i-Romano Minúsculo'), ('A', 'A-Alfabético Maiúsculo'), ('a', 'a-Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')], verbose_name='Formato da Variação 5'),
        ),
    ]
