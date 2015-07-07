# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0001_initial'),
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcompanhamentoMateria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=100, verbose_name='Endere\xe7o de E-mail')),
                ('hash', models.CharField(max_length=8)),
            ],
            options={
                'verbose_name': 'Acompanhamento de Mat\xe9ria',
                'verbose_name_plural': 'Acompanhamentos de Mat\xe9ria',
            },
        ),
        migrations.CreateModel(
            name='Anexada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_anexacao', models.DateField(verbose_name='Data Anexa\xe7\xe3o')),
                ('data_desanexacao', models.DateField(null=True, verbose_name='Data Desanexa\xe7\xe3o', blank=True)),
            ],
            options={
                'verbose_name': 'Anexada',
                'verbose_name_plural': 'Anexadas',
            },
        ),
        migrations.CreateModel(
            name='AssuntoMateria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assunto', models.CharField(max_length=200)),
                ('dispositivo', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Assunto de Mat\xe9ria',
                'verbose_name_plural': 'Assuntos de Mat\xe9ria',
            },
        ),
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50, null=True, verbose_name='Autor', blank=True)),
                ('cargo', models.CharField(max_length=50, null=True, blank=True)),
                ('username', models.CharField(max_length=50, null=True, blank=True)),
                ('comissao', models.ForeignKey(blank=True, to='comissoes.Comissao', null=True)),
                ('parlamentar', models.ForeignKey(blank=True, to='parlamentares.Parlamentar', null=True)),
                ('partido', models.ForeignKey(blank=True, to='parlamentares.Partido', null=True)),
            ],
            options={
                'verbose_name': 'Autor',
                'verbose_name_plural': 'Autores',
            },
        ),
        migrations.CreateModel(
            name='Autoria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=30, verbose_name='Descri\xe7\xe3o')),
                ('data', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('autor', models.CharField(max_length=50, null=True, verbose_name='Autor', blank=True)),
                ('ementa', models.TextField(null=True, verbose_name='Ementa', blank=True)),
                ('indexacao', models.TextField(null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Documento Acess\xf3rio',
                'verbose_name_plural': 'Documentos Acess\xf3rios',
            },
        ),
        migrations.CreateModel(
            name='MateriaAssunto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assunto', models.ForeignKey(to='materia.AssuntoMateria')),
            ],
            options={
                'verbose_name': 'Rela\xe7\xe3o Mat\xe9ria - Assunto',
                'verbose_name_plural': 'Rela\xe7\xf5es Mat\xe9ria - Assunto',
            },
        ),
        migrations.CreateModel(
            name='MateriaLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_protocolo', models.IntegerField(null=True, verbose_name='N\xfam. Protocolo', blank=True)),
                ('numero_ident_basica', models.IntegerField(verbose_name='N\xfamero')),
                ('ano_ident_basica', models.SmallIntegerField(verbose_name='Ano')),
                ('data_apresentacao', models.DateField(null=True, verbose_name='Data Apresenta\xe7\xe3o', blank=True)),
                ('tipo_apresentacao', models.CharField(blank=True, max_length=1, null=True, verbose_name='Tipo de Apresenta\xe7\xe3o', choices=[(b'O', 'Oral'), (b'E', 'Escrita')])),
                ('data_publicacao', models.DateField(null=True, verbose_name='Data Publica\xe7\xe3o', blank=True)),
                ('numero_origem_externa', models.CharField(max_length=5, null=True, verbose_name='N\xfamero', blank=True)),
                ('ano_origem_externa', models.SmallIntegerField(null=True, verbose_name='Ano', blank=True)),
                ('data_origem_externa', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('apelido', models.CharField(max_length=50, null=True, verbose_name='Apelido', blank=True)),
                ('dias_prazo', models.IntegerField(null=True, verbose_name='Dias Prazo', blank=True)),
                ('data_fim_prazo', models.DateField(null=True, verbose_name='Data Fim Prazo', blank=True)),
                ('em_tramitacao', models.BooleanField(verbose_name='Em Tramita\xe7\xe3o?')),
                ('polemica', models.NullBooleanField(verbose_name='Mat\xe9ria Pol\xeamica?')),
                ('objeto', models.CharField(max_length=150, null=True, verbose_name='Objeto', blank=True)),
                ('complementar', models.NullBooleanField(verbose_name='\xc9 Complementar?')),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('indexacao', models.TextField(null=True, verbose_name='Indexa\xe7\xe3o', blank=True)),
                ('observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('resultado', models.TextField(null=True, blank=True)),
                ('anexadas', models.ManyToManyField(related_name='anexo_de', through='materia.Anexada', to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Mat\xe9ria Legislativa',
                'verbose_name_plural': 'Mat\xe9rias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='Numeracao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField()),
                ('numero_materia', models.CharField(max_length=5, verbose_name='N\xfamero')),
                ('ano_materia', models.SmallIntegerField(verbose_name='Ano')),
                ('data_materia', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Numera\xe7\xe3o',
                'verbose_name_plural': 'Numera\xe7\xf5es',
            },
        ),
        migrations.CreateModel(
            name='Orgao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('unidade_deliberativa', models.BooleanField(verbose_name='Unidade Deliberativa')),
                ('endereco', models.CharField(max_length=100, null=True, verbose_name='Endere\xe7o', blank=True)),
                ('telefone', models.CharField(max_length=50, null=True, verbose_name='Telefone', blank=True)),
            ],
            options={
                'verbose_name': '\xd3rg\xe3o',
                'verbose_name_plural': '\xd3rg\xe3os',
            },
        ),
        migrations.CreateModel(
            name='Origem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_conclusao', models.CharField(max_length=3, null=True, blank=True)),
                ('tipo_apresentacao', models.CharField(max_length=1, choices=[(b'O', 'Oral'), (b'E', 'Escrita')])),
                ('parecer', models.TextField(null=True, blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_envio', models.DateTimeField(null=True, verbose_name='Data de Envio')),
                ('data_recebimento', models.DateTimeField(null=True, verbose_name='Data de Incorpora\xe7\xe3o', blank=True)),
                ('descricao', models.CharField(max_length=100, verbose_name='Descri\xe7\xe3o')),
                ('data_devolucao', models.DateTimeField(null=True, verbose_name='Data de devolu\xe7\xe3o', blank=True)),
                ('justificativa_devolucao', models.CharField(max_length=200, null=True, verbose_name='Justificativa da Devolu\xe7\xe3o', blank=True)),
                ('numero_proposicao', models.IntegerField(null=True, verbose_name='', blank=True)),
                ('autor', models.ForeignKey(to='materia.Autor')),
                ('documento', models.ForeignKey(verbose_name='Documento', blank=True, to='materia.DocumentoAcessorio', null=True)),
                ('materia', models.ForeignKey(verbose_name='Mat\xe9ria', blank=True, to='materia.MateriaLegislativa', null=True)),
            ],
            options={
                'verbose_name': 'Proposi\xe7\xe3o',
                'verbose_name_plural': 'Proposi\xe7\xf5es',
            },
        ),
        migrations.CreateModel(
            name='RegimeTramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': 'Regime Tramita\xe7\xe3o',
                'verbose_name_plural': 'Regimes Tramita\xe7\xe3o',
            },
        ),
        migrations.CreateModel(
            name='Relatoria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_designacao_relator', models.DateField(verbose_name='Data Designa\xe7\xe3o')),
                ('data_destituicao_relator', models.DateField(null=True, verbose_name='Data Destitui\xe7\xe3o', blank=True)),
                ('comissao', models.ForeignKey(verbose_name='Localiza\xe7\xe3o Atual', blank=True, to='comissoes.Comissao', null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('parlamentar', models.ForeignKey(verbose_name='Parlamentar', to='parlamentares.Parlamentar')),
            ],
            options={
                'verbose_name': 'Relatoria',
                'verbose_name_plural': 'Relatorias',
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=60, verbose_name='Descri\xe7\xe3o')),
                ('indicador', models.CharField(max_length=1, verbose_name='Indicador da Tramita\xe7\xe3o', choices=[(b'F', 'Fim'), (b'R', 'Retorno')])),
            ],
            options={
                'verbose_name': 'Status de Tramita\xe7\xe3o',
                'verbose_name_plural': 'Status de Tramita\xe7\xe3o',
            },
        ),
        migrations.CreateModel(
            name='TipoAutor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
            ],
            options={
                'verbose_name': 'Tipo de Autor',
                'verbose_name_plural': 'Tipos de Autor',
            },
        ),
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla', models.CharField(max_length=5, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o ')),
                ('num_automatica', models.BooleanField()),
                ('quorum_minimo_votacao', models.IntegerField()),
            ],
            options={
                'verbose_name': 'Tipo de Mat\xe9ria Legislativa',
                'verbose_name_plural': 'Tipos de Mat\xe9rias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='TipoProposicao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
                ('materia_ou_documento', models.CharField(max_length=1, verbose_name='Gera', choices=[(b'M', 'Mat\xe9ria'), (b'D', 'Documento')])),
                ('modelo', models.CharField(max_length=50, verbose_name='Modelo XML')),
                ('tipo_documento', models.ForeignKey(verbose_name='Tipo Documento', blank=True, to='materia.TipoDocumento', null=True)),
                ('tipo_materia', models.ForeignKey(verbose_name='Tipo Mat\xe9ria', blank=True, to='materia.TipoMateriaLegislativa', null=True)),
            ],
            options={
                'verbose_name': 'Tipo de Proposi\xe7\xe3o',
                'verbose_name_plural': 'Tipos de Proposi\xe7\xf5es',
            },
        ),
        migrations.CreateModel(
            name='Tramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_tramitacao', models.DateField(null=True, verbose_name='Data Tramita\xe7\xe3o', blank=True)),
                ('data_encaminhamento', models.DateField(null=True, verbose_name='Data Encaminhamento', blank=True)),
                ('ultima', models.BooleanField()),
                ('urgente', models.BooleanField(verbose_name='Urgente ?')),
                ('turno', models.CharField(blank=True, max_length=1, null=True, verbose_name='Turno', choices=[(b'P', 'Primeiro'), (b'S', 'Segundo'), (b'\xc3\x9a', '\xdanico'), (b'L', 'Suplementar'), (b'F', 'Final'), (b'A', 'Vota\xe7\xe3o \xfanica em Regime de Urg\xeancia'), (b'B', '1\xaa Vota\xe7\xe3o'), (b'C', '2\xaa e 3\xaa Vota\xe7\xe3o')])),
                ('texto', models.TextField(null=True, verbose_name='Texto da A\xe7\xe3o', blank=True)),
                ('data_fim_prazo', models.DateField(null=True, verbose_name='Data Fim Prazo', blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('status', models.ForeignKey(verbose_name='Status', blank=True, to='materia.StatusTramitacao', null=True)),
            ],
            options={
                'verbose_name': 'Tramita\xe7\xe3o',
                'verbose_name_plural': 'Tramita\xe7\xf5es',
            },
        ),
        migrations.CreateModel(
            name='UnidadeTramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comissao', models.ForeignKey(verbose_name='Comiss\xe3o', blank=True, to='comissoes.Comissao', null=True)),
                ('orgao', models.ForeignKey(verbose_name='\xd3rg\xe3o', blank=True, to='materia.Orgao', null=True)),
                ('parlamentar', models.ForeignKey(verbose_name='Parlamentar', blank=True, to='parlamentares.Parlamentar', null=True)),
            ],
            options={
                'verbose_name': 'Unidade de Tramita\xe7\xe3o',
                'verbose_name_plural': 'Unidades de Tramita\xe7\xe3o',
            },
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unidade_tramitacao_destino',
            field=models.ForeignKey(related_name='+', verbose_name='Unidade Destino', blank=True, to='materia.UnidadeTramitacao', null=True),
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unidade_tramitacao_local',
            field=models.ForeignKey(related_name='+', verbose_name='Unidade Local', blank=True, to='materia.UnidadeTramitacao', null=True),
        ),
        migrations.AddField(
            model_name='relatoria',
            name='tipo_fim_relatoria',
            field=models.ForeignKey(verbose_name='Motivo Fim Relatoria', blank=True, to='materia.TipoFimRelatoria', null=True),
        ),
        migrations.AddField(
            model_name='proposicao',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo', to='materia.TipoProposicao'),
        ),
        migrations.AddField(
            model_name='parecer',
            name='relatoria',
            field=models.ForeignKey(to='materia.Relatoria'),
        ),
        migrations.AddField(
            model_name='numeracao',
            name='tipo_materia',
            field=models.ForeignKey(verbose_name='Tipo de Mat\xe9ria', to='materia.TipoMateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='local_origem_externa',
            field=models.ForeignKey(verbose_name='Local Origem', blank=True, to='materia.Origem', null=True),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='regime_tramitacao',
            field=models.ForeignKey(verbose_name='Regime Tramita\xe7\xe3o', to='materia.RegimeTramitacao'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='tipo_id_basica',
            field=models.ForeignKey(verbose_name='Tipo', to='materia.TipoMateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='tipo_origem_externa',
            field=models.ForeignKey(related_name='+', verbose_name='Tipo', blank=True, to='materia.TipoMateriaLegislativa', null=True),
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
            field=models.ForeignKey(verbose_name='Tipo', to='materia.TipoDocumento'),
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
            field=models.ForeignKey(verbose_name='Tipo', to='materia.TipoAutor'),
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
