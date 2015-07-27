# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0001_initial'),
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcompanhamentoMateria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('email', models.CharField(max_length=100, verbose_name='Endereço de E-mail')),
                ('hash', models.CharField(max_length=8)),
            ],
            options={
                'verbose_name': 'Acompanhamento de Matéria',
                'verbose_name_plural': 'Acompanhamentos de Matéria',
            },
        ),
        migrations.CreateModel(
            name='Anexada',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_anexacao', models.DateField(verbose_name='Data Anexação')),
                ('data_desanexacao', models.DateField(blank=True, verbose_name='Data Desanexação', null=True)),
            ],
            options={
                'verbose_name': 'Anexada',
                'verbose_name_plural': 'Anexadas',
            },
        ),
        migrations.CreateModel(
            name='AssuntoMateria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('assunto', models.CharField(max_length=200)),
                ('dispositivo', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Assunto de Matéria',
                'verbose_name_plural': 'Assuntos de Matéria',
            },
        ),
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, blank=True, verbose_name='Autor', null=True)),
                ('cargo', models.CharField(max_length=50, blank=True, null=True)),
                ('username', models.CharField(max_length=50, blank=True, null=True)),
                ('comissao', models.ForeignKey(to='comissoes.Comissao', blank=True, null=True)),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', blank=True, null=True)),
                ('partido', models.ForeignKey(to='parlamentares.Partido', blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Autor',
                'verbose_name_plural': 'Autores',
            },
        ),
        migrations.CreateModel(
            name='Autoria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('primeiro_autor', models.BooleanField(verbose_name='Primeiro Autor')),
                ('autor', models.ForeignKey(to='materia.Autor')),
            ],
            options={
                'verbose_name': 'Autoria',
                'verbose_name_plural': 'Autorias',
            },
        ),
        migrations.CreateModel(
            name='DespachoInicial',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero_ordem', models.IntegerField()),
                ('comissao', models.ForeignKey(to='comissoes.Comissao')),
            ],
            options={
                'verbose_name': 'Despacho Inicial',
                'verbose_name_plural': 'Despachos Iniciais',
            },
        ),
        migrations.CreateModel(
            name='DocumentoAcessorio',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=30, verbose_name='Descrição')),
                ('data', models.DateField(blank=True, verbose_name='Data', null=True)),
                ('autor', models.CharField(max_length=50, blank=True, verbose_name='Autor', null=True)),
                ('ementa', models.TextField(blank=True, verbose_name='Ementa', null=True)),
                ('indexacao', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Documento Acessório',
                'verbose_name_plural': 'Documentos Acessórios',
            },
        ),
        migrations.CreateModel(
            name='MateriaAssunto',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('assunto', models.ForeignKey(to='materia.AssuntoMateria')),
            ],
            options={
                'verbose_name': 'Relação Matéria - Assunto',
                'verbose_name_plural': 'Relações Matéria - Assunto',
            },
        ),
        migrations.CreateModel(
            name='MateriaLegislativa',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero', models.IntegerField(verbose_name='Número')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('numero_protocolo', models.IntegerField(blank=True, verbose_name='Núm. Protocolo', null=True)),
                ('data_apresentacao', models.DateField(blank=True, verbose_name='Data Apresentação', null=True)),
                ('tipo_apresentacao', models.CharField(max_length=1, choices=[('O', 'Oral'), ('E', 'Escrita')], blank=True, verbose_name='Tipo de Apresentação', null=True)),
                ('data_publicacao', models.DateField(blank=True, verbose_name='Data Publicação', null=True)),
                ('numero_origem_externa', models.CharField(max_length=5, blank=True, verbose_name='Número', null=True)),
                ('ano_origem_externa', models.SmallIntegerField(blank=True, verbose_name='Ano', null=True)),
                ('data_origem_externa', models.DateField(blank=True, verbose_name='Data', null=True)),
                ('apelido', models.CharField(max_length=50, blank=True, verbose_name='Apelido', null=True)),
                ('dias_prazo', models.IntegerField(blank=True, verbose_name='Dias Prazo', null=True)),
                ('data_fim_prazo', models.DateField(blank=True, verbose_name='Data Fim Prazo', null=True)),
                ('em_tramitacao', models.BooleanField(verbose_name='Em Tramitação?')),
                ('polemica', models.NullBooleanField(verbose_name='Matéria Polêmica?')),
                ('objeto', models.CharField(max_length=150, blank=True, verbose_name='Objeto', null=True)),
                ('complementar', models.NullBooleanField(verbose_name='É Complementar?')),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('indexacao', models.TextField(blank=True, verbose_name='Indexação', null=True)),
                ('observacao', models.TextField(blank=True, verbose_name='Observação', null=True)),
                ('resultado', models.TextField(blank=True, null=True)),
                ('anexadas', models.ManyToManyField(to='materia.MateriaLegislativa', through='materia.Anexada', related_name='anexo_de')),
            ],
            options={
                'verbose_name': 'Matéria Legislativa',
                'verbose_name_plural': 'Matérias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='Numeracao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('numero_ordem', models.IntegerField()),
                ('numero_materia', models.CharField(max_length=5, verbose_name='Número')),
                ('ano_materia', models.SmallIntegerField(verbose_name='Ano')),
                ('data_materia', models.DateField(blank=True, verbose_name='Data', null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Numeração',
                'verbose_name_plural': 'Numerações',
            },
        ),
        migrations.CreateModel(
            name='Orgao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('unidade_deliberativa', models.BooleanField(verbose_name='Unidade Deliberativa')),
                ('endereco', models.CharField(max_length=100, blank=True, verbose_name='Endereço', null=True)),
                ('telefone', models.CharField(max_length=50, blank=True, verbose_name='Telefone', null=True)),
            ],
            options={
                'verbose_name': 'Órgão',
                'verbose_name_plural': 'Órgãos',
            },
        ),
        migrations.CreateModel(
            name='Origem',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Origem',
                'verbose_name_plural': 'Origens',
            },
        ),
        migrations.CreateModel(
            name='Parecer',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('tipo_conclusao', models.CharField(max_length=3, blank=True, null=True)),
                ('tipo_apresentacao', models.CharField(max_length=1, choices=[('O', 'Oral'), ('E', 'Escrita')])),
                ('parecer', models.TextField(blank=True, null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Parecer',
                'verbose_name_plural': 'Pareceres',
            },
        ),
        migrations.CreateModel(
            name='Proposicao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_envio', models.DateTimeField(verbose_name='Data de Envio', null=True)),
                ('data_recebimento', models.DateTimeField(blank=True, verbose_name='Data de Incorporação', null=True)),
                ('descricao', models.CharField(max_length=100, verbose_name='Descrição')),
                ('data_devolucao', models.DateTimeField(blank=True, verbose_name='Data de devolução', null=True)),
                ('justificativa_devolucao', models.CharField(max_length=200, blank=True, verbose_name='Justificativa da Devolução', null=True)),
                ('numero_proposicao', models.IntegerField(blank=True, verbose_name='', null=True)),
                ('autor', models.ForeignKey(to='materia.Autor')),
                ('documento', models.ForeignKey(to='materia.DocumentoAcessorio', blank=True, null=True, verbose_name='Documento')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa', blank=True, null=True, verbose_name='Matéria')),
            ],
            options={
                'verbose_name': 'Proposição',
                'verbose_name_plural': 'Proposições',
            },
        ),
        migrations.CreateModel(
            name='RegimeTramitacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Regime Tramitação',
                'verbose_name_plural': 'Regimes Tramitação',
            },
        ),
        migrations.CreateModel(
            name='Relatoria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_designacao_relator', models.DateField(verbose_name='Data Designação')),
                ('data_destituicao_relator', models.DateField(blank=True, verbose_name='Data Destituição', null=True)),
                ('comissao', models.ForeignKey(to='comissoes.Comissao', blank=True, null=True, verbose_name='Localização Atual')),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name': 'Relatoria',
                'verbose_name_plural': 'Relatorias',
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacao',
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
            name='TipoAutor',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo de Autor',
                'verbose_name_plural': 'Tipos de Autor',
            },
        ),
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Tipo Documento')),
            ],
            options={
                'verbose_name': 'Tipo de Documento',
                'verbose_name_plural': 'Tipos de Documento',
            },
        ),
        migrations.CreateModel(
            name='TipoFimRelatoria',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Tipo Fim Relatoria')),
            ],
            options={
                'verbose_name': 'Tipo Fim de Relatoria',
                'verbose_name_plural': 'Tipos Fim de Relatoria',
            },
        ),
        migrations.CreateModel(
            name='TipoMateriaLegislativa',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=5, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição ')),
                ('num_automatica', models.BooleanField()),
                ('quorum_minimo_votacao', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Tipo de Matéria Legislativa',
                'verbose_name_plural': 'Tipos de Matérias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='TipoProposicao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
                ('materia_ou_documento', models.CharField(max_length=1, choices=[('M', 'Matéria'), ('D', 'Documento')], verbose_name='Gera')),
                ('modelo', models.CharField(max_length=50, verbose_name='Modelo XML')),
                ('tipo_documento', models.ForeignKey(to='materia.TipoDocumento', blank=True, null=True, verbose_name='Tipo Documento')),
                ('tipo_materia', models.ForeignKey(to='materia.TipoMateriaLegislativa', blank=True, null=True, verbose_name='Tipo Matéria')),
            ],
            options={
                'verbose_name': 'Tipo de Proposição',
                'verbose_name_plural': 'Tipos de Proposições',
            },
        ),
        migrations.CreateModel(
            name='Tramitacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('data_tramitacao', models.DateField(blank=True, verbose_name='Data Tramitação', null=True)),
                ('data_encaminhamento', models.DateField(blank=True, verbose_name='Data Encaminhamento', null=True)),
                ('ultima', models.BooleanField()),
                ('urgente', models.BooleanField(verbose_name='Urgente ?')),
                ('turno', models.CharField(max_length=1, choices=[('P', 'Primeiro'), ('S', 'Segundo'), ('Ú', 'Único'), ('L', 'Suplementar'), ('F', 'Final'), ('A', 'Votação única em Regime de Urgência'), ('B', '1ª Votação'), ('C', '2ª e 3ª Votação')], blank=True, verbose_name='Turno', null=True)),
                ('texto', models.TextField(blank=True, verbose_name='Texto da Ação', null=True)),
                ('data_fim_prazo', models.DateField(blank=True, verbose_name='Data Fim Prazo', null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('status', models.ForeignKey(to='materia.StatusTramitacao', blank=True, null=True, verbose_name='Status')),
            ],
            options={
                'verbose_name': 'Tramitação',
                'verbose_name_plural': 'Tramitações',
            },
        ),
        migrations.CreateModel(
            name='UnidadeTramitacao',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('comissao', models.ForeignKey(to='comissoes.Comissao', blank=True, null=True, verbose_name='Comissão')),
                ('orgao', models.ForeignKey(to='materia.Orgao', blank=True, null=True, verbose_name='Órgão')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar', blank=True, null=True, verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name': 'Unidade de Tramitação',
                'verbose_name_plural': 'Unidades de Tramitação',
            },
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unidade_tramitacao_destino',
            field=models.ForeignKey(to='materia.UnidadeTramitacao', blank=True, null=True, related_name='+', verbose_name='Unidade Destino'),
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unidade_tramitacao_local',
            field=models.ForeignKey(to='materia.UnidadeTramitacao', blank=True, null=True, related_name='+', verbose_name='Unidade Local'),
        ),
        migrations.AddField(
            model_name='relatoria',
            name='tipo_fim_relatoria',
            field=models.ForeignKey(to='materia.TipoFimRelatoria', blank=True, null=True, verbose_name='Motivo Fim Relatoria'),
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
            field=models.ForeignKey(to='materia.Origem', blank=True, null=True, verbose_name='Local Origem'),
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
            field=models.ForeignKey(to='materia.TipoMateriaLegislativa', blank=True, null=True, related_name='+', verbose_name='Tipo'),
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
            field=models.ForeignKey(related_name='+', to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='anexada',
            name='materia_principal',
            field=models.ForeignKey(related_name='+', to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='acompanhamentomateria',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
    ]
