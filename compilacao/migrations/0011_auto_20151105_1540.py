# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0010_auto_20151105_1532'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tipodispositivorelationship',
            options={'verbose_name': 'Relação Direta Permitida', 'verbose_name_plural': 'Relaçõe Diretas Permitidas', 'ordering': ['pai', 'filho_permitido']},
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='filho_permitido',
            field=models.ForeignKey(null=True, to='compilacao.TipoDispositivo', blank=True, default=None, related_name='filho_permitido'),
        ),
        migrations.AlterUniqueTogether(
            name='tipodispositivorelationship',
            unique_together=set([('pai', 'filho_permitido')]),
        ),
    ]
