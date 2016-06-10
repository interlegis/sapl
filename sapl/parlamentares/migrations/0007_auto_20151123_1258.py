# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0006_auto_20151119_1318'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parlamentar',
            name='unidade_deliberativa',
            field=models.BooleanField(),
        ),
    ]
