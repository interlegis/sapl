# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0024_auto_20151120_1814'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nota',
            old_name='efetifidade',
            new_name='efetividade',
        ),
        migrations.AlterField(
            model_name='nota',
            name='dispositivo',
            field=models.ForeignKey(to='compilacao.Dispositivo', related_name='notas', verbose_name='Dispositivo da Nota'),
        ),
    ]
