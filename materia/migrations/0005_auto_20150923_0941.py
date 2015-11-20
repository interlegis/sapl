# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0004_materialegislativa_texto_original'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='materialegislativa',
            unique_together=set([('tipo', 'numero', 'ano')]),
        ),
    ]
