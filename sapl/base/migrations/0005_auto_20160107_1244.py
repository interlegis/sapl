# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_auto_20160107_1158'),
    ]

    operations = [
        migrations.AlterField(
            model_name='casalegislativa',
            name='email',
            field=models.CharField(max_length=100, null=True, verbose_name='E-mail', blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='endereco_web',
            field=models.CharField(max_length=100, null=True, verbose_name='HomePage', blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='fax',
            field=models.CharField(max_length=100, null=True, verbose_name='Fax', blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='informacao_geral',
            field=models.CharField(max_length=100, null=True, verbose_name='Informação Geral', blank=True),
        ),
        migrations.AlterField(
            model_name='casalegislativa',
            name='telefone',
            field=models.CharField(max_length=100, null=True, verbose_name='Telefone', blank=True),
        ),
    ]
