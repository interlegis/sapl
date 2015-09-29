# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0003_auto_20150729_1717'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='parlamentar',
            options={'ordering': ['nome_parlamentar'], 'verbose_name': 'Parlamentar', 'verbose_name_plural': 'Parlamentares'},
        ),
    ]
