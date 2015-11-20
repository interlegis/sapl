# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orgao',
            name='unidade_deliberativa',
            field=models.BooleanField(verbose_name='Unidade Deliberativa', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
    ]
