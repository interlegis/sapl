# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0004_auto_20150907_0004'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='normajuridica',
            options={'verbose_name_plural': 'Normas Jurídicas', 'verbose_name': 'Norma Jurídica', 'ordering': ['-data']},
        ),
    ]
