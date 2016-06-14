# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lexml', '0002_auto_20150806_1614'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lexmlprovedor',
            name='email_responsavel',
            field=models.CharField(verbose_name='E-mail do responsável', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='lexmlprovedor',
            name='nome_responsavel',
            field=models.CharField(verbose_name='Nome do responsável', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='lexmlprovedor',
            name='xml',
            field=models.TextField(verbose_name='XML fornecido pela equipe do LexML:', blank=True),
        ),
        migrations.AlterField(
            model_name='lexmlpublicador',
            name='email_responsavel',
            field=models.CharField(verbose_name='E-mail do responsável', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='lexmlpublicador',
            name='nome_responsavel',
            field=models.CharField(verbose_name='Nome do responsável', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='lexmlpublicador',
            name='sigla',
            field=models.CharField(verbose_name='Sigla do Publicador', max_length=255, blank=True),
        ),
    ]
