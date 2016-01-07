# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import base.models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_auto_20160107_1257'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casalegislativa',
            name='informacao_geral',
            field=models.CharField(blank=True, max_length=100, verbose_name='Informação Geral', null=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='logotipo',
            field=models.ImageField(blank=True, upload_to=base.models.get_casa_media_path, verbose_name='Logotipo', null=True),
        ),
    ]
