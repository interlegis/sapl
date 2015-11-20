# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0005_parlamentar_fotografia'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parlamentar',
            name='unidade_deliberativa',
            field=models.BooleanField(verbose_name='Unidade'),
        ),
    ]
