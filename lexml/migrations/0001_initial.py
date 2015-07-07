# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LexmlProvedor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('id_provedor', models.IntegerField(verbose_name='Id do provedor')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do provedor')),
                ('sigla', models.CharField(max_length=15)),
                ('email_responsavel', models.CharField(max_length=50, null=True, verbose_name='E-mail do respons\xe1vel', blank=True)),
                ('nome_responsavel', models.CharField(max_length=255, null=True, verbose_name='Nome do respons\xe1vel', blank=True)),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(null=True, verbose_name='Id do respons\xe1vel', blank=True)),
                ('xml', models.TextField(null=True, verbose_name='XML fornecido pela equipe do LexML:', blank=True)),
            ],
            options={
                'verbose_name': 'Provedor Lexml',
                'verbose_name_plural': 'Provedores Lexml',
            },
        ),
        migrations.CreateModel(
            name='LexmlPublicador',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('id_publicador', models.IntegerField(verbose_name='Id do publicador')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome do publicador')),
                ('email_responsavel', models.CharField(max_length=50, null=True, verbose_name='E-mail do respons\xe1vel', blank=True)),
                ('sigla', models.CharField(max_length=255, null=True, verbose_name='Sigla do Publicador', blank=True)),
                ('nome_responsavel', models.CharField(max_length=255, null=True, verbose_name='Nome do respons\xe1vel', blank=True)),
                ('tipo', models.CharField(max_length=50)),
                ('id_responsavel', models.IntegerField(verbose_name='Id do respons\xe1vel')),
            ],
            options={
                'verbose_name': 'Publicador Lexml',
                'verbose_name_plural': 'Publicadores Lexml',
            },
        ),
    ]
