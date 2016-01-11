# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0037_auto_20151226_1414'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipotextoarticulado',
            name='model',
            field=models.CharField(max_length=50, blank=True, default='', null=True, verbose_name='Modelagem Django'),
        ),
    ]
