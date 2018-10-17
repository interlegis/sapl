# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2018-02-02 17:28
from __future__ import unicode_literals

from django.db import migrations
import image_cropping.fields


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0016_auto_20180202_1331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parlamentar',
            name='cropping',
            field=image_cropping.fields.ImageRatioField('fotografia', '128x128', adapt_rotation=False, allow_fullsize=False, free_crop=False, help_text='A configuração do Avatar é possível após a atualização da fotografia.', hide_image_field=False, size_warning=True, verbose_name='Avatar'),
        ),
    ]
