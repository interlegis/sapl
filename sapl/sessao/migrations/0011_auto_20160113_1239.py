# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0010_acompanharmateria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acompanharmateria',
            name='usuario',
            field=models.CharField(max_length=50),
        ),
    ]
