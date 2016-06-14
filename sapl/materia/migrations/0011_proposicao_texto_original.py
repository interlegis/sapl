# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import sapl.materia.models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0010_auto_20151117_1551'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposicao',
            name='texto_original',
            field=models.FileField(upload_to=sapl.materia.models.texto_upload_path,
                                   verbose_name='Texto Original (PDF)', blank=True, null=True),
        ),
    ]
