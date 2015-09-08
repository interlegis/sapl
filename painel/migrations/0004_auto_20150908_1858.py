# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0003_cronometro_counter'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cronometro',
            name='counter',
        ),
        migrations.RemoveField(
            model_name='cronometro',
            name='reset',
        ),
        migrations.RemoveField(
            model_name='cronometro',
            name='start',
        ),
        migrations.RemoveField(
            model_name='cronometro',
            name='stop',
        ),
        migrations.AddField(
            model_name='cronometro',
            name='status',
            field=models.CharField(max_length=1, verbose_name='Status do cronômetro', choices=[('I', 'Start'), ('R', 'Reset'), ('S', 'Stop')], default='S'),
        ),
        migrations.AddField(
            model_name='cronometro',
            name='time',
            field=models.FloatField(verbose_name='Start time', default=0),
        ),
        migrations.AlterField(
            model_name='cronometro',
            name='data_painel',
            field=models.DateField(verbose_name='Data do cronômetro'),
        ),
    ]
