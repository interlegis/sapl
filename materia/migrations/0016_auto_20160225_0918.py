# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0015_auto_20160216_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tramitacao',
            name='turno',
            field=models.CharField(max_length=1, verbose_name='Turno', choices=[('P', 'Primeiro'), ('S', 'Segundo'), ('U', 'Único'), ('L', 'Suplementar'), ('F', 'Final'), ('A', 'Votação única em Regime de Urgência'), ('B', '1ª Votação'), ('C', '2ª e 3ª Votação')], blank=True),
        ),
    ]
