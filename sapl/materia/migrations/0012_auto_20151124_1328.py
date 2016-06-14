# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0011_proposicao_texto_original'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proposicao',
            name='autor',
            field=models.ForeignKey(null=True, to='materia.Autor', blank=True),
        ),
    ]
