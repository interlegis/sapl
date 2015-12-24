# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0037_auto_20151224_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipotextoarticulado',
            name='participacao_social',
            field=models.NullBooleanField(default=False, verbose_name='Participação Social', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
        migrations.AlterField(
            model_name='textoarticulado',
            name='participacao_social',
            field=models.NullBooleanField(default=None, verbose_name='Participação Social', choices=[(None, 'Padrão definido no Tipo'), (True, 'Sim'), (False, 'Não')]),
        ),
    ]
