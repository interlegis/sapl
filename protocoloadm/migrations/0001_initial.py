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
                ('nome_documento', models.CharField(max_length=30)),
                ('nome_arquivo', models.CharField(max_length=100)),
                ('data_documento', models.DateField(null=True, blank=True)),
                ('nome_autor_documento', models.CharField(max_length=50, null=True, blank=True)),
                ('txt_assunto', models.TextField(null=True, blank=True)),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_documento', models.IntegerField()),
                ('ano_documento', models.SmallIntegerField()),
                ('data_documento', models.DateField()),
                ('numero_protocolo', models.IntegerField(null=True, blank=True)),
                ('txt_interessado', models.CharField(max_length=50, null=True, blank=True)),
                ('numero_dias_prazo', models.IntegerField(null=True, blank=True)),
                ('data_fim_prazo', models.DateField(null=True, blank=True)),
                ('tramitacao', models.BooleanField()),
                ('txt_assunto', models.TextField()),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('autor', models.ForeignKey(blank=True, to='materia.Autor', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Protocolo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_protocolo', models.IntegerField(null=True, blank=True)),
                ('ano_protocolo', models.SmallIntegerField()),
                ('data_protocolo', models.DateField()),
                ('hora_protocolo', models.TimeField()),
                ('data_timestamp', models.DateTimeField()),
                ('tipo_protocolo', models.IntegerField()),
                ('tipo_processo', models.IntegerField()),
                ('txt_interessado', models.CharField(max_length=60, null=True, blank=True)),
                ('txt_assunto_ementa', models.TextField(null=True, blank=True)),
                ('numero_paginas', models.IntegerField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('anulado', models.BooleanField()),
                ('txt_user_anulacao', models.CharField(max_length=20, null=True, blank=True)),
                ('txt_ip_anulacao', models.CharField(max_length=15, null=True, blank=True)),
                ('txt_just_anulacao', models.CharField(max_length=60, null=True, blank=True)),
                ('timestamp_anulacao', models.DateTimeField(null=True, blank=True)),
                ('autor', models.ForeignKey(blank=True, to='materia.Autor', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StatusTramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_status', models.CharField(max_length=10)),
                ('descricao_status', models.CharField(max_length=60)),
                ('fim_tramitacao', models.BooleanField()),
                ('retorno_tramitacao', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='TipoDocumentoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_tipo_documento', models.CharField(max_length=5)),
                ('descricao_tipo_documento', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='TramitacaoAdministrativo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_tramitacao', models.DateField(null=True, blank=True)),
                ('cod_unid_tram_local', models.IntegerField(null=True, blank=True)),
                ('data_encaminha', models.DateField(null=True, blank=True)),
                ('cod_unid_tram_dest', models.IntegerField(null=True, blank=True)),
                ('ult_tramitacao', models.BooleanField()),
                ('txt_tramitacao', models.TextField(null=True, blank=True)),
                ('data_fim_prazo', models.DateField(null=True, blank=True)),
                ('documento', models.ForeignKey(to='protocoloadm.DocumentoAdministrativo')),
                ('status', models.ForeignKey(blank=True, to='protocoloadm.StatusTramitacaoAdministrativo', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_documento',
            field=models.ForeignKey(blank=True, to='protocoloadm.TipoDocumentoAdministrativo', null=True),
        ),
        migrations.AddField(
            model_name='protocolo',
            name='tipo_materia',
            field=models.ForeignKey(blank=True, to='materia.TipoMateriaLegislativa', null=True),
        ),
        migrations.AddField(
            model_name='documentoadministrativo',
            name='tipo',
            field=models.ForeignKey(to='protocoloadm.TipoDocumentoAdministrativo'),
        ),
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='documento',
            field=models.ForeignKey(to='protocoloadm.DocumentoAdministrativo'),
        ),
        migrations.AddField(
            model_name='documentoacessorioadministrativo',
            name='tipo',
            field=models.ForeignKey(to='protocoloadm.TipoDocumentoAdministrativo'),
        ),
    ]
