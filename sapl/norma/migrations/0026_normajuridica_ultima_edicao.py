# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-08-02 19:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0025_auto_20190704_1403'),
    ]

    operations = [
        migrations.AddField(
            model_name='normajuridica',
            name='ultima_edicao',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data e Hora da Edição'),
        ),
    ]
