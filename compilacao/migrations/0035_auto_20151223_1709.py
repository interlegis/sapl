# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0034_auto_20151222_1609'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoTextoArticulado',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=3, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Texto Articulados',
                'verbose_name': 'Tipo de Texto Articulado',
            },
        ),
        migrations.AddField(
            model_name='textoarticulado',
            name='tipo_ta',
            field=models.ForeignKey(to='compilacao.TipoTextoArticulado', default=1, verbose_name='Tipo de Texto Articulado'),
            preserve_default=False,
        ),
    ]
