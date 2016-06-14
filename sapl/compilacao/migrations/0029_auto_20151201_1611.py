# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0028_auto_20151201_0042'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nota',
            name='publicidade',
            field=models.PositiveSmallIntegerField(verbose_name='Nível de Publicidade', choices=[(1, 'Nota Privada'), (2, 'Nota Institucional'), (3, 'Nota Pública')]),
        ),
    ]
