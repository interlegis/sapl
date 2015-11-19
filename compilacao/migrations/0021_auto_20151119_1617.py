# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0020_auto_20151119_1126'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='perfilestruturaltextosnormativos',
            options={'verbose_name': 'Perfil Estrutural de Textos Normativos', 'verbose_name_plural': 'Perfis Estruturais de Textos Normativos', 'ordering': ['-padrao', 'sigla']},
        ),
        migrations.AddField(
            model_name='tipodispositivorelationship',
            name='permitir_variacao',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], verbose_name='Permitir Variação Numérica', default=True),
        ),
    ]
