# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cronometro',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('status', models.CharField(max_length=1, verbose_name='Status do cronômetro', choices=[('I', 'Start'), ('R', 'Reset'), ('S', 'Stop')], default='S')),
                ('data_cronometro', models.DateField(verbose_name='Data do cronômetro')),
                ('tipo', models.CharField(max_length=1, verbose_name='Tipo Cronômetro', choices=[('A', 'Aparte'), ('D', 'Discurso'), ('O', 'Ordem do dia')])),
            ],
        ),
        migrations.CreateModel(
            name='Painel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('aberto', models.BooleanField(default=False, verbose_name='Abrir painel')),
                ('data_painel', models.DateField(verbose_name='Data painel')),
                ('mostrar', models.CharField(max_length=1, choices=[('C', 'Completo'), ('P', 'Parlamentares'), ('V', 'Votação'), ('M', 'Mensagem')], default='C')),
            ],
        ),
    ]
