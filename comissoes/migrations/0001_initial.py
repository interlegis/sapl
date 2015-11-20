# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CargoComissao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=50, verbose_name='Cargo')),
                ('unico', models.BooleanField(verbose_name='Único')),
            ],
            options={
                'verbose_name_plural': 'Cargos de Comissão',
                'verbose_name': 'Cargo de Comissão',
            },
        ),
        migrations.CreateModel(
            name='Comissao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('data_criacao', models.DateField(verbose_name='Data de Criação')),
                ('data_extincao', models.DateField(blank=True, null=True, verbose_name='Data de Extinção')),
                ('apelido_temp', models.CharField(blank=True, max_length=100, null=True, verbose_name='Apelido')),
                ('data_instalacao_temp', models.DateField(blank=True, null=True, verbose_name='Data Instalação')),
                ('data_final_prevista_temp', models.DateField(blank=True, null=True, verbose_name='Data Prevista Término')),
                ('data_prorrogada_temp', models.DateField(blank=True, null=True, verbose_name='Novo Prazo')),
                ('data_fim_comissao', models.DateField(blank=True, null=True, verbose_name='Data Término')),
                ('secretario', models.CharField(blank=True, max_length=30, null=True, verbose_name='Secretário')),
                ('telefone_reuniao', models.CharField(blank=True, max_length=15, null=True, verbose_name='Tel. Sala Reunião')),
                ('endereco_secretaria', models.CharField(blank=True, max_length=100, null=True, verbose_name='Endereço Secretaria')),
                ('telefone_secretaria', models.CharField(blank=True, max_length=15, null=True, verbose_name='Tel. Secretaria')),
                ('fax_secretaria', models.CharField(blank=True, max_length=15, null=True, verbose_name='Fax Secretaria')),
                ('agenda_reuniao', models.CharField(blank=True, max_length=100, null=True, verbose_name='Data/Hora Reunião')),
                ('local_reuniao', models.CharField(blank=True, max_length=100, null=True, verbose_name='Local Reunião')),
                ('finalidade', models.TextField(blank=True, null=True, verbose_name='Finalidade')),
                ('email', models.CharField(blank=True, max_length=100, null=True, verbose_name='E-mail')),
                ('unidade_deliberativa', models.BooleanField(verbose_name='Unidade Deliberativa', choices=[(True, 'Sim'), (False, 'Não')])),
            ],
            options={
                'verbose_name_plural': 'Comissões',
                'verbose_name': 'Comissão',
            },
        ),
        migrations.CreateModel(
            name='Composicao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('comissao', models.ForeignKey(to='comissoes.Comissao', verbose_name='Comissão')),
            ],
            options={
                'verbose_name_plural': 'Composições de Comissão',
                'verbose_name': 'Composição de Comissão',
            },
        ),
        migrations.CreateModel(
            name='Participacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('titular', models.BooleanField(verbose_name='Titular')),
                ('data_designacao', models.DateField(verbose_name='Data Designação')),
                ('data_desligamento', models.DateField(blank=True, null=True, verbose_name='Data Desligamento')),
                ('motivo_desligamento', models.CharField(blank=True, max_length=150, null=True, verbose_name='Motivo Desligamento')),
                ('observacao', models.CharField(blank=True, max_length=150, null=True, verbose_name='Observação')),
                ('cargo', models.ForeignKey(to='comissoes.CargoComissao')),
                ('composicao', models.ForeignKey(to='comissoes.Composicao')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Participações em Comissão',
                'verbose_name': 'Participação em Comissão',
            },
        ),
        migrations.CreateModel(
            name='Periodo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(blank=True, null=True, verbose_name='Data Fim')),
            ],
            options={
                'verbose_name_plural': 'Períodos de composição de Comissão',
                'verbose_name': 'Período de composição de Comissão',
            },
        ),
        migrations.CreateModel(
            name='TipoComissao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('natureza', models.CharField(choices=[('T', 'Temporária'), ('P', 'Permanente')], max_length=1, verbose_name='Natureza')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('dispositivo_regimental', models.CharField(blank=True, max_length=50, null=True, verbose_name='Dispositivo Regimental')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Comissão',
                'verbose_name': 'Tipo de Comissão',
            },
        ),
        migrations.AddField(
            model_name='composicao',
            name='periodo',
            field=models.ForeignKey(to='comissoes.Periodo', verbose_name='Período'),
        ),
        migrations.AddField(
            model_name='comissao',
            name='tipo',
            field=models.ForeignKey(to='comissoes.TipoComissao', verbose_name='Tipo'),
        ),
    ]
