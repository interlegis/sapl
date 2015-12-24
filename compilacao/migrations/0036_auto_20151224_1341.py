# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0035_auto_20151223_1709'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='textoarticulado',
            options={'verbose_name': 'Texto Articulado', 'verbose_name_plural': 'Textos Articulados', 'ordering': ['-data', '-numero']},
        ),
        migrations.AddField(
            model_name='textoarticulado',
            name='participacao_social',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], verbose_name='Participação Social', default=False),
        ),
    ]
