# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0016_auto_20160223_0813'),
    ]

    operations = [
        migrations.AddField(
            model_name='acompanhamentomateria',
            name='confirmado',
            field=models.BooleanField(default=False),
        ),
    ]
