# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargocomissao',
            name='unico',
            field=models.BooleanField(verbose_name='Único', choices=[(True, 'Sim'), (False, 'Não')]),
        ),
    ]
