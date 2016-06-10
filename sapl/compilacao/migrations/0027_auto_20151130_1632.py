# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0026_auto_20151122_1756'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='nota',
            options={'verbose_name': 'Nota', 'ordering': ['-publicacao', '-modified'], 'verbose_name_plural': 'Notas'},
        ),
        migrations.AlterField(
            model_name='nota',
            name='titulo',
            field=models.CharField(verbose_name='Título', default='', blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='vide',
            name='dispositivo_base',
            field=models.ForeignKey(verbose_name='Dispositivo Base', related_name='cita', to='compilacao.Dispositivo'),
        ),
        migrations.AlterField(
            model_name='vide',
            name='dispositivo_ref',
            field=models.ForeignKey(verbose_name='Dispositivo Referido', related_name='citado', to='compilacao.Dispositivo'),
        ),
    ]
