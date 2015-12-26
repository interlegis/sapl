# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import builtins

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('compilacao', '0034_auto_20151226_1321'),
    ]

    operations = [
        migrations.AddField(
            model_name='textoarticulado',
            name='content_type',
            field=models.ForeignKey(
                to='contenttypes.ContentType', default=142),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='textoarticulado',
            name='object_id',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
