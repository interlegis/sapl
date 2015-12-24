# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0036_auto_20151224_1341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textoarticulado',
            name='participacao_social',
            field=models.NullBooleanField(verbose_name='Participação Social', choices=[(True, 'Sim'), (False, 'Não')], default=False),
        ),
    ]
