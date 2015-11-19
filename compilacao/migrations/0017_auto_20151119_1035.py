# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0016_auto_20151119_0950'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilestruturaltextosnormativos',
            name='padrao',
            field=models.BooleanField(verbose_name='Padrão', choices=[(True, 'Sim'), (False, 'Não')], default=False),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='perfil',
            field=models.ForeignKey(to='compilacao.PerfilEstruturalTextosNormativos'),
        ),
        migrations.AlterUniqueTogether(
            name='tipodispositivorelationship',
            unique_together=set([('pai', 'filho_permitido', 'perfil')]),
        ),
    ]
