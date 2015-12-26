# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0036_auto_20151226_1411'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textoarticulado',
            name='object_id',
            field=models.PositiveIntegerField(blank=True, default=None, null=True),
        ),
    ]
