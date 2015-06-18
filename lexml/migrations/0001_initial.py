# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LexmlRegistroProvedor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('id_provedor', models.IntegerField()),
                ('nome_provedor', models.CharField(max_length=255)),
                ('sigla_provedor', models.CharField(max_length=15)),
                ('adm_email', models.CharField(max_length=50, null=True, blank=True)),
                ('nome_responsavel', models.CharField(max_length=255, null=True, blank=True)),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(null=True, blank=True)),
                ('xml_provedor', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LexmlRegistroPublicador',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('id_publicador', models.IntegerField()),
                ('nome_publicador', models.CharField(max_length=255)),
                ('adm_email', models.CharField(max_length=50, null=True, blank=True)),
                ('sigla', models.CharField(max_length=255, null=True, blank=True)),
                ('nome_responsavel', models.CharField(max_length=255, null=True, blank=True)),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField()),
            ],
        ),
    ]
