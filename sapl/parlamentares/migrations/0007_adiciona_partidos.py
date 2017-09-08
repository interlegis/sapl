# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
import json
import os


from django.core.management import call_command



def gera_partidos_tse(apps, schema_editor):
    Partido = apps.get_model("parlamentares", "Partido")
    db_alias = schema_editor.connection.alias
    partidos = Partido.objects.all().exists()

    if partidos:
        # Caso haja algum partido cadastrado na base de dados,
        # a migração não deve ser carregada para evitar duplicações de dados.
        print("Carga de Partido não efetuada. Já Existem partidos cadastrados...")
    else:
        fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
        # pega partidos listados em fixtures/pre_popula_partidos.json
        fixture_filename = 'pre_popula_partidos.json'
        fixture_file = os.path.join(fixture_dir, fixture_filename)
        call_command('loaddata', fixture_file)

class Migration(migrations.Migration):

    dependencies = [
        # A dependencia real desse script é o arquivo 0001_initial.py, mas
        # isso gera um erro (Conflicting migrations detected; multiple leaf
         # nodes in the migration graph). para não  ocasionar problemas de migração,
         # vamos manter a ordem padrão do django.
        ('parlamentares', '0006_auto_20170831_1400'),
    ]

    operations = [
        migrations.RunPython(gera_partidos_tse),
    ]
