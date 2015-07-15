# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LexmlProvedor',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('id_provedor', models.IntegerField(verbose_name='Id do provedor')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do provedor')),
                ('sigla', models.CharField(max_length=15)),
                ('email_responsavel', models.CharField(max_length=50, blank=True, verbose_name='E-mail do responsável', null=True)),
                ('nome_responsavel', models.CharField(max_length=255, blank=True, verbose_name='Nome do responsável', null=True)),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(blank=True, verbose_name='Id do responsável', null=True)),
                ('xml', models.TextField(blank=True, verbose_name='XML fornecido pela equipe do LexML:', null=True)),
            ],
            options={
                'verbose_name': 'Provedor Lexml',
                'verbose_name_plural': 'Provedores Lexml',
            },
        ),
        migrations.CreateModel(
            name='LexmlPublicador',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('id_publicador', models.IntegerField(verbose_name='Id do publicador')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do publicador')),
                ('email_responsavel', models.CharField(max_length=50, blank=True, verbose_name='E-mail do responsável', null=True)),
                ('sigla', models.CharField(max_length=255, blank=True, verbose_name='Sigla do Publicador', null=True)),
                ('nome_responsavel', models.CharField(max_length=255, blank=True, verbose_name='Nome do responsável', null=True)),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(verbose_name='Id do responsável')),
            ],
            options={
                'verbose_name': 'Publicador Lexml',
                'verbose_name_plural': 'Publicadores Lexml',
            },
        ),
    ]
