# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0008_auto_20151005_1023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipodispositivo',
            name='rotulo_ordinal',
            field=models.IntegerField(choices=[(0, 'Numeração Cardinal.'), (-1, 'Numeração Ordinal.'), (9, 'Numeração Ordinal até o item nove.')], verbose_name='Tipo de número do rótulo'),
        ),
        migrations.AlterUniqueTogether(
            name='dispositivo',
            unique_together=set([('norma', 'ordem'), ('norma', 'dispositivo0', 'dispositivo1', 'dispositivo2', 'dispositivo3', 'dispositivo4', 'dispositivo5', 'tipo_dispositivo', 'dispositivo_pai', 'norma_publicada', 'publicacao')]),
        ),
    ]
