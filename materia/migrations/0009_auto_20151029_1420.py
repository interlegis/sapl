# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0008_auto_20151029_1416'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='numeracao',
            name='numero_ordem',
        )
    ]
