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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('start', models.PositiveIntegerField()),
                ('reset', models.PositiveIntegerField()),
                ('stop', models.PositiveIntegerField()),
                ('tipo', models.CharField(choices=[('A', 'Aparte'), ('D', 'Discurso'), ('O', 'Ordem do dia')], max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Painel',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('abrir', models.PositiveIntegerField()),
                ('fechar', models.PositiveIntegerField()),
                ('mostrar', models.CharField(choices=[('C', 'Completo'), ('P', 'Parlamentares'), ('V', 'Votação'), ('M', 'Mensagem')], max_length=1)),
            ],
        ),
    ]
