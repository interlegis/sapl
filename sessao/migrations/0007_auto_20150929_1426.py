# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0006_auto_20150929_1425'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sessaoplenariapresenca',
            old_name='sessao_plen',
            new_name='sessao_plenaria',
        ),
    ]
