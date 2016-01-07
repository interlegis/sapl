# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_auto_20160107_1244'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casalegislativa',
            name='informacao_geral',
            field=models.CharField(verbose_name='Informação Geral', max_length=100, default=1),
            preserve_default=False,
        ),
    ]
