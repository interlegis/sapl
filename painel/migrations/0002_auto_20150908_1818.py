# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('painel', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='painel',
            name='abrir',
        ),
        migrations.RemoveField(
            model_name='painel',
            name='fechar',
        ),
        migrations.AddField(
            model_name='painel',
            name='aberto',
            field=models.BooleanField(verbose_name='Abrir painel', default=False),
        ),
    ]
