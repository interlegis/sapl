# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0038_auto_20151224_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textoarticulado',
            name='tipo_ta',
            field=models.ForeignKey(default=None, null=True, to='compilacao.TipoTextoArticulado', blank=True, verbose_name='Tipo de Texto Articulado'),
        ),
    ]
