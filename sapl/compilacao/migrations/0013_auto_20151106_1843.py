# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0012_auto_20151105_1658'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipodispositivo',
            name='relacoes_diretas_pai_filho',
            field=models.ManyToManyField(to='compilacao.TipoDispositivo', related_name='_relacoes_diretas_pai_filho_+', through='compilacao.TipoDispositivoRelationship'),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='filho_permitido',
            field=models.ForeignKey(null=True, blank=True, related_name='possiveis_pais', to='compilacao.TipoDispositivo', default=None),
        ),
    ]
