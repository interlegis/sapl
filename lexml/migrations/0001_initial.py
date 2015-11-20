# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LexmlProvedor',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('id_provedor', models.IntegerField(verbose_name='Id do provedor')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do provedor')),
                ('sigla', models.CharField(max_length=15)),
                ('email_responsavel', models.CharField(blank=True, max_length=50, null=True, verbose_name='E-mail do responsável')),
                ('nome_responsavel', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome do responsável')),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(blank=True, null=True, verbose_name='Id do responsável')),
                ('xml', models.TextField(blank=True, null=True, verbose_name='XML fornecido pela equipe do LexML:')),
            ],
            options={
                'verbose_name_plural': 'Provedores Lexml',
                'verbose_name': 'Provedor Lexml',
            },
        ),
        migrations.CreateModel(
            name='LexmlPublicador',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('id_publicador', models.IntegerField(verbose_name='Id do publicador')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do publicador')),
                ('email_responsavel', models.CharField(blank=True, max_length=50, null=True, verbose_name='E-mail do responsável')),
                ('sigla', models.CharField(blank=True, max_length=255, null=True, verbose_name='Sigla do Publicador')),
                ('nome_responsavel', models.CharField(blank=True, max_length=255, null=True, verbose_name='Nome do responsável')),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(verbose_name='Id do responsável')),
            ],
            options={
                'verbose_name_plural': 'Publicadores Lexml',
                'verbose_name': 'Publicador Lexml',
            },
        ),
    ]
