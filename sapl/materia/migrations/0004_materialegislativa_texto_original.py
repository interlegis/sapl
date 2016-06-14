# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import sapl.materia.models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0003_auto_20150729_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='materialegislativa',
            name='texto_original',
            field=models.FileField(
                null=True, blank=True, verbose_name='Texto original (PDF)', upload_to=sapl.materia.models.texto_upload_path),
        ),
    ]
