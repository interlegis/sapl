# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import materia.models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0009_auto_20151029_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='materialegislativa',
            name='texto_original',
            field=models.FileField(verbose_name='Texto Original (PDF)', upload_to=materia.models.texto_upload_path, blank=True, null=True),
        ),
    ]
