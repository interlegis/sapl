# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.core.management import call_command
from django.db import migrations


def gera_tipo_vinculo(apps, schema_editor):
    TipoVinculoNormaJuridica = apps.get_model("norma", "TipoVinculoNormaJuridica")

    db_alias = schema_editor.connection.alias
    tipo_vinculos = TipoVinculoNormaJuridica.objects.all().exists()

    if tipo_vinculos:
        # Caso haja algum TipoVinculoNormaJuridica cadastrado na base de dados,
        # a migração não deve ser carregada para evitar duplicações de dados.
        print("Carga de {} não efetuada. Já Existem {} cadastrados...".format(
            TipoVinculoNormaJuridica._meta.verbose_name,
            TipoVinculoNormaJuridica._meta.verbose_name_plural
           )
        )
    else:
        fixture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../fixtures'))
        # pega tipo_vinculo_norma_juridica listados em fixtures/pre_popula_tipo_vinculo_norma.json
        fixture_filename = 'pre_popula_tipo_vinculo_norma.json'
        fixture_file = os.path.join(fixture_dir, fixture_filename)
        call_command('loaddata', fixture_file)

class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0007_auto_20170904_1708'),
    ]

    operations = [
        migrations.RunPython(gera_tipo_vinculo),
    ]