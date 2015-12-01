# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0006_auto_20151025_1427'),
    ]

    operations = [
        migrations.AlterField(
            model_name='normajuridica',
            name='complemento',
            field=models.NullBooleanField(verbose_name='Complementar ?', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
    ]
