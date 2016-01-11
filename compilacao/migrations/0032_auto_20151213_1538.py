# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0031_merge'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='vide',
            unique_together=set(
                [('dispositivo_base', 'dispositivo_ref', 'tipo')]),
        ),
    ]
