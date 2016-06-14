# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='casalegislativa',
            name='codigo',
            field=models.CharField(verbose_name='Codigo', default=1, max_length=100),
            preserve_default=False,
        ),
    ]
