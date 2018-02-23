# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db import migrations

def popula_campo_data_inicio(apps, schema_editor):
    Mandato = apps.get_model("parlamentares", "Mandato")
    mandatos = Mandato.objects.all()

    for m in mandatos:
        if m.data_inicio_mandato == None:
            m.data_inicio_mandato = m.legislatura.data_inicio
            m.save()


class Migration(migrations.Migration):

    dependencies = [
        # A dependencia real desse script é o arquivo 0001_initial.py, mas
        # isso gera um erro (Conflicting migrations detected; multiple leaf
        # nodes in the migration graph). para não ocasionar problemas de migração,
        # vamos manter a ordem padrão do django.
        ('parlamentares', '0019_auto_20180221_1155'),
    ]

    operations = [
        migrations.RunPython(popula_campo_data_inicio),
    ]