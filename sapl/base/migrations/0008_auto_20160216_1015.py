# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models, migrations
from django.utils.timezone import utc

import sapl.base.models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0007_auto_20160107_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casalegislativa',
            name='email',
            field=models.CharField(verbose_name='E-mail', max_length=100, default=datetime.datetime(
                2016, 2, 16, 12, 15, 30, 241941, tzinfo=utc), blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='endereco_web',
            field=models.CharField(
                verbose_name='HomePage', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='fax',
            field=models.CharField(
                verbose_name='Fax', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='informacao_geral',
            field=models.CharField(
                verbose_name='Informação Geral', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='logotipo',
            field=models.ImageField(
                verbose_name='Logotipo', upload_to=sapl.base.models.get_casa_media_path, blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='telefone',
            field=models.CharField(
                verbose_name='Telefone', max_length=100, blank=True),
        ),
    ]
