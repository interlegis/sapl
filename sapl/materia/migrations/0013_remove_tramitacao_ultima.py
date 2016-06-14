# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0012_auto_20151124_1328'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tramitacao',
            name='ultima',
        ),
    ]
