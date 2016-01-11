# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0033_auto_20151226_1320'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='dispositivo',
            unique_together=set([('ta', 'ordem'), ('ta', 'dispositivo0', 'dispositivo1', 'dispositivo2', 'dispositivo3', 'dispositivo4', 'dispositivo5', 'tipo_dispositivo', 'dispositivo_pai', 'ta_publicado', 'publicacao')]),
        ),
    ]
