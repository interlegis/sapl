# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0038_auto_20151224_1429'),
        ('norma', '0008_normajuridica_texto_integral'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='normajuridica',
            options={'verbose_name': 'Norma Jurídica', 'verbose_name_plural': 'Normas Jurídicas'},
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='ano',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='data',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='ementa',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='id',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='numero',
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='observacao',
        ),
        migrations.AddField(
            model_name='normajuridica',
            name='textoarticulado_ptr',
            field=models.OneToOneField(to='compilacao.TextoArticulado', primary_key=True, parent_link=True, auto_created=True, default=1, serialize=False),
            preserve_default=False,
        ),
    ]
