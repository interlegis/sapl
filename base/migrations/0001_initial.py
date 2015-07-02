# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CasaLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cod_casa', models.CharField(max_length=100, verbose_name='C\xf3digo')),
                ('nom_casa', models.CharField(max_length=100, verbose_name='Nome')),
                ('sgl_casa', models.CharField(max_length=100, verbose_name='Sigla')),
                ('end_casa', models.CharField(max_length=100, verbose_name='Endere\xe7o')),
                ('num_cep', models.CharField(max_length=100, verbose_name='CEP')),
                ('municipio', models.CharField(max_length=100, verbose_name='Munic\xedpio')),
                ('sgl_uf', models.CharField(max_length=100, verbose_name='UF')),
                ('num_tel', models.CharField(max_length=100, verbose_name='Telefone')),
                ('num_fax', models.CharField(max_length=100, verbose_name='Fax')),
                ('txt_senha_inicial', models.CharField(max_length=100, verbose_name='Senha')),
                ('cor_fundo', models.CharField(max_length=100, verbose_name='Cor de fundo')),
                ('cor_borda', models.CharField(max_length=100, verbose_name='Cor da borda')),
                ('cor_principal', models.CharField(max_length=100, verbose_name='Cor principal')),
                ('nom_logo', models.CharField(max_length=100, verbose_name='Logotipo')),
                ('end_web_casa', models.CharField(max_length=100, verbose_name='HomePage')),
                ('end_email_casa', models.CharField(max_length=100, verbose_name='E-mail')),
                ('informacao_geral', models.CharField(max_length=100, verbose_name='Informa\xe7\xe3o Geral')),
            ],
            options={
                'verbose_name': 'Casa Legislativa',
                'verbose_name_plural': 'Casas Legislativas',
            },
        ),
    ]
