# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import parlamentares.models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0004_auto_20150929_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='parlamentar',
            name='fotografia',
            field=models.FileField(blank=True, null=True, verbose_name='Fotografia', upload_to=parlamentares.models.foto_upload_path),
        ),
    ]
