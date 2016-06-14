# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0038_tipotextoarticulado_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipotextoarticulado',
            name='model',
            field=models.CharField(verbose_name='Modelagem Django', default='', blank=True, null=True, max_length=50, unique=True),
        ),
    ]
