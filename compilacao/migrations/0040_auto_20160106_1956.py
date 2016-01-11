# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('compilacao', '0039_auto_20151226_1433'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tipotextoarticulado',
            name='model',
        ),
        migrations.AddField(
            model_name='tipotextoarticulado',
            name='content_type',
            field=models.ForeignKey(verbose_name='Modelo Integrado', blank=True, default=None, null=True, to='contenttypes.ContentType'),
        ),
    ]
