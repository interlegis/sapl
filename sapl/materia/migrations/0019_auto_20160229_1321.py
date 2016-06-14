# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0018_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='materialegislativa',
            name='anexadas',
            field=models.ManyToManyField(to='materia.MateriaLegislativa', blank=True, related_name='anexo_de', through='materia.Anexada'),
        ),
    ]
