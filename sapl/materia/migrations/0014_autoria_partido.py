# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0010_auto_20160107_1850'),
        ('materia', '0013_remove_tramitacao_ultima'),
    ]

    operations = [
        migrations.AddField(
            model_name='autoria',
            name='partido',
            field=models.ForeignKey(null=True, to='parlamentares.Partido', blank=True),
        ),
    ]
