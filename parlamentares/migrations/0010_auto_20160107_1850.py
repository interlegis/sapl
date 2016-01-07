# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import parlamentares.models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0009_auto_20151126_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parlamentar',
            name='fotografia',
            field=models.ImageField(null=True, verbose_name='Fotografia', blank=True, upload_to=parlamentares.models.foto_upload_path),
        ),
    ]
