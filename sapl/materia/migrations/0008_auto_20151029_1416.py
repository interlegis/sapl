# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0007_auto_20151021_1200'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='despachoinicial',
            name='numero_ordem',
        )
    ]
