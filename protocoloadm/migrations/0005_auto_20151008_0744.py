# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import protocoloadm.models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0004_auto_20151007_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoacessorioadministrativo',
            name='arquivo',
            field=models.FileField(blank=True, null=True, upload_to=protocoloadm.models.texto_upload_path, verbose_name='Arquivo'),
        ),
    ]
