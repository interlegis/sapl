# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0025_auto_20151122_1744'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='nota',
            options={'verbose_name': 'Nota', 'ordering': ['publicacao'], 'verbose_name_plural': 'Notas'},
        ),
        migrations.AddField(
            model_name='nota',
            name='titulo',
            field=models.CharField(verbose_name='Título', max_length=100, default=''),
        ),
        migrations.AlterField(
            model_name='nota',
            name='texto',
            field=models.TextField(verbose_name='Texto'),
        ),
    ]
