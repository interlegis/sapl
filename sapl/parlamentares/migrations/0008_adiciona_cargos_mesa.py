# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
import json
import os


from django.core.management import call_command



def gera_cargos_mesa(apps, schema_editor):
    CargoMesa = apps.get_model("parlamentares", "CargoMesa")
    db_alias = schema_editor.connection.alias
    cargos_mesa = CargoMesa.objects.all().exists()

    if cargos_mesa:
        # Caso haja algum CargoMesa cadastrado na base de dados,
        # a migração não deve ser carregada para evitar duplicações de dados.
        print("Carga de {} não efetuada. Já Existem {} cadastrados...".format(
            CargoMesa._meta.verbose_name, CargoMesa._meta.verbose_name_plural))
    else:
        fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
        # pega partidos listados em fixtures/pre_popula_partidos.json
        fixture_filename = 'pre_popula_cargosmesa.json'
        fixture_file = os.path.join(fixture_dir, fixture_filename)
        call_command('loaddata', fixture_file)

class Migration(migrations.Migration):

    dependencies = [
        # A dependencia real desse script é o arquivo 0001_initial.py, mas
        # isso gera um erro (Conflicting migrations detected; multiple leaf
         # nodes in the migration graph). para não ocasionar problemas de migração,
         # vamos manter a ordem padrão do django.
        ('parlamentares', '0007_adiciona_partidos'),
    ]

    operations = [
        migrations.RunPython(gera_cargos_mesa),
    ]
