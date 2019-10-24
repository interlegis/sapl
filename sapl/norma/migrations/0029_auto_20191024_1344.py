# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-10-24 16:44
from __future__ import unicode_literals

from django.db import migrations, models
import sapl.norma.models
import sapl.utils


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0028_auto_20191024_1330'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anexonormajuridica',
            name='anexo_arquivo',
            field=models.FileField(blank=True, max_length=300, null=True, storage=sapl.utils.OverwriteStorage(), upload_to=sapl.norma.models.norma_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_txt], verbose_name='Arquivo Anexo'),
        ),
    ]
