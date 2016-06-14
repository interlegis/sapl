# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sapl.norma.models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0007_auto_20151130_1632'),
    ]

    operations = [
        migrations.AddField(
            model_name='normajuridica',
            name='texto_integral',
            field=models.FileField(
                null=True, verbose_name='Texto Integral', upload_to=sapl.norma.models.texto_upload_path, blank=True),
        ),
    ]
