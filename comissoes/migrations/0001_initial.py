# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CargoComissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Cargo')),
                ('unico', models.BooleanField(verbose_name='\xdanico')),
            ],
            options={
                'verbose_name': 'Cargo de Comiss\xe3o',
                'verbose_name_plural': 'Cargos de Comiss\xe3o',
            },
        ),
        migrations.CreateModel(
            name='Comissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('data_criacao', models.DateField(verbose_name='Data de Cria\xe7\xe3o')),
                ('data_extincao', models.DateField(null=True, verbose_name='Data de Extin\xe7\xe3o', blank=True)),
                ('apelido_temp', models.CharField(max_length=100, null=True, verbose_name='Apelido', blank=True)),
                ('data_instalacao_temp', models.DateField(null=True, verbose_name='Data Instala\xe7\xe3o', blank=True)),
                ('data_final_prevista_temp', models.DateField(null=True, verbose_name='Data Prevista T\xe9rmino', blank=True)),
                ('data_prorrogada_temp', models.DateField(null=True, verbose_name='Novo Prazo', blank=True)),
                ('data_fim_comissao', models.DateField(null=True, verbose_name='Data T\xe9rmino', blank=True)),
                ('secretario', models.CharField(max_length=30, null=True, verbose_name='Secret\xe1rio', blank=True)),
                ('telefone_reuniao', models.CharField(max_length=15, null=True, verbose_name='Tel. Sala Reuni\xe3o', blank=True)),
                ('endereco_secretaria', models.CharField(max_length=100, null=True, verbose_name='Endere\xe7o Secretaria', blank=True)),
                ('telefone_secretaria', models.CharField(max_length=15, null=True, verbose_name='Tel. Secretaria', blank=True)),
                ('fax_secretaria', models.CharField(max_length=15, null=True, verbose_name='Fax Secretaria', blank=True)),
                ('agenda_reuniao', models.CharField(max_length=100, null=True, verbose_name='Data/Hora Reuni\xe3o', blank=True)),
                ('local_reuniao', models.CharField(max_length=100, null=True, verbose_name='Local Reuni\xe3o', blank=True)),
                ('finalidade', models.TextField(null=True, verbose_name='Finalidade', blank=True)),
                ('email', models.CharField(max_length=100, null=True, verbose_name='E-mail', blank=True)),
                ('unidade_deliberativa', models.BooleanField()),
            ],
            options={
                'verbose_name': 'Comiss\xe3o',
                'verbose_name_plural': 'Comiss\xf5es',
            },
        ),
        migrations.CreateModel(
            name='Composicao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comissao', models.ForeignKey(verbose_name='Comiss\xe3o', to='comissoes.Comissao')),
            ],
            options={
                'verbose_name': 'Composi\xe7\xe3o de Comiss\xe3o',
                'verbose_name_plural': 'Composi\xe7\xf5es de Comiss\xe3o',
            },
        ),
        migrations.CreateModel(
            name='Participacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('titular', models.BooleanField(verbose_name='Titular')),
                ('data_designacao', models.DateField(verbose_name='Data Designa\xe7\xe3o')),
                ('data_desligamento', models.DateField(null=True, verbose_name='Data Desligamento', blank=True)),
                ('motivo_desligamento', models.CharField(max_length=150, null=True, verbose_name='Motivo Desligamento', blank=True)),
                ('observacao', models.CharField(max_length=150, null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('cargo', models.ForeignKey(to='comissoes.CargoComissao')),
                ('composicao', models.ForeignKey(to='comissoes.Composicao')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Participa\xe7\xe3o em Comiss\xe3o',
                'verbose_name_plural': 'Participa\xe7\xf5es em Comiss\xe3o',
            },
        ),
        migrations.CreateModel(
            name='Periodo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_inicio', models.DateField(verbose_name='Data In\xedcio')),
                ('data_fim', models.DateField(null=True, verbose_name='Data Fim', blank=True)),
            ],
            options={
                'verbose_name': 'Per\xedodo de composi\xe7\xe3o de Comiss\xe3o',
                'verbose_name_plural': 'Per\xedodos de composi\xe7\xe3o de Comiss\xe3o',
            },
        ),
        migrations.CreateModel(
            name='TipoComissao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('natureza', models.CharField(max_length=1, verbose_name='Natureza', choices=[(b'T', 'Tempor\xe1ria'), (b'P', 'Permanente')])),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('dispositivo_regimental', models.CharField(max_length=50, null=True, verbose_name='Dispositivo Regimental', blank=True)),
            ],
            options={
                'verbose_name': 'Tipo de Comiss\xe3o',
                'verbose_name_plural': 'Tipos de Comiss\xe3o',
            },
        ),
        migrations.AddField(
            model_name='composicao',
            name='periodo',
            field=models.ForeignKey(verbose_name='Per\xedodo', to='comissoes.Periodo'),
        ),
        migrations.AddField(
            model_name='comissao',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo', to='comissoes.TipoComissao'),
        ),
    ]
