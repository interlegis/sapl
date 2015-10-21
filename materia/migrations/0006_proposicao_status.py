# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0005_auto_20150923_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposicao',
            name='status',
            field=models.CharField(verbose_name='Status Proposição', max_length=1, blank=True, choices=[('P', 'Pendente'), ('D', 'Devolvida'), ('I', 'Incorporada')], null=True),
        ),
    ]
