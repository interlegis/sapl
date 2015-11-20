# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0008_auto_20151005_0814'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expedientemateria',
            old_name='votacao_iniciada',
            new_name='votacao_aberta',
        ),
        migrations.RenameField(
            model_name='ordemdia',
            old_name='votacao_iniciada',
            new_name='votacao_aberta',
        ),
    ]
