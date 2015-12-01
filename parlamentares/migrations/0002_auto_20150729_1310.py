# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipoafastamento',
            name='afastamento',
            field=models.BooleanField(verbose_name='Indicador', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
    ]
