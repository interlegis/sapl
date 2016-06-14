# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import sapl.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_casalegislativa_codigo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casalegislativa',
            name='logotipo',
            field=models.FileField(
                null=True, upload_to=sapl.base.models.get_casa_media_path, verbose_name='Logotipo', blank=True),
        ),
    ]
