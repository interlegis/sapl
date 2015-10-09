# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0006_auto_20150924_1121'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipodispositivo',
            name='class_css',
            field=models.CharField(max_length=20, blank=True, verbose_name='Classe CSS'),
        ),
    ]
