# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0042_auto_20160110_1620'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publicacao',
            name='hora',
            field=models.TimeField(null=True, verbose_name='Horário de Publicação', blank=True),
        ),
    ]
