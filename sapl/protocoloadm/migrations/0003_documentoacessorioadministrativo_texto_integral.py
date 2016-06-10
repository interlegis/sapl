# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import sapl.protocoloadm.models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0002_auto_20150729_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='texto_integral',
            field=models.FileField(verbose_name='Texto Integral', blank=True,
                                   null=True, upload_to=sapl.protocoloadm.models.texto_upload_path),
        ),
    ]
