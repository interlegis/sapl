# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-08-12 23:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0031_auto_20200407_1406'),
        ('comissoes', '0025_auto_20200605_1051'),
    ]

    operations = [
        migrations.CreateModel(
            name='PresencaReuniaoComissao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parlamentar', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.Parlamentar')),
                ('reuniao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='presencareuniaocomissao_set', to='comissoes.Reuniao')),
            ],
            options={
                'verbose_name': 'Presença em Reunião de Comissão',
                'verbose_name_plural': 'Presenças em Reuniões de Comissão',
            },
        ),
    ]
