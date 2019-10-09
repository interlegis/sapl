# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-10-09 18:50
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0047_merge_20191009_1535'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registroleitura',
            name='expediente',
        ),
        migrations.RemoveField(
            model_name='registroleitura',
            name='materia',
        ),
        migrations.RemoveField(
            model_name='registroleitura',
            name='ordem',
        ),
        migrations.RemoveField(
            model_name='registroleitura',
            name='user',
        ),
        migrations.AlterField(
            model_name='expedientemateria',
            name='tipo_votacao',
            field=models.PositiveIntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], default=1, verbose_name='Tipo de votação'),
        ),
        migrations.AlterField(
            model_name='ordemdia',
            name='tipo_votacao',
            field=models.PositiveIntegerField(choices=[(1, 'Simbólica'), (2, 'Nominal'), (3, 'Secreta')], default=1, verbose_name='Tipo de votação'),
        ),
        migrations.DeleteModel(
            name='RegistroLeitura',
        ),
    ]
