# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0002_auto_20150729_1717'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssuntoNormaRelationship',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('assunto', models.ForeignKey(to='norma.AssuntoNorma')),
            ],
        ),
        migrations.RemoveField(
            model_name='normajuridica',
            name='assunto',
        ),
        migrations.AddField(
            model_name='assuntonormarelationship',
            name='norma',
            field=models.ForeignKey(to='norma.NormaJuridica'),
        ),
        migrations.AddField(
            model_name='normajuridica',
            name='assuntos',
            field=models.ManyToManyField(to='norma.AssuntoNorma', through='norma.AssuntoNormaRelationship'),
        ),
    ]
