# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
import json
import os
from datetime import timedelta

from django.core.management import call_command



def altera_data_inicio_mandato(apps, schema_editor):
    Mandato = apps.get_model("parlamentares", "Mandato")
    mandatos = Mandato.objects.all()

    for mandato in mandatos:
        data_inicio = mandato.data_inicio_mandato
        data_inicio_legislatura = mandato.legislatura.data_inicio
        days = abs((data_inicio - data_inicio_legislatura).days)

        if days >= 60:
            mandato.data_inicio_mandato = data_inicio_legislatura
            mandato.save()


class Migration(migrations.Migration):

    dependencies = [
        # A dependencia real desse script é o arquivo 0001_initial.py, mas
        # isso gera um erro (Conflicting migrations detected; multiple leaf
         # nodes in the migration graph). para não ocasionar problemas de migração,
         # vamos manter a ordem padrão do django.
        ('parlamentares', '0009_auto_20170905_1617'),
    ]

    operations = [
        migrations.RunPython(altera_data_inicio_mandato),
    ]
