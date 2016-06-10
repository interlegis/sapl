# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0006_proposicao_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposicao',
            name='status',
            field=models.CharField(max_length=1, verbose_name='Status Proposição', blank=True, null=True, choices=[('E', 'Enviada'), ('D', 'Devolvida'), ('I', 'Incorporada')]),
        ),
    ]
