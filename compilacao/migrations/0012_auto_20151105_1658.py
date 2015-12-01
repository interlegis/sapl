# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0011_auto_20151105_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipodispositivorelationship',
            name='filho_de_insercao_automatica',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Filho de Inserção Automática'),
        ),
        migrations.AlterField(
            model_name='tipodispositivo',
            name='relacoes_diretas_pai_filho',
            field=models.ManyToManyField(to='compilacao.TipoDispositivo', related_name='possiveis_pais', through='compilacao.TipoDispositivoRelationship'),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='filho_permitido',
            field=models.ForeignKey(blank=True, default=None, null=True, related_name='pais', to='compilacao.TipoDispositivo'),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='pai',
            field=models.ForeignKey(to='compilacao.TipoDispositivo', related_name='filhos_permitidos'),
        ),
    ]
