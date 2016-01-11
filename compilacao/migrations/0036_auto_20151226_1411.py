# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0035_auto_20151226_1349'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textoarticulado',
            name='content_type',
            field=models.ForeignKey(default=None, null=True, to='contenttypes.ContentType', blank=True),
        ),
    ]
