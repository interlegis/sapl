# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.utils.timezone import utc
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronometro',
            name='data',
            field=models.DateField(null=True, verbose_name='Data cronômetro', auto_now_add=True),
        ),
        migrations.AddField(
            model_name='painel',
            name='data_painel',
            field=models.DateField(default=datetime.datetime(2015, 9, 8, 17, 35, 48, 279510, tzinfo=utc), verbose_name='Data painel', auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cronometro',
            name='reset',
            field=models.PositiveIntegerField(verbose_name='Reiniciar cronômetro'),
        ),
        migrations.AlterField(
            model_name='cronometro',
            name='start',
            field=models.PositiveIntegerField(verbose_name='Iniciar cronômetro'),
        ),
        migrations.AlterField(
            model_name='cronometro',
            name='stop',
            field=models.PositiveIntegerField(verbose_name='Parar cronômetro'),
        ),
        migrations.AlterField(
            model_name='cronometro',
            name='tipo',
            field=models.CharField(choices=[('A', 'Aparte'), ('D', 'Discurso'), ('O', 'Ordem do dia')], verbose_name='Tipo Cronômetro', max_length=1),
        ),
        migrations.AlterField(
            model_name='painel',
            name='abrir',
            field=models.PositiveIntegerField(default=0, verbose_name='Abrir painel'),
        ),
        migrations.AlterField(
            model_name='painel',
            name='fechar',
            field=models.PositiveIntegerField(default=1, verbose_name='Fechar painel'),
        ),
        migrations.AlterField(
            model_name='painel',
            name='mostrar',
            field=models.CharField(default='C', choices=[('C', 'Completo'), ('P', 'Parlamentares'), ('V', 'Votação'), ('M', 'Mensagem')], max_length=1),
        ),
    ]
