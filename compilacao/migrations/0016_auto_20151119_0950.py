# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0015_auto_20151115_2310'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilEstruturalTextosNormativos',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
            ],
            options={
                'verbose_name_plural': 'Perfis Estruturais de Textos Normativos',
                'verbose_name': 'Perfil Estrutural de Textos Normativos',
            },
        ),
        migrations.RemoveField(
            model_name='dispositivo',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 19, 11, 49, 55, 455058, tzinfo=utc), auto_now_add=True, verbose_name='created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='modified',
            field=models.DateTimeField(auto_now=True, default=datetime.datetime(2015, 11, 19, 11, 50, 5, 86839, tzinfo=utc), verbose_name='modified'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tipodispositivorelationship',
            name='perfil',
            field=models.ForeignKey(blank=True, related_name='+', null=True, default=None, to='compilacao.PerfilEstruturalTextosNormativos'),
        ),
    ]
