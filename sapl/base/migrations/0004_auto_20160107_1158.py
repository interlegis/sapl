# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_auto_20160107_1122'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='casalegislativa',
            name='cor_borda',
        ),
        migrations.RemoveField(
            model_name='casalegislativa',
            name='cor_fundo',
        ),
        migrations.RemoveField(
            model_name='casalegislativa',
            name='cor_principal',
        ),
    ]
