# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # A dependencia real desse script é o arquivo 0001_initial.py, mas
        # isso gera um erro (Conflicting migrations detected; multiple leaf
        # nodes in the migration graph). para não ocasionar problemas de migração,
        # vamos manter a ordem padrão do django.
        ('parlamentares', '0007_adiciona_partidos'),
    ]

    operations = [
        # obsoleto, migrado para 0044 devido a dependência gerada por 0043
        # migrations.RunPython(gera_cargos_mesa),
    ]
