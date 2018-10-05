# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-09-08 10:24
from __future__ import unicode_literals

from django.db import migrations

from sapl.materia.models import TipoProposicao


class AlterUniqueTogetherFixConstraintInexistente(
        migrations.AlterUniqueTogether):

    def database_forwards(self,
                          app_label, schema_editor, from_state, to_state):
        constraint_names = schema_editor._constraint_names(
            TipoProposicao, ['content_type_id', 'object_id'], unique=True)
        if constraint_names:
            # por alguma razão a constraint não existe em alguns bancos
            # se ela existir continua a exetução normal
            super(AlterUniqueTogetherFixConstraintInexistente,
                  self).database_forwards(
                app_label, schema_editor, from_state, to_state
            )


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0014_auto_20170905_0818'),
    ]

    operations = [
        AlterUniqueTogetherFixConstraintInexistente(
            name='tipoproposicao',
            unique_together=set([]),
        ),
    ]
