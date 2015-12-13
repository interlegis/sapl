# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0029_auto_20151201_1611'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipodispositivo',
            name='relacoes_diretas_pai_filho',
            field=models.ManyToManyField(to='compilacao.TipoDispositivo', through='compilacao.TipoDispositivoRelationship', related_name='+'),
        ),
    ]
