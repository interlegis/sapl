# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-06-03 13:10
from __future__ import unicode_literals

from django.db import migrations


def create_default_cronometros(apps, schema_editor):
    tipos_default = ['Cronômetro do Discurso', 'Cronômetro do Aparte', 
                     'Cronômetro da Ordem', 'Cronômetro de Considerações Finais']
    Cronometro = apps.get_model('painel', 'Cronometro')
    for tipo in tipos_default:
        Cronometro.objects.get_or_create(tipo=tipo, duracao_cronometro='00:30:00', status='S')


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0003_auto_20190603_1009'),
    ]

    operations = [
        migrations.RunPython(create_default_cronometros)
    ]