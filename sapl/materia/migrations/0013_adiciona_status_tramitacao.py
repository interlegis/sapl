# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations
import json
import os


from django.core.management import call_command



def gera_status_tramitacao(apps, schema_editor):
    StatusTramitacao = apps.get_model("materia", "StatusTramitacao")
    db_alias = schema_editor.connection.alias
    status_tramitacoes = StatusTramitacao.objects.all().exists()

    if status_tramitacoes:
        # Caso haja algum StatusTramitacao cadastrado na base de dados,
        # a migração não deve ser carregada para evitar duplicações de dados.
        print("Carga de {} não efetuada. Já Existem {} cadastrados...".format(
            StatusTramitacao._meta.verbose_name,
            StatusTramitacao._meta.verbose_name_plural
           )
        )
    else:
        fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
        # pega status_tramitacoes listados em fixtures/pre_popula_status_tramitacao.json
        fixture_filename = 'pre_popula_status_tramitacao.json'
        fixture_file = os.path.join(fixture_dir, fixture_filename)
        call_command('loaddata', fixture_file)

class Migration(migrations.Migration):

    dependencies = [
        # A dependencia real desse script é o arquivo 0001_initial.py, mas
        # isso gera um erro (Conflicting migrations detected; multiple leaf
         # nodes in the migration graph). para não ocasionar problemas de migração,
         # vamos manter a ordem padrão do django.
        ('materia', '0012_auto_20170829_1321'),
    ]

    operations = [
        migrations.RunPython(gera_status_tramitacao),
    ]
