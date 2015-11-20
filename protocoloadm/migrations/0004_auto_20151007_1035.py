# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import protocoloadm.models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0003_documentoacessorioadministrativo_texto_integral'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentoacessorioadministrativo',
            name='texto_integral',
        ),
        migrations.AddField(
            model_name='documentoadministrativo',
            name='texto_integral',
            field=models.FileField(blank=True, null=True, upload_to=protocoloadm.models.texto_upload_path, verbose_name='Texto Integral'),
        ),
    ]
