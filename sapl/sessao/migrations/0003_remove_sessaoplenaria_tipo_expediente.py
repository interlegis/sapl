# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0002_auto_20150729_1450'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessaoplenaria',
            name='tipo_expediente',
        ),
    ]
