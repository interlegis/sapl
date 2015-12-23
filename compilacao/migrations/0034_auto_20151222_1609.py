# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0033_auto_20151222_1608'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dispositivo',
            options={'ordering': ['ta', 'ordem'], 'verbose_name_plural': 'Dispositivos', 'verbose_name': 'Dispositivo'},
        ),
        migrations.AlterUniqueTogether(
            name='dispositivo',
            unique_together=set([('ta', 'dispositivo0', 'dispositivo1', 'dispositivo2', 'dispositivo3', 'dispositivo4', 'dispositivo5', 'tipo_dispositivo', 'dispositivo_pai', 'ta_publicado', 'publicacao'), ('ta', 'ordem')]),
        ),
    ]
