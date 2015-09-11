# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cronometro',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('start', models.PositiveIntegerField(verbose_name='Iniciar cronômetro')),
                ('reset', models.PositiveIntegerField(verbose_name='Reiniciar cronômetro')),
                ('stop', models.PositiveIntegerField(verbose_name='Parar cronômetro')),
                ('data_painel', models.DateField(verbose_name='Data cronômetro')),
                ('tipo', models.CharField(max_length=1, choices=[('A', 'Aparte'), ('D', 'Discurso'), ('O', 'Ordem do dia')], verbose_name='Tipo Cronômetro')),
            ],
        ),
        migrations.CreateModel(
            name='Painel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('abrir', models.PositiveIntegerField(verbose_name='Abrir painel', default=0)),
                ('fechar', models.PositiveIntegerField(verbose_name='Fechar painel', default=1)),
                ('data_painel', models.DateField(verbose_name='Data painel')),
                ('mostrar', models.CharField(max_length=1, choices=[('C', 'Completo'), ('P', 'Parlamentares'), ('V', 'Votação'), ('M', 'Mensagem')], default='C')),
            ],
        ),
    ]
