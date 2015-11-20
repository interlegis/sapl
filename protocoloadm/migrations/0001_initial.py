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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=30, verbose_name='Nome')),
                ('arquivo', models.CharField(max_length=100, verbose_name='Arquivo')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('autor', models.CharField(blank=True, max_length=50, null=True, verbose_name='Autor')),
                ('assunto', models.TextField(blank=True, null=True, verbose_name='Assunto')),
                ('indexacao', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Documentos Acessórios',
                'verbose_name': 'Documento Acessório',
            },
        ),
        migrations.CreateModel(
            name='DocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('data', models.DateField(verbose_name='Data')),
                ('numero_protocolo', models.IntegerField(blank=True, null=True, verbose_name='Núm. Protocolo')),
                ('interessado', models.CharField(blank=True, max_length=50, null=True, verbose_name='Interessado')),
                ('dias_prazo', models.IntegerField(blank=True, null=True, verbose_name='Dias Prazo')),
                ('data_fim_prazo', models.DateField(blank=True, null=True, verbose_name='Data Fim Prazo')),
                ('tramitacao', models.BooleanField(verbose_name='Em Tramitação?')),
                ('assunto', models.TextField(verbose_name='Assunto')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('autor', models.ForeignKey(blank=True, null=True, to='materia.Autor')),
            ],
            options={
                'verbose_name_plural': 'Documentos Administrativos',
                'verbose_name': 'Documento Administrativo',
            },
        ),
        migrations.CreateModel(
            name='Protocolo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero', models.IntegerField(blank=True, null=True, verbose_name='Número do Protocolo')),
                ('ano', models.SmallIntegerField()),
                ('data', models.DateField()),
                ('hora', models.TimeField()),
                ('timestamp', models.DateTimeField()),
                ('tipo_protocolo', models.IntegerField(verbose_name='Tipo de Protocolo')),
                ('tipo_processo', models.IntegerField()),
                ('interessado', models.CharField(blank=True, max_length=60, null=True, verbose_name='Interessado')),
                ('assunto_ementa', models.TextField(blank=True, null=True)),
                ('numero_paginas', models.IntegerField(blank=True, null=True, verbose_name='Número de Páginas')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('anulado', models.BooleanField()),
                ('user_anulacao', models.CharField(blank=True, max_length=20, null=True)),
                ('ip_anulacao', models.CharField(blank=True, max_length=15, null=True)),
                ('justificativa_anulacao', models.CharField(blank=True, max_length=60, null=True)),
                ('timestamp_anulacao', models.DateTimeField(blank=True, null=True)),
                ('autor', models.ForeignKey(blank=True, null=True, to='materia.Autor')),
            ],
            options={
                'verbose_name_plural': 'Protocolos',
                'verbose_name': 'Protocolo',
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=60, verbose_name='Descrição')),
                ('indicador', models.CharField(choices=[('F', 'Fim'), ('R', 'Retorno')], max_length=1, verbose_name='Indicador da Tramitação')),
            ],
            options={
                'verbose_name_plural': 'Status de Tramitação',
                'verbose_name': 'Status de Tramitação',
            },
        ),
        migrations.CreateModel(
            name='TipoDocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('sigla', models.CharField(max_length=5, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Documento Administrativo',
                'verbose_name': 'Tipo de Documento Administrativo',
            },
        ),
        migrations.CreateModel(
            name='TramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_tramitacao', models.DateField(blank=True, null=True, verbose_name='Data Tramitação')),
                ('data_encaminhamento', models.DateField(blank=True, null=True, verbose_name='Data Encaminhamento')),
                ('ultima', models.BooleanField()),
                ('texto', models.TextField(blank=True, null=True, verbose_name='Texto da Ação')),
                ('data_fim_prazo', models.DateField(blank=True, null=True, verbose_name='Data Fim do Prazo')),
                ('documento', models.ForeignKey(to='protocoloadm.DocumentoAdministrativo')),
                ('status', models.ForeignKey(blank=True, null=True, to='protocoloadm.StatusTramitacaoAdministrativo', verbose_name='Status')),
                ('unidade_tramitacao_destino', models.ForeignKey(blank=True, null=True, to='materia.UnidadeTramitacao', verbose_name='Unidade Destino', related_name='+')),
                ('unidade_tramitacao_local', models.ForeignKey(blank=True, null=True, to='materia.UnidadeTramitacao', verbose_name='Unidade Local', related_name='+')),
            ],
            options={
                'verbose_name_plural': 'Tramitações de Documento Administrativo',
                'verbose_name': 'Tramitação de Documento Administrativo',
            },
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_documento',
            field=models.ForeignKey(blank=True, null=True, to='protocoloadm.TipoDocumentoAdministrativo', verbose_name='Tipo de documento'),
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_materia',
            field=models.ForeignKey(blank=True, null=True, to='materia.TipoMateriaLegislativa', verbose_name='Tipo Matéria'),
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
