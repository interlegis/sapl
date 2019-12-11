# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-11-20 17:40
from __future__ import unicode_literals

from django.db import migrations, models
import sapl.comissoes.models
import sapl.utils


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0021_auto_20191001_1115'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoacessorio',
            name='arquivo',
            field=models.FileField(blank=True, max_length=300, null=True, storage=sapl.utils.OverwriteStorage(), upload_to=sapl.comissoes.models.anexo_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_txt], verbose_name='Texto Integral'),
        ),
        migrations.AlterField(
            model_name='documentoacessorio',
            name='autor',
            field=models.CharField(max_length=200, verbose_name='Autor'),
        ),
        migrations.AlterField(
            model_name='reuniao',
            name='upload_anexo',
            field=models.FileField(blank=True, max_length=300, null=True, storage=sapl.utils.OverwriteStorage(), upload_to=sapl.comissoes.models.anexo_upload_path, verbose_name='Anexo da Reunião'),
        ),
        migrations.AlterField(
            model_name='reuniao',
            name='upload_ata',
            field=models.FileField(blank=True, max_length=300, null=True, storage=sapl.utils.OverwriteStorage(), upload_to=sapl.comissoes.models.ata_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_txt], verbose_name='Ata da Reunião'),
        ),
        migrations.AlterField(
            model_name='reuniao',
            name='upload_pauta',
            field=models.FileField(blank=True, max_length=300, null=True, storage=sapl.utils.OverwriteStorage(), upload_to=sapl.comissoes.models.pauta_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_txt], verbose_name='Pauta da Reunião'),
        ),
    ]
