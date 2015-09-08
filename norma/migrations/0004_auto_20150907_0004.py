# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0003_auto_20150906_0239'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='assuntonormarelationship',
            unique_together=set([('assunto', 'norma')]),
        ),
    ]
