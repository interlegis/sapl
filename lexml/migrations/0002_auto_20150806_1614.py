# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lexml', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lexmlprovedor',
            name='id_provedor',
            field=models.PositiveIntegerField(verbose_name='Id do provedor'),
        ),
        migrations.AlterField(
            model_name='lexmlprovedor',
            name='id_responsavel',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Id do responsável'),
        ),
        migrations.AlterField(
            model_name='lexmlpublicador',
            name='id_publicador',
            field=models.PositiveIntegerField(verbose_name='Id do publicador'),
        ),
        migrations.AlterField(
            model_name='lexmlpublicador',
            name='id_responsavel',
            field=models.PositiveIntegerField(verbose_name='Id do responsável'),
        ),
    ]
