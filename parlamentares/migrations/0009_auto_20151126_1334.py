# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0008_auto_20151126_1332'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parlamentar',
            name='cod_casa',
        ),
        migrations.RemoveField(
            model_name='parlamentar',
            name='unidade_deliberativa',
        ),
    ]
