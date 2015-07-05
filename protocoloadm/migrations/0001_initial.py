# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentoAcessorioAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_documento', models.CharField(max_length=30, verbose_name='Nome')),
                ('nome_arquivo', models.CharField(max_length=100, verbose_name='Arquivo')),
                ('data_documento', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('nome_autor_documento', models.CharField(max_length=50, null=True, verbose_name='Autor', blank=True)),
                ('assunto', models.TextField(null=True, verbose_name='Assunto', blank=True)),
                ('indexacao', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Documento Acess\xf3rio',
                'verbose_name_plural': 'Documentos Acess\xf3rios',
            },
        ),
        migrations.CreateModel(
            name='DocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_documento', models.IntegerField(verbose_name='N\xfamero')),
                ('ano_documento', models.SmallIntegerField(verbose_name='Ano')),
                ('data_documento', models.DateField(verbose_name='Data')),
                ('numero_protocolo', models.IntegerField(null=True, verbose_name='N\xfam. Protocolo', blank=True)),
                ('interessado', models.CharField(max_length=50, null=True, verbose_name='Interessado', blank=True)),
                ('numero_dias_prazo', models.IntegerField(null=True, verbose_name='Dias Prazo', blank=True)),
                ('data_fim_prazo', models.DateField(null=True, verbose_name='Data Fim Prazo', blank=True)),
                ('tramitacao', models.BooleanField(verbose_name='Em Tramita\xe7\xe3o?')),
                ('assunto', models.TextField(verbose_name='Assunto')),
                ('observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('autor', models.ForeignKey(blank=True, to='materia.Autor', null=True)),
            ],
            options={
                'verbose_name': 'Documento Administrativo',
                'verbose_name_plural': 'Documentos Administrativos',
            },
        ),
        migrations.CreateModel(
            name='Protocolo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_protocolo', models.IntegerField(null=True, verbose_name='N\xfam. Protocolo', blank=True)),
                ('ano_protocolo', models.SmallIntegerField()),
                ('data_protocolo', models.DateField()),
                ('hora_protocolo', models.TimeField()),
                ('data_timestamp', models.DateTimeField()),
                ('tipo_protocolo', models.IntegerField(verbose_name='Tipo de Protocolo')),
                ('tipo_processo', models.IntegerField()),
                ('interessado', models.CharField(max_length=60, null=True, verbose_name='Interessado', blank=True)),
                ('assunto_ementa', models.TextField(null=True, blank=True)),
                ('numero_paginas', models.IntegerField(null=True, verbose_name='N\xfam. P\xe1ginas', blank=True)),
                ('observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('anulado', models.BooleanField()),
                ('user_anulacao', models.CharField(max_length=20, null=True, blank=True)),
                ('ip_anulacao', models.CharField(max_length=15, null=True, blank=True)),
                ('just_anulacao', models.CharField(max_length=60, null=True, blank=True)),
                ('timestamp_anulacao', models.DateTimeField(null=True, blank=True)),
                ('autor', models.ForeignKey(blank=True, to='materia.Autor', null=True)),
            ],
            options={
                'verbose_name': 'Protocolo',
                'verbose_name_plural': 'Protocolos',
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_status', models.CharField(max_length=10, verbose_name='Sigla')),
                ('descricao_status', models.CharField(max_length=60, verbose_name='Descri\xe7\xe3o')),
                ('fim_tramitacao', models.BooleanField()),
                ('retorno_tramitacao', models.BooleanField()),
            ],
            options={
                'verbose_name': 'Status de Tramita\xe7\xe3o',
                'verbose_name_plural': 'Status de Tramita\xe7\xe3o',
            },
        ),
        migrations.CreateModel(
            name='TipoDocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_tipo_documento', models.CharField(max_length=5, verbose_name='Sigla')),
                ('descricao_tipo_documento', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
            ],
            options={
                'verbose_name': 'Tipo de Documento Administrativo',
                'verbose_name_plural': 'Tipos de Documento Administrativo',
            },
        ),
        migrations.CreateModel(
            name='TramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_tramitacao', models.DateField(null=True, verbose_name='Data Tramita\xe7\xe3o', blank=True)),
                ('cod_unid_tram_local', models.IntegerField(null=True, verbose_name='Unidade Local', blank=True)),
                ('data_encaminha', models.DateField(null=True, verbose_name='Data Encaminhamento', blank=True)),
                ('cod_unid_tram_dest', models.IntegerField(null=True, verbose_name='Unidade Destino', blank=True)),
                ('ult_tramitacao', models.BooleanField()),
                ('tramitacao', models.TextField(null=True, verbose_name='Texto da A\xe7\xe3o', blank=True)),
                ('data_fim_prazo', models.DateField(null=True, verbose_name='Data Fim do Prazo', blank=True)),
                ('documento', models.ForeignKey(to='protocoloadm.DocumentoAdministrativo')),
                ('status', models.ForeignKey(verbose_name='Status', blank=True, to='protocoloadm.StatusTramitacaoAdministrativo', null=True)),
            ],
            options={
                'verbose_name': 'Tramita\xe7\xe3o de Documento Administrativo',
                'verbose_name_plural': 'Tramita\xe7\xf5es de Documento Administrativo',
            },
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_documento',
            field=models.ForeignKey(verbose_name='Tipo de documento', blank=True, to='protocoloadm.TipoDocumentoAdministrativo', null=True),
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_materia',
            field=models.ForeignKey(verbose_name='Tipo Mat\xe9ria', blank=True, to='materia.TipoMateriaLegislativa', null=True),
        ),
        migrations.AddField(
            model_name='documentoadministrativo',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo Documento', to='protocoloadm.TipoDocumentoAdministrativo'),
        ),
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='documento',
            field=models.ForeignKey(to='protocoloadm.DocumentoAdministrativo'),
        ),
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo', to='protocoloadm.TipoDocumentoAdministrativo'),
        ),
    ]
