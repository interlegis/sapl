# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dispositivo',
            options={'ordering': ['norma', 'ordem'], 'verbose_name_plural': 'Dispositivos', 'verbose_name': 'Dispositivo'},
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_atualizador',
            field=models.ForeignKey(related_name='dispositivos_alterados_set', to='compilacao.Dispositivo', null=True, verbose_name='Dispositivo Atualizador', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_pai',
            field=models.ForeignKey(related_name='+', to='compilacao.Dispositivo', null=True, verbose_name='Dispositivo Pai', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_subsequente',
            field=models.ForeignKey(related_name='+', to='compilacao.Dispositivo', null=True, verbose_name='Dispositivo Subsequente', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_substituido',
            field=models.ForeignKey(related_name='+', to='compilacao.Dispositivo', null=True, verbose_name='Dispositivo Substituido', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_vigencia',
            field=models.ForeignKey(related_name='+', to='compilacao.Dispositivo', null=True, verbose_name='Dispositivo de Vigência', default=None, blank=True),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='norma_publicada',
            field=models.ForeignKey(related_name='dispositivos_alterados_set', to='norma.NormaJuridica', null=True, verbose_name='Norma Jurídica Publicada', default=None, blank=True),
        ),
    ]
