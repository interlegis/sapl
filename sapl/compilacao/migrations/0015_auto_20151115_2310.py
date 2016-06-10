# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0014_auto_20151107_1836'),
    ]

    operations = [
        migrations.AddField(
            model_name='tipodispositivo',
            name='dispositivo_de_alteracao',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Dispositivo de Alteração'),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='filho_permitido',
            field=models.ForeignKey(related_name='possiveis_pais', to='compilacao.TipoDispositivo'),
        ),
    ]
