# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0006_auto_20160216_1015'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentoadministrativo',
            name='tramitacao',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], verbose_name='Em Tramitação?'),
        ),
    ]
