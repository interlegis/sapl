# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0005_remove_presencaordemdia_data_ordem'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expedientemateria',
            options={'ordering': ['numero_ordem'], 'verbose_name': 'Matéria do Expediente', 'verbose_name_plural': 'Matérias do Expediente'},
        ),
        migrations.AlterModelOptions(
            name='ordemdia',
            options={'ordering': ['numero_ordem'], 'verbose_name': 'Matéria da Ordem do Dia', 'verbose_name_plural': 'Matérias da Ordem do Dia'},
        ),
        migrations.AlterModelOptions(
            name='presencaordemdia',
            options={'ordering': ['parlamentar__nome_parlamentar'], 'verbose_name': 'Presença da Ordem do Dia', 'verbose_name_plural': 'Presenças da Ordem do Dia'},
        ),
        migrations.AlterModelOptions(
            name='sessaoplenariapresenca',
            options={'ordering': ['parlamentar__nome_parlamentar'], 'verbose_name': 'Presença em Sessão Plenária', 'verbose_name_plural': 'Presenças em Sessões Plenárias'},
        ),
    ]
