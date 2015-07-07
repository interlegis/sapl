# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='materialegislativa',
            old_name='ano_ident_basica',
            new_name='ano',
        ),
        migrations.RenameField(
            model_name='materialegislativa',
            old_name='numero_ident_basica',
            new_name='numero',
        ),
        migrations.RenameField(
            model_name='materialegislativa',
            old_name='tipo_id_basica',
            new_name='tipo',
        ),
    ]
