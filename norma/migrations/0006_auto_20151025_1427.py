# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0005_auto_20150915_1141'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='normajuridica',
            options={'ordering': ['-data', '-numero'], 'verbose_name_plural': 'Normas Jurídicas', 'verbose_name': 'Norma Jurídica'},
        ),
    ]
