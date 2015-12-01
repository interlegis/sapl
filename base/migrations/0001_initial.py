# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CasaLegislativa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=100, verbose_name='Sigla')),
                ('endereco', models.CharField(max_length=100, verbose_name='Endereço')),
                ('cep', models.CharField(max_length=100, verbose_name='CEP')),
                ('municipio', models.CharField(max_length=100, verbose_name='Município')),
                ('uf', models.CharField(max_length=100, verbose_name='UF')),
                ('telefone', models.CharField(max_length=100, verbose_name='Telefone')),
                ('fax', models.CharField(max_length=100, verbose_name='Fax')),
                ('cor_fundo', models.CharField(max_length=100, verbose_name='Cor de fundo')),
                ('cor_borda', models.CharField(max_length=100, verbose_name='Cor da borda')),
                ('cor_principal', models.CharField(max_length=100, verbose_name='Cor principal')),
                ('logotipo', models.CharField(max_length=100, verbose_name='Logotipo')),
                ('endereco_web', models.CharField(max_length=100, verbose_name='HomePage')),
                ('email', models.CharField(max_length=100, verbose_name='E-mail')),
                ('informacao_geral', models.CharField(max_length=100, verbose_name='Informação Geral')),
            ],
            options={
                'verbose_name_plural': 'Casas Legislativas',
                'verbose_name': 'Casa Legislativa',
            },
        ),
    ]
