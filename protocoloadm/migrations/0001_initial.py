# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentoAcessorioAdministrativo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=30, verbose_name='Nome')),
                ('arquivo', models.CharField(max_length=100, verbose_name='Arquivo')),
                ('data', models.DateField(blank=True, verbose_name='Data', null=True)),
                ('autor', models.CharField(max_length=50, blank=True, verbose_name='Autor', null=True)),
                ('assunto', models.TextField(blank=True, verbose_name='Assunto', null=True)),
                ('indexacao', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Documento Acessório',
                'verbose_name_plural': 'Documentos Acessórios',
            },
        ),
        migrations.CreateModel(
            name='DocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('data', models.DateField(verbose_name='Data')),
                ('numero_protocolo', models.IntegerField(blank=True, verbose_name='Núm. Protocolo', null=True)),
                ('interessado', models.CharField(max_length=50, blank=True, verbose_name='Interessado', null=True)),
                ('dias_prazo', models.IntegerField(blank=True, verbose_name='Dias Prazo', null=True)),
                ('data_fim_prazo', models.DateField(blank=True, verbose_name='Data Fim Prazo', null=True)),
                ('tramitacao', models.BooleanField(verbose_name='Em Tramitação?')),
                ('assunto', models.TextField(verbose_name='Assunto')),
                ('observacao', models.TextField(blank=True, verbose_name='Observação', null=True)),
                ('autor', models.ForeignKey(to='materia.Autor', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Documento Administrativo',
                'verbose_name_plural': 'Documentos Administrativos',
            },
        ),
        migrations.CreateModel(
            name='Protocolo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero', models.IntegerField(blank=True, verbose_name='Número do Protocolo', null=True)),
                ('ano', models.SmallIntegerField()),
                ('data', models.DateField()),
                ('hora', models.TimeField()),
                ('timestamp', models.DateTimeField()),
                ('tipo_protocolo', models.IntegerField(verbose_name='Tipo de Protocolo')),
                ('tipo_processo', models.IntegerField()),
                ('interessado', models.CharField(max_length=60, blank=True, verbose_name='Interessado', null=True)),
                ('assunto_ementa', models.TextField(blank=True, null=True)),
                ('numero_paginas', models.IntegerField(blank=True, verbose_name='Número de Páginas', null=True)),
                ('observacao', models.TextField(blank=True, verbose_name='Observação', null=True)),
                ('anulado', models.BooleanField()),
                ('user_anulacao', models.CharField(max_length=20, blank=True, null=True)),
                ('ip_anulacao', models.CharField(max_length=15, blank=True, null=True)),
                ('justificativa_anulacao', models.CharField(max_length=60, blank=True, null=True)),
                ('timestamp_anulacao', models.DateTimeField(blank=True, null=True)),
                ('autor', models.ForeignKey(to='materia.Autor', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Protocolo',
                'verbose_name_plural': 'Protocolos',
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=60, verbose_name='Descrição')),
                ('indicador', models.CharField(max_length=1, choices=[('F', 'Fim'), ('R', 'Retorno')], verbose_name='Indicador da Tramitação')),
            ],
            options={
                'verbose_name': 'Status de Tramitação',
                'verbose_name_plural': 'Status de Tramitação',
            },
        ),
        migrations.CreateModel(
            name='TipoDocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=5, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Documento Administrativo',
                'verbose_name_plural': 'Tipos de Documento Administrativo',
            },
        ),
        migrations.CreateModel(
            name='TramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_tramitacao', models.DateField(blank=True, verbose_name='Data Tramitação', null=True)),
                ('data_encaminhamento', models.DateField(blank=True, verbose_name='Data Encaminhamento', null=True)),
                ('ultima', models.BooleanField()),
                ('texto', models.TextField(blank=True, verbose_name='Texto da Ação', null=True)),
                ('data_fim_prazo', models.DateField(blank=True, verbose_name='Data Fim do Prazo', null=True)),
                ('documento', models.ForeignKey(to='protocoloadm.DocumentoAdministrativo')),
                ('status', models.ForeignKey(to='protocoloadm.StatusTramitacaoAdministrativo', blank=True, null=True, verbose_name='Status')),
                ('unidade_tramitacao_destino', models.ForeignKey(to='materia.UnidadeTramitacao', blank=True, null=True, related_name='+', verbose_name='Unidade Destino')),
                ('unidade_tramitacao_local', models.ForeignKey(to='materia.UnidadeTramitacao', blank=True, null=True, related_name='+', verbose_name='Unidade Local')),
            ],
            options={
                'verbose_name': 'Tramitação de Documento Administrativo',
                'verbose_name_plural': 'Tramitações de Documento Administrativo',
            },
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_documento',
            field=models.ForeignKey(to='protocoloadm.TipoDocumentoAdministrativo', blank=True, null=True, verbose_name='Tipo de documento'),
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_materia',
            field=models.ForeignKey(to='materia.TipoMateriaLegislativa', blank=True, null=True, verbose_name='Tipo Matéria'),
        ),
        migrations.AddField(
            model_name='documentoadministrativo',
            name='tipo',
            field=models.ForeignKey(to='protocoloadm.TipoDocumentoAdministrativo', verbose_name='Tipo Documento'),
        ),
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='documento',
            field=models.ForeignKey(to='protocoloadm.DocumentoAdministrativo'),
        ),
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='tipo',
            field=models.ForeignKey(to='protocoloadm.TipoDocumentoAdministrativo', verbose_name='Tipo'),
        ),
    ]
