# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-10-23 15:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0026_auto_20181016_1944'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='finalizada',
            field=models.NullBooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Sessão finalizada?'),
        ),
        migrations.AlterField(
            model_name='sessaoplenaria',
            name='iniciada',
            field=models.NullBooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=True, verbose_name='Sessão iniciada?'),
        ),
    ]
