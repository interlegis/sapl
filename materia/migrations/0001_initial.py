# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0001_initial'),
        ('comissoes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcompanhamentoMateria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('email', models.CharField(max_length=100, verbose_name='Endereço de E-mail')),
                ('hash', models.CharField(max_length=8)),
            ],
            options={
                'verbose_name_plural': 'Acompanhamentos de Matéria',
                'verbose_name': 'Acompanhamento de Matéria',
            },
        ),
        migrations.CreateModel(
            name='Anexada',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_anexacao', models.DateField(verbose_name='Data Anexação')),
                ('data_desanexacao', models.DateField(blank=True, null=True, verbose_name='Data Desanexação')),
            ],
            options={
                'verbose_name_plural': 'Anexadas',
                'verbose_name': 'Anexada',
            },
        ),
        migrations.CreateModel(
            name='AssuntoMateria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('assunto', models.CharField(max_length=200)),
                ('dispositivo', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Assuntos de Matéria',
                'verbose_name': 'Assunto de Matéria',
            },
        ),
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(blank=True, max_length=50, null=True, verbose_name='Autor')),
                ('cargo', models.CharField(blank=True, max_length=50, null=True)),
                ('username', models.CharField(blank=True, max_length=50, null=True)),
                ('comissao', models.ForeignKey(blank=True, null=True, to='comissoes.Comissao')),
                ('parlamentar', models.ForeignKey(blank=True, null=True, to='parlamentares.Parlamentar')),
                ('partido', models.ForeignKey(blank=True, null=True, to='parlamentares.Partido')),
            ],
            options={
                'verbose_name_plural': 'Autores',
                'verbose_name': 'Autor',
            },
        ),
        migrations.CreateModel(
            name='Autoria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('primeiro_autor', models.BooleanField(verbose_name='Primeiro Autor')),
                ('autor', models.ForeignKey(to='materia.Autor')),
            ],
            options={
                'verbose_name_plural': 'Autorias',
                'verbose_name': 'Autoria',
            },
        ),
        migrations.CreateModel(
            name='DespachoInicial',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero_ordem', models.IntegerField()),
                ('comissao', models.ForeignKey(to='comissoes.Comissao')),
            ],
            options={
                'verbose_name_plural': 'Despachos Iniciais',
                'verbose_name': 'Despacho Inicial',
            },
        ),
        migrations.CreateModel(
            name='DocumentoAcessorio',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=30, verbose_name='Descrição')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('autor', models.CharField(blank=True, max_length=50, null=True, verbose_name='Autor')),
                ('ementa', models.TextField(blank=True, null=True, verbose_name='Ementa')),
                ('indexacao', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'Documentos Acessórios',
                'verbose_name': 'Documento Acessório',
            },
        ),
        migrations.CreateModel(
            name='MateriaAssunto',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('assunto', models.ForeignKey(to='materia.AssuntoMateria')),
            ],
            options={
                'verbose_name_plural': 'Relações Matéria - Assunto',
                'verbose_name': 'Relação Matéria - Assunto',
            },
        ),
        migrations.CreateModel(
            name='MateriaLegislativa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('numero_protocolo', models.IntegerField(blank=True, null=True, verbose_name='Núm. Protocolo')),
                ('data_apresentacao', models.DateField(blank=True, null=True, verbose_name='Data Apresentação')),
                ('tipo_apresentacao', models.CharField(blank=True, max_length=1, null=True, verbose_name='Tipo de Apresentação', choices=[('O', 'Oral'), ('E', 'Escrita')])),
                ('data_publicacao', models.DateField(blank=True, null=True, verbose_name='Data Publicação')),
                ('numero_origem_externa', models.CharField(blank=True, max_length=5, null=True, verbose_name='Número')),
                ('ano_origem_externa', models.SmallIntegerField(blank=True, null=True, verbose_name='Ano')),
                ('data_origem_externa', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('apelido', models.CharField(blank=True, max_length=50, null=True, verbose_name='Apelido')),
                ('dias_prazo', models.IntegerField(blank=True, null=True, verbose_name='Dias Prazo')),
                ('data_fim_prazo', models.DateField(blank=True, null=True, verbose_name='Data Fim Prazo')),
                ('em_tramitacao', models.BooleanField(verbose_name='Em Tramitação?')),
                ('polemica', models.NullBooleanField(verbose_name='Matéria Polêmica?')),
                ('objeto', models.CharField(blank=True, max_length=150, null=True, verbose_name='Objeto')),
                ('complementar', models.NullBooleanField(verbose_name='É Complementar?')),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('indexacao', models.TextField(blank=True, null=True, verbose_name='Indexação')),
                ('observacao', models.TextField(blank=True, null=True, verbose_name='Observação')),
                ('resultado', models.TextField(blank=True, null=True)),
                ('anexadas', models.ManyToManyField(to='materia.MateriaLegislativa', through='materia.Anexada', related_name='anexo_de')),
            ],
            options={
                'verbose_name_plural': 'Matérias Legislativas',
                'verbose_name': 'Matéria Legislativa',
            },
        ),
        migrations.CreateModel(
            name='Numeracao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('numero_ordem', models.IntegerField()),
                ('numero_materia', models.CharField(max_length=5, verbose_name='Número')),
                ('ano_materia', models.SmallIntegerField(verbose_name='Ano')),
                ('data_materia', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name_plural': 'Numerações',
                'verbose_name': 'Numeração',
            },
        ),
        migrations.CreateModel(
            name='Orgao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('unidade_deliberativa', models.BooleanField(verbose_name='Unidade Deliberativa')),
                ('endereco', models.CharField(blank=True, max_length=100, null=True, verbose_name='Endereço')),
                ('telefone', models.CharField(blank=True, max_length=50, null=True, verbose_name='Telefone')),
            ],
            options={
                'verbose_name_plural': 'Órgãos',
                'verbose_name': 'Órgão',
            },
        ),
        migrations.CreateModel(
            name='Origem',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
            ],
            options={
                'verbose_name_plural': 'Origens',
                'verbose_name': 'Origem',
            },
        ),
        migrations.CreateModel(
            name='Parecer',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('tipo_conclusao', models.CharField(blank=True, max_length=3, null=True)),
                ('tipo_apresentacao', models.CharField(choices=[('O', 'Oral'), ('E', 'Escrita')], max_length=1)),
                ('parecer', models.TextField(blank=True, null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name_plural': 'Pareceres',
                'verbose_name': 'Parecer',
            },
        ),
        migrations.CreateModel(
            name='Proposicao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_envio', models.DateTimeField(null=True, verbose_name='Data de Envio')),
                ('data_recebimento', models.DateTimeField(blank=True, null=True, verbose_name='Data de Incorporação')),
                ('descricao', models.CharField(max_length=100, verbose_name='Descrição')),
                ('data_devolucao', models.DateTimeField(blank=True, null=True, verbose_name='Data de devolução')),
                ('justificativa_devolucao', models.CharField(blank=True, max_length=200, null=True, verbose_name='Justificativa da Devolução')),
                ('numero_proposicao', models.IntegerField(blank=True, null=True, verbose_name='Número')),
                ('autor', models.ForeignKey(to='materia.Autor')),
                ('documento', models.ForeignKey(blank=True, null=True, to='materia.DocumentoAcessorio', verbose_name='Documento')),
                ('materia', models.ForeignKey(blank=True, null=True, to='materia.MateriaLegislativa', verbose_name='Matéria')),
            ],
            options={
                'verbose_name_plural': 'Proposições',
                'verbose_name': 'Proposição',
            },
        ),
        migrations.CreateModel(
            name='RegimeTramitacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name_plural': 'Regimes Tramitação',
                'verbose_name': 'Regime Tramitação',
            },
        ),
        migrations.CreateModel(
            name='Relatoria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_designacao_relator', models.DateField(verbose_name='Data Designação')),
                ('data_destituicao_relator', models.DateField(blank=True, null=True, verbose_name='Data Destituição')),
                ('comissao', models.ForeignKey(blank=True, null=True, to='comissoes.Comissao', verbose_name='Localização Atual')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Relatorias',
                'verbose_name': 'Relatoria',
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacao',
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
            name='TipoAutor',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Autor',
                'verbose_name': 'Tipo de Autor',
            },
        ),
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Tipo Documento')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Documento',
                'verbose_name': 'Tipo de Documento',
            },
        ),
        migrations.CreateModel(
            name='TipoFimRelatoria',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Tipo Fim Relatoria')),
            ],
            options={
                'verbose_name_plural': 'Tipos Fim de Relatoria',
                'verbose_name': 'Tipo Fim de Relatoria',
            },
        ),
        migrations.CreateModel(
            name='TipoMateriaLegislativa',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('sigla', models.CharField(max_length=5, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição ')),
                ('num_automatica', models.BooleanField()),
                ('quorum_minimo_votacao', models.IntegerField()),
            ],
            options={
                'verbose_name_plural': 'Tipos de Matérias Legislativas',
                'verbose_name': 'Tipo de Matéria Legislativa',
            },
        ),
        migrations.CreateModel(
            name='TipoProposicao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
                ('materia_ou_documento', models.CharField(choices=[('M', 'Matéria'), ('D', 'Documento')], max_length=1, verbose_name='Gera')),
                ('modelo', models.CharField(max_length=50, verbose_name='Modelo XML')),
                ('tipo_documento', models.ForeignKey(blank=True, null=True, to='materia.TipoDocumento', verbose_name='Tipo Documento')),
                ('tipo_materia', models.ForeignKey(blank=True, null=True, to='materia.TipoMateriaLegislativa', verbose_name='Tipo Matéria')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Proposições',
                'verbose_name': 'Tipo de Proposição',
            },
        ),
        migrations.CreateModel(
            name='Tramitacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('data_tramitacao', models.DateField(blank=True, null=True, verbose_name='Data Tramitação')),
                ('data_encaminhamento', models.DateField(blank=True, null=True, verbose_name='Data Encaminhamento')),
                ('ultima', models.BooleanField()),
                ('urgente', models.BooleanField(verbose_name='Urgente ?')),
                ('turno', models.CharField(blank=True, max_length=1, null=True, verbose_name='Turno', choices=[('P', 'Primeiro'), ('S', 'Segundo'), ('Ú', 'Único'), ('L', 'Suplementar'), ('F', 'Final'), ('A', 'Votação única em Regime de Urgência'), ('B', '1ª Votação'), ('C', '2ª e 3ª Votação')])),
                ('texto', models.TextField(blank=True, null=True, verbose_name='Texto da Ação')),
                ('data_fim_prazo', models.DateField(blank=True, null=True, verbose_name='Data Fim Prazo')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('status', models.ForeignKey(blank=True, null=True, to='materia.StatusTramitacao', verbose_name='Status')),
            ],
            options={
                'verbose_name_plural': 'Tramitações',
                'verbose_name': 'Tramitação',
            },
        ),
        migrations.CreateModel(
            name='UnidadeTramitacao',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('comissao', models.ForeignKey(blank=True, null=True, to='comissoes.Comissao', verbose_name='Comissão')),
                ('orgao', models.ForeignKey(blank=True, null=True, to='materia.Orgao', verbose_name='Órgão')),
                ('parlamentar', models.ForeignKey(blank=True, null=True, to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name_plural': 'Unidades de Tramitação',
                'verbose_name': 'Unidade de Tramitação',
            },
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unidade_tramitacao_destino',
            field=models.ForeignKey(blank=True, null=True, to='materia.UnidadeTramitacao', verbose_name='Unidade Destino', related_name='+'),
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unidade_tramitacao_local',
            field=models.ForeignKey(blank=True, null=True, to='materia.UnidadeTramitacao', verbose_name='Unidade Local', related_name='+'),
        ),
        migrations.AddField(
            model_name='relatoria',
            name='tipo_fim_relatoria',
            field=models.ForeignKey(blank=True, null=True, to='materia.TipoFimRelatoria', verbose_name='Motivo Fim Relatoria'),
        ),
        migrations.AddField(
            model_name='proposicao',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoProposicao', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='parecer',
            name='relatoria',
            field=models.ForeignKey(to='materia.Relatoria'),
        ),
        migrations.AddField(
            model_name='numeracao',
            name='tipo_materia',
            field=models.ForeignKey(to='materia.TipoMateriaLegislativa', verbose_name='Tipo de Matéria'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='local_origem_externa',
            field=models.ForeignKey(blank=True, null=True, to='materia.Origem', verbose_name='Local Origem'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='regime_tramitacao',
            field=models.ForeignKey(to='materia.RegimeTramitacao', verbose_name='Regime Tramitação'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoMateriaLegislativa', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='tipo_origem_externa',
            field=models.ForeignKey(blank=True, null=True, to='materia.TipoMateriaLegislativa', verbose_name='Tipo', related_name='+'),
        ),
        migrations.AddField(
            model_name='materiaassunto',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='documentoacessorio',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='documentoacessorio',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoDocumento', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='despachoinicial',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='autoria',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='autor',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoAutor', verbose_name='Tipo'),
        ),
        migrations.AddField(
            model_name='anexada',
            name='materia_anexada',
            field=models.ForeignKey(to='materia.MateriaLegislativa', related_name='+'),
        ),
        migrations.AddField(
            model_name='anexada',
            name='materia_principal',
            field=models.ForeignKey(to='materia.MateriaLegislativa', related_name='+'),
        ),
        migrations.AddField(
            model_name='acompanhamentomateria',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
    ]
