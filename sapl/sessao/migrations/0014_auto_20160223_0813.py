# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0013_auto_20160216_1015'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='acompanharmateria',
            name='materia_cadastrada',
        ),
        migrations.DeleteModel(
            name='AcompanharMateria',
        ),
    ]
