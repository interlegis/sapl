# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0011_auto_20160113_1239'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrovotacao',
            name='expediente',
            field=models.ForeignKey(blank=True, null=True, to='sessao.ExpedienteMateria'),
        ),
        migrations.AlterField(
            model_name='registrovotacao',
            name='ordem',
            field=models.ForeignKey(blank=True, null=True, to='sessao.OrdemDia'),
        ),
    ]
