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
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Cargo')),
                ('unico', models.BooleanField(verbose_name='Único')),
            ],
            options={
                'verbose_name': 'Cargo de Comissão',
                'verbose_name_plural': 'Cargos de Comissão',
            },
        ),
        migrations.CreateModel(
            name='Comissao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('data_criacao', models.DateField(verbose_name='Data de Criação')),
                ('data_extincao', models.DateField(blank=True, verbose_name='Data de Extinção', null=True)),
                ('apelido_temp', models.CharField(max_length=100, blank=True, verbose_name='Apelido', null=True)),
                ('data_instalacao_temp', models.DateField(blank=True, verbose_name='Data Instalação', null=True)),
                ('data_final_prevista_temp', models.DateField(blank=True, verbose_name='Data Prevista Término', null=True)),
                ('data_prorrogada_temp', models.DateField(blank=True, verbose_name='Novo Prazo', null=True)),
                ('data_fim_comissao', models.DateField(blank=True, verbose_name='Data Término', null=True)),
                ('secretario', models.CharField(max_length=30, blank=True, verbose_name='Secretário', null=True)),
                ('telefone_reuniao', models.CharField(max_length=15, blank=True, verbose_name='Tel. Sala Reunião', null=True)),
                ('endereco_secretaria', models.CharField(max_length=100, blank=True, verbose_name='Endereço Secretaria', null=True)),
                ('telefone_secretaria', models.CharField(max_length=15, blank=True, verbose_name='Tel. Secretaria', null=True)),
                ('fax_secretaria', models.CharField(max_length=15, blank=True, verbose_name='Fax Secretaria', null=True)),
                ('agenda_reuniao', models.CharField(max_length=100, blank=True, verbose_name='Data/Hora Reunião', null=True)),
                ('local_reuniao', models.CharField(max_length=100, blank=True, verbose_name='Local Reunião', null=True)),
                ('finalidade', models.TextField(blank=True, verbose_name='Finalidade', null=True)),
                ('email', models.CharField(max_length=100, blank=True, verbose_name='E-mail', null=True)),
                ('unidade_deliberativa', models.BooleanField()),
            ],
            options={
                'verbose_name': 'Comissão',
                'verbose_name_plural': 'Comissões',
            },
        ),
        migrations.CreateModel(
            name='Composicao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('comissao', models.ForeignKey(to='comissoes.Comissao', verbose_name='Comissão')),
            ],
            options={
                'verbose_name': 'Composição de Comissão',
                'verbose_name_plural': 'Composições de Comissão',
            },
        ),
        migrations.CreateModel(
            name='Participacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('titular', models.BooleanField(verbose_name='Titular')),
                ('data_designacao', models.DateField(verbose_name='Data Designação')),
                ('data_desligamento', models.DateField(blank=True, verbose_name='Data Desligamento', null=True)),
                ('motivo_desligamento', models.CharField(max_length=150, blank=True, verbose_name='Motivo Desligamento', null=True)),
                ('observacao', models.CharField(max_length=150, blank=True, verbose_name='Observação', null=True)),
                ('cargo', models.ForeignKey(to='comissoes.CargoComissao')),
                ('composicao', models.ForeignKey(to='comissoes.Composicao')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Participação em Comissão',
                'verbose_name_plural': 'Participações em Comissão',
            },
        ),
        migrations.CreateModel(
            name='Periodo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(blank=True, verbose_name='Data Fim', null=True)),
            ],
            options={
                'verbose_name': 'Período de composição de Comissão',
                'verbose_name_plural': 'Períodos de composição de Comissão',
            },
        ),
        migrations.CreateModel(
            name='TipoComissao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('natureza', models.CharField(max_length=1, choices=[('T', 'Temporária'), ('P', 'Permanente')], verbose_name='Natureza')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('dispositivo_regimental', models.CharField(max_length=50, blank=True, verbose_name='Dispositivo Regimental', null=True)),
            ],
            options={
                'verbose_name': 'Tipo de Comissão',
                'verbose_name_plural': 'Tipos de Comissão',
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
