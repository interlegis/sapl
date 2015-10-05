# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0007_auto_20150929_1426'),
    ]

    operations = [
        migrations.AddField(
            model_name='expedientemateria',
            name='votacao_iniciada',
            field=models.NullBooleanField(choices=[(True, 'Sim'), (False, 'Não')], verbose_name='Votação iniciada?'),
        ),
        migrations.AddField(
            model_name='ordemdia',
            name='votacao_iniciada',
            field=models.NullBooleanField(choices=[(True, 'Sim'), (False, 'Não')], verbose_name='Votação iniciada?'),
        ),
    ]
