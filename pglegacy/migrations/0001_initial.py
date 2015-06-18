# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AcompMateria',
            fields=[
                ('cod_cadastro', models.IntegerField(serialize=False, primary_key=True)),
                ('txt_email', models.CharField(max_length=40)),
                ('txt_nome', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'acomp_materia',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AndamentoSessao',
            fields=[
                ('cod_andamento_sessao', models.AutoField(serialize=False, primary_key=True)),
                ('nom_andamento', models.CharField(max_length=100)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'andamento_sessao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Anexada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dat_anexacao', models.DateField()),
                ('dat_desanexacao', models.DateField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'anexada',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AssuntoMateria',
            fields=[
                ('cod_assunto', models.IntegerField(serialize=False, primary_key=True)),
                ('des_assunto', models.CharField(max_length=200)),
                ('des_dispositivo', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'assunto_materia',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('cod_autor', models.AutoField(serialize=False, primary_key=True)),
                ('nom_autor', models.CharField(max_length=50, null=True, blank=True)),
                ('des_cargo', models.CharField(max_length=50, null=True, blank=True)),
                ('col_username', models.CharField(max_length=50, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'autor',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Autoria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_primeiro_autor', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'autoria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CargoComissao',
            fields=[
                ('cod_cargo', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_cargo', models.CharField(max_length=50)),
                ('ind_unico', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'cargo_comissao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='CargoMesa',
            fields=[
                ('cod_cargo', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_cargo', models.CharField(max_length=50)),
                ('ind_unico', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'cargo_mesa',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Coligacao',
            fields=[
                ('cod_coligacao', models.AutoField(serialize=False, primary_key=True)),
                ('nom_coligacao', models.CharField(max_length=50)),
                ('num_votos_coligacao', models.IntegerField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'coligacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Comissao',
            fields=[
                ('cod_comissao', models.AutoField(serialize=False, primary_key=True)),
                ('nom_comissao', models.CharField(max_length=60)),
                ('sgl_comissao', models.CharField(max_length=10)),
                ('dat_criacao', models.DateField()),
                ('dat_extincao', models.DateField(null=True, blank=True)),
                ('nom_apelido_temp', models.CharField(max_length=100, null=True, blank=True)),
                ('dat_instalacao_temp', models.DateField(null=True, blank=True)),
                ('dat_final_prevista_temp', models.DateField(null=True, blank=True)),
                ('dat_prorrogada_temp', models.DateField(null=True, blank=True)),
                ('dat_fim_comissao', models.DateField(null=True, blank=True)),
                ('nom_secretario', models.CharField(max_length=30, null=True, blank=True)),
                ('num_tel_reuniao', models.CharField(max_length=15, null=True, blank=True)),
                ('end_secretaria', models.CharField(max_length=100, null=True, blank=True)),
                ('num_tel_secretaria', models.CharField(max_length=15, null=True, blank=True)),
                ('num_fax_secretaria', models.CharField(max_length=15, null=True, blank=True)),
                ('des_agenda_reuniao', models.CharField(max_length=100, null=True, blank=True)),
                ('loc_reuniao', models.CharField(max_length=100, null=True, blank=True)),
                ('txt_finalidade', models.TextField(null=True, blank=True)),
                ('end_email', models.CharField(max_length=100, null=True, blank=True)),
                ('ind_unid_deliberativa', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'comissao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ComposicaoColigacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'composicao_coligacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ComposicaoComissao',
            fields=[
                ('cod_comp_comissao', models.AutoField(serialize=False, primary_key=True)),
                ('ind_titular', models.SmallIntegerField()),
                ('dat_designacao', models.DateField()),
                ('dat_desligamento', models.DateField(null=True, blank=True)),
                ('des_motivo_desligamento', models.CharField(max_length=150)),
                ('obs_composicao', models.CharField(max_length=150)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'composicao_comissao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ComposicaoMesa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'composicao_mesa',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Dependente',
            fields=[
                ('cod_dependente', models.AutoField(serialize=False, primary_key=True)),
                ('nom_dependente', models.CharField(max_length=50)),
                ('sex_dependente', models.CharField(max_length=1)),
                ('dat_nascimento', models.DateField(null=True, blank=True)),
                ('num_cpf', models.CharField(max_length=14, null=True, blank=True)),
                ('num_rg', models.CharField(max_length=15, null=True, blank=True)),
                ('num_tit_eleitor', models.CharField(max_length=15, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'dependente',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DespachoInicial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_ordem', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'despacho_inicial',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DocumentoAcessorio',
            fields=[
                ('cod_documento', models.AutoField(serialize=False, primary_key=True)),
                ('nom_documento', models.CharField(max_length=30)),
                ('dat_documento', models.DateField(null=True, blank=True)),
                ('nom_autor_documento', models.CharField(max_length=50, null=True, blank=True)),
                ('txt_ementa', models.TextField(null=True, blank=True)),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'documento_acessorio',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='ExpedienteSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('txt_expediente', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'expediente_sessao_plenaria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Filiacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dat_filiacao', models.DateField()),
                ('dat_desfiliacao', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'filiacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='LegislacaoCitada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('des_disposicoes', models.CharField(max_length=15, null=True, blank=True)),
                ('des_parte', models.CharField(max_length=8, null=True, blank=True)),
                ('des_livro', models.CharField(max_length=7, null=True, blank=True)),
                ('des_titulo', models.CharField(max_length=7, null=True, blank=True)),
                ('des_capitulo', models.CharField(max_length=7, null=True, blank=True)),
                ('des_secao', models.CharField(max_length=7, null=True, blank=True)),
                ('des_subsecao', models.CharField(max_length=7, null=True, blank=True)),
                ('des_artigo', models.CharField(max_length=4, null=True, blank=True)),
                ('des_paragrafo', models.CharField(max_length=3, null=True, blank=True)),
                ('des_inciso', models.CharField(max_length=10, null=True, blank=True)),
                ('des_alinea', models.CharField(max_length=3, null=True, blank=True)),
                ('des_item', models.CharField(max_length=3, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'legislacao_citada',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Legislatura',
            fields=[
                ('num_legislatura', models.IntegerField(serialize=False, primary_key=True)),
                ('dat_inicio', models.DateField()),
                ('dat_fim', models.DateField()),
                ('dat_eleicao', models.DateField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'legislatura',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Localidade',
            fields=[
                ('cod_localidade', models.IntegerField(serialize=False, primary_key=True)),
                ('nom_localidade', models.CharField(max_length=50)),
                ('nom_localidade_pesq', models.CharField(max_length=50)),
                ('tip_localidade', models.CharField(max_length=1)),
                ('sgl_uf', models.CharField(max_length=2)),
                ('sgl_regiao', models.CharField(max_length=2)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'localidade',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Mandato',
            fields=[
                ('cod_mandato', models.AutoField(serialize=False, primary_key=True)),
                ('tip_causa_fim_mandato', models.SmallIntegerField(null=True, blank=True)),
                ('dat_fim_mandato', models.DateField(null=True, blank=True)),
                ('num_votos_recebidos', models.IntegerField(null=True, blank=True)),
                ('dat_expedicao_diploma', models.DateField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'mandato',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MateriaAssunto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'materia_assunto',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MateriaLegislativa',
            fields=[
                ('cod_materia', models.AutoField(serialize=False, primary_key=True)),
                ('num_ident_basica', models.CharField(max_length=6)),
                ('ano_ident_basica', models.SmallIntegerField()),
                ('dat_apresentacao', models.DateField(null=True, blank=True)),
                ('tip_apresentacao', models.CharField(max_length=1, null=True, blank=True)),
                ('dat_publicacao', models.DateField(null=True, blank=True)),
                ('num_origem_externa', models.CharField(max_length=9, null=True, blank=True)),
                ('ano_origem_externa', models.SmallIntegerField(null=True, blank=True)),
                ('dat_origem_externa', models.DateField(null=True, blank=True)),
                ('nom_apelido', models.CharField(max_length=50, null=True, blank=True)),
                ('num_dias_prazo', models.SmallIntegerField(null=True, blank=True)),
                ('dat_fim_prazo', models.DateField(null=True, blank=True)),
                ('ind_tramitacao', models.SmallIntegerField()),
                ('ind_polemica', models.SmallIntegerField(null=True, blank=True)),
                ('des_objeto', models.CharField(max_length=150, null=True, blank=True)),
                ('ind_complementar', models.SmallIntegerField(null=True, blank=True)),
                ('txt_ementa', models.TextField()),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
                ('txt_resultado', models.TextField(null=True, blank=True)),
            ],
            options={
                'db_table': 'materia_legislativa',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='MesaSessaoPlenaria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'mesa_sessao_plenaria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='NivelInstrucao',
            fields=[
                ('cod_nivel_instrucao', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_nivel_instrucao', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'nivel_instrucao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='NormaJuridica',
            fields=[
                ('cod_norma', models.AutoField(serialize=False, primary_key=True)),
                ('num_norma', models.IntegerField()),
                ('ano_norma', models.SmallIntegerField()),
                ('tip_esfera_federacao', models.CharField(max_length=1)),
                ('dat_norma', models.DateField(null=True, blank=True)),
                ('dat_publicacao', models.DateField(null=True, blank=True)),
                ('des_veiculo_publicacao', models.CharField(max_length=30, null=True, blank=True)),
                ('num_pag_inicio_publ', models.IntegerField(null=True, blank=True)),
                ('num_pag_fim_publ', models.IntegerField(null=True, blank=True)),
                ('txt_ementa', models.TextField()),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('ind_complemento', models.SmallIntegerField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'norma_juridica',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Numeracao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_ordem', models.SmallIntegerField()),
                ('num_materia', models.CharField(max_length=6)),
                ('ano_materia', models.SmallIntegerField()),
                ('dat_materia', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'numeracao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Oradores',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_ordem', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'oradores',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OrdemDia',
            fields=[
                ('cod_ordem', models.AutoField(serialize=False, primary_key=True)),
                ('dat_ordem', models.DateField()),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
                ('num_ordem', models.IntegerField()),
                ('txt_resultado', models.TextField(null=True, blank=True)),
                ('tip_votacao', models.IntegerField()),
            ],
            options={
                'db_table': 'ordem_dia',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='OrdemDiaPresenca',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField()),
                ('dat_ordem', models.DateField()),
            ],
            options={
                'db_table': 'ordem_dia_presenca',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Orgao',
            fields=[
                ('cod_orgao', models.AutoField(serialize=False, primary_key=True)),
                ('nom_orgao', models.CharField(max_length=60)),
                ('sgl_orgao', models.CharField(max_length=10)),
                ('ind_unid_deliberativa', models.SmallIntegerField()),
                ('end_orgao', models.CharField(max_length=100, null=True, blank=True)),
                ('num_tel_orgao', models.CharField(max_length=50, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'orgao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Origem',
            fields=[
                ('cod_origem', models.AutoField(serialize=False, primary_key=True)),
                ('sgl_origem', models.CharField(max_length=10)),
                ('nom_origem', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'origem',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Parecer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tip_conclusao', models.CharField(max_length=3, null=True, blank=True)),
                ('tip_apresentacao', models.CharField(max_length=1)),
                ('txt_parecer', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'parecer',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Parlamentar',
            fields=[
                ('cod_parlamentar', models.AutoField(serialize=False, primary_key=True)),
                ('nom_completo', models.CharField(max_length=50)),
                ('nom_parlamentar', models.CharField(max_length=50, null=True, blank=True)),
                ('sex_parlamentar', models.CharField(max_length=1)),
                ('dat_nascimento', models.DateField(null=True, blank=True)),
                ('num_cpf', models.CharField(max_length=14, null=True, blank=True)),
                ('num_rg', models.CharField(max_length=15, null=True, blank=True)),
                ('num_tit_eleitor', models.CharField(max_length=15, null=True, blank=True)),
                ('cod_casa', models.IntegerField()),
                ('num_gab_parlamentar', models.CharField(max_length=10, null=True, blank=True)),
                ('num_tel_parlamentar', models.CharField(max_length=50, null=True, blank=True)),
                ('num_fax_parlamentar', models.CharField(max_length=50, null=True, blank=True)),
                ('end_residencial', models.CharField(max_length=100, null=True, blank=True)),
                ('num_cep_resid', models.CharField(max_length=9, null=True, blank=True)),
                ('num_tel_resid', models.CharField(max_length=50, null=True, blank=True)),
                ('num_fax_resid', models.CharField(max_length=50, null=True, blank=True)),
                ('end_web', models.CharField(max_length=100, null=True, blank=True)),
                ('nom_profissao', models.CharField(max_length=50, null=True, blank=True)),
                ('end_email', models.CharField(max_length=100, null=True, blank=True)),
                ('des_local_atuacao', models.CharField(max_length=100, null=True, blank=True)),
                ('ind_ativo', models.SmallIntegerField()),
                ('ind_unid_deliberativa', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'parlamentar',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Partido',
            fields=[
                ('cod_partido', models.AutoField(serialize=False, primary_key=True)),
                ('sgl_partido', models.CharField(max_length=9)),
                ('nom_partido', models.CharField(max_length=50)),
                ('dat_criacao', models.DateField(null=True, blank=True)),
                ('dat_extincao', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'partido',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='PeriodoCompComissao',
            fields=[
                ('cod_periodo_comp', models.AutoField(serialize=False, primary_key=True)),
                ('dat_inicio_periodo', models.DateField()),
                ('dat_fim_periodo', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'periodo_comp_comissao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Proposicao',
            fields=[
                ('cod_proposicao', models.AutoField(serialize=False, primary_key=True)),
                ('dat_envio', models.DateTimeField()),
                ('dat_recebimento', models.DateTimeField(null=True, blank=True)),
                ('txt_descricao', models.CharField(max_length=100)),
                ('cod_mat_ou_doc', models.IntegerField(null=True, blank=True)),
                ('dat_devolucao', models.DateTimeField(null=True, blank=True)),
                ('txt_justif_devolucao', models.CharField(max_length=200, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'proposicao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RegimeTramitacao',
            fields=[
                ('cod_regime_tramitacao', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_regime_tramitacao', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'regime_tramitacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RegistroVotacao',
            fields=[
                ('cod_votacao', models.AutoField(serialize=False, primary_key=True)),
                ('num_votos_sim', models.SmallIntegerField()),
                ('num_votos_nao', models.SmallIntegerField()),
                ('num_abstencao', models.SmallIntegerField()),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'registro_votacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RegistroVotacaoParlamentar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField()),
                ('vot_parlamentar', models.CharField(max_length=10)),
            ],
            options={
                'db_table': 'registro_votacao_parlamentar',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Relatoria',
            fields=[
                ('cod_relatoria', models.AutoField(serialize=False, primary_key=True)),
                ('dat_desig_relator', models.DateField()),
                ('dat_destit_relator', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'relatoria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SessaoLegislativa',
            fields=[
                ('cod_sessao_leg', models.AutoField(serialize=False, primary_key=True)),
                ('num_sessao_leg', models.SmallIntegerField()),
                ('tip_sessao_leg', models.CharField(max_length=1)),
                ('dat_inicio', models.DateField()),
                ('dat_fim', models.DateField()),
                ('dat_inicio_intervalo', models.DateField(null=True, blank=True)),
                ('dat_fim_intervalo', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'sessao_legislativa',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenaria',
            fields=[
                ('cod_sessao_plen', models.IntegerField(serialize=False, primary_key=True)),
                ('tip_expediente', models.CharField(max_length=10)),
                ('dat_inicio_sessao', models.DateField()),
                ('dia_sessao', models.CharField(max_length=15)),
                ('hr_inicio_sessao', models.CharField(max_length=5)),
                ('hr_fim_sessao', models.CharField(max_length=5, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
                ('num_sessao_plen', models.IntegerField()),
                ('dat_fim_sessao', models.DateField(null=True, blank=True)),
            ],
            options={
                'db_table': 'sessao_plenaria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SessaoPlenariaPresenca',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ind_excluido', models.SmallIntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'sessao_plenaria_presenca',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='StatusTramitacao',
            fields=[
                ('cod_status', models.AutoField(serialize=False, primary_key=True)),
                ('sgl_status', models.CharField(max_length=10)),
                ('des_status', models.CharField(max_length=60)),
                ('ind_fim_tramitacao', models.SmallIntegerField()),
                ('ind_retorno_tramitacao', models.SmallIntegerField()),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'status_tramitacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoAfastamento',
            fields=[
                ('tip_afastamento', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_afastamento', models.CharField(max_length=50)),
                ('ind_afastamento', models.SmallIntegerField()),
                ('ind_fim_mandato', models.SmallIntegerField()),
                ('des_dispositivo', models.CharField(max_length=50, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_afastamento',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoAutor',
            fields=[
                ('tip_autor', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_tipo_autor', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_autor',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoComissao',
            fields=[
                ('tip_comissao', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('nom_tipo_comissao', models.CharField(max_length=50)),
                ('sgl_natureza_comissao', models.CharField(max_length=1)),
                ('sgl_tipo_comissao', models.CharField(max_length=10)),
                ('des_dispositivo_regimental', models.CharField(max_length=50, null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_comissao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoDependente',
            fields=[
                ('tip_dependente', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_tipo_dependente', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_dependente',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('tip_documento', models.AutoField(serialize=False, primary_key=True)),
                ('des_tipo_documento', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_documento',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoExpediente',
            fields=[
                ('cod_expediente', models.AutoField(serialize=False, primary_key=True)),
                ('nom_expediente', models.CharField(max_length=100)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_expediente',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoFimRelatoria',
            fields=[
                ('tip_fim_relatoria', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_fim_relatoria', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_fim_relatoria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoMateriaLegislativa',
            fields=[
                ('tip_materia', models.AutoField(serialize=False, primary_key=True)),
                ('sgl_tipo_materia', models.CharField(max_length=5)),
                ('des_tipo_materia', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_materia_legislativa',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoNormaJuridica',
            fields=[
                ('tip_norma', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('sgl_tipo_norma', models.CharField(max_length=3)),
                ('des_tipo_norma', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_norma_juridica',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoProposicao',
            fields=[
                ('tip_proposicao', models.AutoField(serialize=False, primary_key=True)),
                ('des_tipo_proposicao', models.CharField(max_length=50)),
                ('ind_mat_ou_doc', models.CharField(max_length=1)),
                ('tip_mat_ou_doc', models.IntegerField()),
                ('nom_modelo', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_proposicao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoResultadoVotacao',
            fields=[
                ('tip_resultado_votacao', models.AutoField(serialize=False, primary_key=True)),
                ('nom_resultado', models.CharField(max_length=100)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_resultado_votacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoSessaoPlenaria',
            fields=[
                ('tip_sessao', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('nom_sessao', models.CharField(max_length=30)),
                ('ind_excluido', models.SmallIntegerField()),
                ('num_minimo', models.IntegerField()),
            ],
            options={
                'db_table': 'tipo_sessao_plenaria',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='TipoSituacaoMilitar',
            fields=[
                ('tip_situacao_militar', models.SmallIntegerField(serialize=False, primary_key=True)),
                ('des_tipo_situacao', models.CharField(max_length=50)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tipo_situacao_militar',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Tramitacao',
            fields=[
                ('cod_tramitacao', models.AutoField(serialize=False, primary_key=True)),
                ('dat_tramitacao', models.DateField(null=True, blank=True)),
                ('dat_encaminha', models.DateField(null=True, blank=True)),
                ('ind_ult_tramitacao', models.SmallIntegerField()),
                ('ind_urgencia', models.SmallIntegerField()),
                ('sgl_turno', models.CharField(max_length=1, null=True, blank=True)),
                ('txt_tramitacao', models.TextField(null=True, blank=True)),
                ('dat_fim_prazo', models.DateField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'tramitacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='UnidadeTramitacao',
            fields=[
                ('cod_unid_tramitacao', models.AutoField(serialize=False, primary_key=True)),
                ('cod_parlamentar', models.IntegerField(null=True, blank=True)),
                ('ind_excluido', models.SmallIntegerField()),
            ],
            options={
                'db_table': 'unidade_tramitacao',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VinculoNormaJuridica',
            fields=[
                ('cod_vinculo', models.AutoField(serialize=False, primary_key=True)),
                ('tip_vinculo', models.CharField(max_length=1, null=True, blank=True)),
                ('ind_excluido', models.CharField(max_length=1)),
            ],
            options={
                'db_table': 'vinculo_norma_juridica',
                'managed': False,
            },
        ),
    ]
