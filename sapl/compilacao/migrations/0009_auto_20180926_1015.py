# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-09-26 13:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0008_auto_20180924_1724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipodispositivo',
            name='class_css',
            field=models.CharField(blank=True, max_length=256, verbose_name='Classe CSS'),
        ),
    ]
