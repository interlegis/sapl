# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0009_auto_20151007_1635'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoDispositivoRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('filho_permitido', models.ForeignKey(related_name='filho_permitido', to='compilacao.TipoDispositivo')),
                ('pai', models.ForeignKey(related_name='pai', to='compilacao.TipoDispositivo')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='tipodispositivo',
            name='relacoes_diretas_pai_filho',
            field=models.ManyToManyField(related_name='filhos_permitidos', through='compilacao.TipoDispositivoRelationship', to='compilacao.TipoDispositivo'),
        ),
    ]
