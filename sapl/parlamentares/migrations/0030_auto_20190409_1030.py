# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-09 13:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import sapl.parlamentares.models
import sapl.utils


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0029_historicopartido_proximo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='historicopartido',
            old_name='data_alteracao',
            new_name='fim_historico',
        ),
        migrations.AddField(
            model_name='historicopartido',
            name='inicio_historico',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='Data Alteração'),
        ),
        migrations.AddField(
            model_name='historicopartido',
            name='logo_partido',
            field=models.ImageField(blank=True, null=True, upload_to=sapl.parlamentares.models.logo_upload_path, validators=[sapl.utils.restringe_tipos_de_arquivo_img], verbose_name='Logo Partido'),
        ),
    ]
