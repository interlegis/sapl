# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin sqlcustom [app_label]'
# into your database.
from __future__ import unicode_literals

from django.db import models


class AcompMateria(models.Model):
    cod_cadastro = models.IntegerField(primary_key=True)
    cod_regime_tramitacao = models.ForeignKey('RegimeTramitacao', db_column='cod_regime_tramitacao')
    cod_materia = models.ForeignKey('MateriaLegislativa', db_column='cod_materia')
    txt_email = models.CharField(max_length=40)
    txt_nome = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'acomp_materia'


class AndamentoSessao(models.Model):
    cod_andamento_sessao = models.AutoField(primary_key=True)
    nom_andamento = models.CharField(max_length=100)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'andamento_sessao'


class Anexada(models.Model):
    cod_materia_principal = models.ForeignKey('MateriaLegislativa', db_column='cod_materia_principal')
    cod_materia_anexada = models.ForeignKey('MateriaLegislativa', db_column='cod_materia_anexada')
    dat_anexacao = models.DateField()
    dat_desanexacao = models.DateField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'anexada'
        unique_together = (('cod_materia_principal', 'cod_materia_anexada'),)


class AssuntoMateria(models.Model):
    cod_assunto = models.IntegerField(primary_key=True)
    des_assunto = models.CharField(max_length=200)
    des_dispositivo = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'assunto_materia'


class Autor(models.Model):
    cod_autor = models.AutoField(primary_key=True)
    cod_partido = models.ForeignKey('Partido', db_column='cod_partido', blank=True, null=True)
    cod_comissao = models.ForeignKey('Comissao', db_column='cod_comissao', blank=True, null=True)
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar', blank=True, null=True)
    tip_autor = models.ForeignKey('TipoAutor', db_column='tip_autor')
    nom_autor = models.CharField(max_length=50, blank=True, null=True)
    des_cargo = models.CharField(max_length=50, blank=True, null=True)
    col_username = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'autor'


class Autoria(models.Model):
    cod_autor = models.ForeignKey(Autor, db_column='cod_autor')
    cod_materia = models.ForeignKey('MateriaLegislativa', db_column='cod_materia')
    ind_primeiro_autor = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'autoria'
        unique_together = (('cod_autor', 'cod_materia'),)


class CargoComissao(models.Model):
    cod_cargo = models.SmallIntegerField(primary_key=True)
    des_cargo = models.CharField(max_length=50)
    ind_unico = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'cargo_comissao'


class CargoMesa(models.Model):
    cod_cargo = models.SmallIntegerField(primary_key=True)
    des_cargo = models.CharField(max_length=50)
    ind_unico = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'cargo_mesa'


class Coligacao(models.Model):
    cod_coligacao = models.AutoField(primary_key=True)
    num_legislatura = models.ForeignKey('Legislatura', db_column='num_legislatura')
    nom_coligacao = models.CharField(max_length=50)
    num_votos_coligacao = models.IntegerField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'coligacao'


class Comissao(models.Model):
    cod_comissao = models.AutoField(primary_key=True)
    tip_comissao = models.ForeignKey('TipoComissao', db_column='tip_comissao')
    nom_comissao = models.CharField(max_length=60)
    sgl_comissao = models.CharField(max_length=10)
    dat_criacao = models.DateField()
    dat_extincao = models.DateField(blank=True, null=True)
    nom_apelido_temp = models.CharField(max_length=100, blank=True, null=True)
    dat_instalacao_temp = models.DateField(blank=True, null=True)
    dat_final_prevista_temp = models.DateField(blank=True, null=True)
    dat_prorrogada_temp = models.DateField(blank=True, null=True)
    dat_fim_comissao = models.DateField(blank=True, null=True)
    nom_secretario = models.CharField(max_length=30, blank=True, null=True)
    num_tel_reuniao = models.CharField(max_length=15, blank=True, null=True)
    end_secretaria = models.CharField(max_length=100, blank=True, null=True)
    num_tel_secretaria = models.CharField(max_length=15, blank=True, null=True)
    num_fax_secretaria = models.CharField(max_length=15, blank=True, null=True)
    des_agenda_reuniao = models.CharField(max_length=100, blank=True, null=True)
    loc_reuniao = models.CharField(max_length=100, blank=True, null=True)
    txt_finalidade = models.TextField(blank=True, null=True)
    end_email = models.CharField(max_length=100, blank=True, null=True)
    ind_unid_deliberativa = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'comissao'


class ComposicaoColigacao(models.Model):
    cod_partido = models.ForeignKey('Partido', db_column='cod_partido')
    cod_coligacao = models.ForeignKey(Coligacao, db_column='cod_coligacao')
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_coligacao'
        unique_together = (('cod_partido', 'cod_coligacao'),)


class ComposicaoComissao(models.Model):
    cod_comp_comissao = models.AutoField(primary_key=True)
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    cod_comissao = models.ForeignKey(Comissao, db_column='cod_comissao')
    cod_periodo_comp = models.ForeignKey('PeriodoCompComissao', db_column='cod_periodo_comp')
    cod_cargo = models.ForeignKey(CargoComissao, db_column='cod_cargo')
    ind_titular = models.SmallIntegerField()
    dat_designacao = models.DateField()
    dat_desligamento = models.DateField(blank=True, null=True)
    des_motivo_desligamento = models.CharField(max_length=150)
    obs_composicao = models.CharField(max_length=150)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_comissao'


class ComposicaoMesa(models.Model):
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    cod_sessao_leg = models.ForeignKey('SessaoLegislativa', db_column='cod_sessao_leg')
    cod_cargo = models.ForeignKey(CargoMesa, db_column='cod_cargo')
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_mesa'
        unique_together = (('cod_parlamentar', 'cod_sessao_leg', 'cod_cargo'),)


class Dependente(models.Model):
    cod_dependente = models.AutoField(primary_key=True)
    tip_dependente = models.ForeignKey('TipoDependente', db_column='tip_dependente')
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    nom_dependente = models.CharField(max_length=50)
    sex_dependente = models.CharField(max_length=1)
    dat_nascimento = models.DateField(blank=True, null=True)
    num_cpf = models.CharField(max_length=14, blank=True, null=True)
    num_rg = models.CharField(max_length=15, blank=True, null=True)
    num_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'dependente'


class DespachoInicial(models.Model):
    cod_materia = models.ForeignKey('MateriaLegislativa', db_column='cod_materia')
    num_ordem = models.SmallIntegerField()
    cod_comissao = models.ForeignKey(Comissao, db_column='cod_comissao')
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'despacho_inicial'
        unique_together = (('cod_materia', 'num_ordem'),)


class DocumentoAcessorio(models.Model):
    cod_documento = models.AutoField(primary_key=True)
    cod_materia = models.ForeignKey('MateriaLegislativa', db_column='cod_materia')
    tip_documento = models.ForeignKey('TipoDocumento', db_column='tip_documento')
    nom_documento = models.CharField(max_length=30)
    dat_documento = models.DateField(blank=True, null=True)
    nom_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_ementa = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'documento_acessorio'


class ExpedienteSessaoPlenaria(models.Model):
    cod_sessao_plen = models.ForeignKey('SessaoPlenaria', db_column='cod_sessao_plen')
    cod_expediente = models.ForeignKey('TipoExpediente', db_column='cod_expediente')
    txt_expediente = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'expediente_sessao_plenaria'
        unique_together = (('cod_sessao_plen', 'cod_expediente'),)


class Filiacao(models.Model):
    dat_filiacao = models.DateField()
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    cod_partido = models.ForeignKey('Partido', db_column='cod_partido')
    dat_desfiliacao = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'filiacao'
        unique_together = (('dat_filiacao', 'cod_parlamentar', 'cod_partido'),)


class LegislacaoCitada(models.Model):
    cod_materia = models.ForeignKey('MateriaLegislativa', db_column='cod_materia')
    cod_norma = models.ForeignKey('NormaJuridica', db_column='cod_norma')
    des_disposicoes = models.CharField(max_length=15, blank=True, null=True)
    des_parte = models.CharField(max_length=8, blank=True, null=True)
    des_livro = models.CharField(max_length=7, blank=True, null=True)
    des_titulo = models.CharField(max_length=7, blank=True, null=True)
    des_capitulo = models.CharField(max_length=7, blank=True, null=True)
    des_secao = models.CharField(max_length=7, blank=True, null=True)
    des_subsecao = models.CharField(max_length=7, blank=True, null=True)
    des_artigo = models.CharField(max_length=4, blank=True, null=True)
    des_paragrafo = models.CharField(max_length=3, blank=True, null=True)
    des_inciso = models.CharField(max_length=10, blank=True, null=True)
    des_alinea = models.CharField(max_length=3, blank=True, null=True)
    des_item = models.CharField(max_length=3, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'legislacao_citada'
        unique_together = (('cod_materia', 'cod_norma'),)


class Legislatura(models.Model):
    num_legislatura = models.IntegerField(primary_key=True)
    dat_inicio = models.DateField()
    dat_fim = models.DateField()
    dat_eleicao = models.DateField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'legislatura'


class Localidade(models.Model):
    cod_localidade = models.IntegerField(primary_key=True)
    nom_localidade = models.CharField(max_length=50)
    nom_localidade_pesq = models.CharField(max_length=50)
    tip_localidade = models.CharField(max_length=1)
    sgl_uf = models.CharField(max_length=2)
    sgl_regiao = models.CharField(max_length=2)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'localidade'


class Mandato(models.Model):
    cod_mandato = models.AutoField(primary_key=True)
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    tip_afastamento = models.ForeignKey('TipoAfastamento', db_column='tip_afastamento')
    num_legislatura = models.ForeignKey(Legislatura, db_column='num_legislatura')
    cod_coligacao = models.ForeignKey(Coligacao, db_column='cod_coligacao')
    tip_causa_fim_mandato = models.SmallIntegerField(blank=True, null=True)
    dat_fim_mandato = models.DateField(blank=True, null=True)
    num_votos_recebidos = models.IntegerField(blank=True, null=True)
    dat_expedicao_diploma = models.DateField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'mandato'


class MateriaAssunto(models.Model):
    cod_assunto = models.ForeignKey(AssuntoMateria, db_column='cod_assunto')
    cod_materia = models.ForeignKey('MateriaLegislativa', db_column='cod_materia')
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'materia_assunto'
        unique_together = (('cod_assunto', 'cod_materia'),)


class MateriaLegislativa(models.Model):
    cod_materia = models.AutoField(primary_key=True)
    tip_id_basica = models.ForeignKey('TipoMateriaLegislativa', db_column='tip_id_basica')
    num_ident_basica = models.CharField(max_length=6)
    ano_ident_basica = models.SmallIntegerField()
    dat_apresentacao = models.DateField(blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1, blank=True, null=True)
    cod_regime_tramitacao = models.ForeignKey('RegimeTramitacao', db_column='cod_regime_tramitacao')
    dat_publicacao = models.DateField(blank=True, null=True)
    tip_origem_externa = models.ForeignKey('TipoMateriaLegislativa', db_column='tip_origem_externa', blank=True, null=True)
    num_origem_externa = models.CharField(max_length=9, blank=True, null=True)
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True)
    dat_origem_externa = models.DateField(blank=True, null=True)
    cod_local_origem_externa = models.ForeignKey('Origem', db_column='cod_local_origem_externa', blank=True, null=True)
    nom_apelido = models.CharField(max_length=50, blank=True, null=True)
    num_dias_prazo = models.SmallIntegerField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_tramitacao = models.SmallIntegerField()
    ind_polemica = models.SmallIntegerField(blank=True, null=True)
    des_objeto = models.CharField(max_length=150, blank=True, null=True)
    ind_complementar = models.SmallIntegerField(blank=True, null=True)
    txt_ementa = models.TextField()
    txt_indexacao = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()
    txt_resultado = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'materia_legislativa'


class MesaSessaoPlenaria(models.Model):
    cod_cargo = models.ForeignKey(CargoMesa, db_column='cod_cargo')
    cod_sessao_leg = models.ForeignKey('SessaoLegislativa', db_column='cod_sessao_leg')
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    cod_sessao_plen = models.ForeignKey('SessaoPlenaria', db_column='cod_sessao_plen')
    ind_excluido = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mesa_sessao_plenaria'
        unique_together = (('cod_cargo', 'cod_sessao_leg', 'cod_parlamentar', 'cod_sessao_plen'),)


class NivelInstrucao(models.Model):
    cod_nivel_instrucao = models.SmallIntegerField(primary_key=True)
    des_nivel_instrucao = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'nivel_instrucao'


class NormaJuridica(models.Model):
    cod_norma = models.AutoField(primary_key=True)
    tip_norma = models.ForeignKey('TipoNormaJuridica', db_column='tip_norma')
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia', blank=True, null=True)
    num_norma = models.IntegerField()
    ano_norma = models.SmallIntegerField()
    tip_esfera_federacao = models.CharField(max_length=1)
    dat_norma = models.DateField(blank=True, null=True)
    dat_publicacao = models.DateField(blank=True, null=True)
    des_veiculo_publicacao = models.CharField(max_length=30, blank=True, null=True)
    num_pag_inicio_publ = models.IntegerField(blank=True, null=True)
    num_pag_fim_publ = models.IntegerField(blank=True, null=True)
    txt_ementa = models.TextField()
    txt_indexacao = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_complemento = models.SmallIntegerField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'norma_juridica'


class Numeracao(models.Model):
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia')
    num_ordem = models.SmallIntegerField()
    tip_materia = models.ForeignKey('TipoMateriaLegislativa', db_column='tip_materia')
    num_materia = models.CharField(max_length=6)
    ano_materia = models.SmallIntegerField()
    dat_materia = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'numeracao'
        unique_together = (('cod_materia', 'num_ordem'),)


class Oradores(models.Model):
    cod_sessao_plen = models.ForeignKey('SessaoPlenaria', db_column='cod_sessao_plen')
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    num_ordem = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'oradores'
        unique_together = (('cod_sessao_plen', 'cod_parlamentar'),)


class OrdemDia(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.ForeignKey('SessaoPlenaria', db_column='cod_sessao_plen')
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia')
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'ordem_dia'


class OrdemDiaPresenca(models.Model):
    cod_parlamentar = models.ForeignKey('Parlamentar', db_column='cod_parlamentar')
    ind_excluido = models.SmallIntegerField()
    dat_ordem = models.DateField()

    class Meta:
        managed = False
        db_table = 'ordem_dia_presenca'


class Orgao(models.Model):
    cod_orgao = models.AutoField(primary_key=True)
    nom_orgao = models.CharField(max_length=60)
    sgl_orgao = models.CharField(max_length=10)
    ind_unid_deliberativa = models.SmallIntegerField()
    end_orgao = models.CharField(max_length=100, blank=True, null=True)
    num_tel_orgao = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'orgao'


class Origem(models.Model):
    cod_origem = models.AutoField(primary_key=True)
    sgl_origem = models.CharField(max_length=10)
    nom_origem = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'origem'


class Parecer(models.Model):
    cod_relatoria = models.ForeignKey('Relatoria', db_column='cod_relatoria')
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia')
    tip_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1)
    txt_parecer = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'parecer'
        unique_together = (('cod_relatoria', 'cod_materia'),)


class Parlamentar(models.Model):
    cod_parlamentar = models.AutoField(primary_key=True)
    cod_nivel_instrucao = models.ForeignKey(NivelInstrucao, db_column='cod_nivel_instrucao', blank=True, null=True)
    tip_situacao_militar = models.ForeignKey('TipoSituacaoMilitar', db_column='tip_situacao_militar', blank=True, null=True)
    nom_completo = models.CharField(max_length=50)
    nom_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    sex_parlamentar = models.CharField(max_length=1)
    dat_nascimento = models.DateField(blank=True, null=True)
    num_cpf = models.CharField(max_length=14, blank=True, null=True)
    num_rg = models.CharField(max_length=15, blank=True, null=True)
    num_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)
    cod_casa = models.IntegerField()
    num_gab_parlamentar = models.CharField(max_length=10, blank=True, null=True)
    num_tel_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    num_fax_parlamentar = models.CharField(max_length=50, blank=True, null=True)
    end_residencial = models.CharField(max_length=100, blank=True, null=True)
    cod_localidade_resid = models.ForeignKey(Localidade, db_column='cod_localidade_resid', blank=True, null=True)
    num_cep_resid = models.CharField(max_length=9, blank=True, null=True)
    num_tel_resid = models.CharField(max_length=50, blank=True, null=True)
    num_fax_resid = models.CharField(max_length=50, blank=True, null=True)
    end_web = models.CharField(max_length=100, blank=True, null=True)
    nom_profissao = models.CharField(max_length=50, blank=True, null=True)
    end_email = models.CharField(max_length=100, blank=True, null=True)
    des_local_atuacao = models.CharField(max_length=100, blank=True, null=True)
    ind_ativo = models.SmallIntegerField()
    ind_unid_deliberativa = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'parlamentar'


class Partido(models.Model):
    cod_partido = models.AutoField(primary_key=True)
    sgl_partido = models.CharField(max_length=9)
    nom_partido = models.CharField(max_length=50)
    dat_criacao = models.DateField(blank=True, null=True)
    dat_extincao = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'partido'


class PeriodoCompComissao(models.Model):
    cod_periodo_comp = models.AutoField(primary_key=True)
    dat_inicio_periodo = models.DateField()
    dat_fim_periodo = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'periodo_comp_comissao'


class Proposicao(models.Model):
    cod_proposicao = models.AutoField(primary_key=True)
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia', blank=True, null=True)
    cod_autor = models.ForeignKey(Autor, db_column='cod_autor')
    tip_proposicao = models.ForeignKey('TipoProposicao', db_column='tip_proposicao')
    dat_envio = models.DateTimeField()
    dat_recebimento = models.DateTimeField(blank=True, null=True)
    txt_descricao = models.CharField(max_length=100)
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)
    dat_devolucao = models.DateTimeField(blank=True, null=True)
    txt_justif_devolucao = models.CharField(max_length=200, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'proposicao'


class RegimeTramitacao(models.Model):
    cod_regime_tramitacao = models.SmallIntegerField(primary_key=True)
    des_regime_tramitacao = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'regime_tramitacao'


class RegistroVotacao(models.Model):
    cod_votacao = models.AutoField(primary_key=True)
    tip_resultado_votacao = models.ForeignKey('TipoResultadoVotacao', db_column='tip_resultado_votacao')
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia')
    cod_ordem = models.ForeignKey(OrdemDia, db_column='cod_ordem')
    num_votos_sim = models.SmallIntegerField()
    num_votos_nao = models.SmallIntegerField()
    num_abstencao = models.SmallIntegerField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'registro_votacao'


class RegistroVotacaoParlamentar(models.Model):
    cod_votacao = models.ForeignKey(RegistroVotacao, db_column='cod_votacao')
    cod_parlamentar = models.ForeignKey(Parlamentar, db_column='cod_parlamentar')
    ind_excluido = models.SmallIntegerField()
    vot_parlamentar = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'registro_votacao_parlamentar'
        unique_together = (('cod_votacao', 'cod_parlamentar'),)


class Relatoria(models.Model):
    cod_relatoria = models.AutoField(primary_key=True)
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia')
    cod_parlamentar = models.ForeignKey(Parlamentar, db_column='cod_parlamentar')
    tip_fim_relatoria = models.ForeignKey('TipoFimRelatoria', db_column='tip_fim_relatoria', blank=True, null=True)
    cod_comissao = models.ForeignKey(Comissao, db_column='cod_comissao', blank=True, null=True)
    dat_desig_relator = models.DateField()
    dat_destit_relator = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'relatoria'


class SessaoLegislativa(models.Model):
    cod_sessao_leg = models.AutoField(primary_key=True)
    num_legislatura = models.ForeignKey(Legislatura, db_column='num_legislatura')
    num_sessao_leg = models.SmallIntegerField()
    tip_sessao_leg = models.CharField(max_length=1)
    dat_inicio = models.DateField()
    dat_fim = models.DateField()
    dat_inicio_intervalo = models.DateField(blank=True, null=True)
    dat_fim_intervalo = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'sessao_legislativa'


class SessaoPlenaria(models.Model):
    cod_sessao_plen = models.IntegerField(primary_key=True)
    num_legislatura = models.ForeignKey(Legislatura, db_column='num_legislatura')
    cod_ordem = models.ForeignKey(OrdemDia, db_column='cod_ordem')
    cod_andamento_sessao = models.ForeignKey(AndamentoSessao, db_column='cod_andamento_sessao', blank=True, null=True)
    tip_sessao = models.ForeignKey('TipoSessaoPlenaria', db_column='tip_sessao')
    cod_sessao_leg = models.ForeignKey(SessaoLegislativa, db_column='cod_sessao_leg')
    tip_expediente = models.CharField(max_length=10)
    dat_inicio_sessao = models.DateField()
    dia_sessao = models.CharField(max_length=15)
    hr_inicio_sessao = models.CharField(max_length=5)
    hr_fim_sessao = models.CharField(max_length=5, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()
    num_sessao_plen = models.IntegerField()
    dat_fim_sessao = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sessao_plenaria'


class SessaoPlenariaPresenca(models.Model):
    cod_sessao_plen = models.ForeignKey(SessaoPlenaria, db_column='cod_sessao_plen')
    cod_parlamentar = models.ForeignKey(Parlamentar, db_column='cod_parlamentar')
    ind_excluido = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sessao_plenaria_presenca'
        unique_together = (('cod_sessao_plen', 'cod_parlamentar'),)


class StatusTramitacao(models.Model):
    cod_status = models.AutoField(primary_key=True)
    sgl_status = models.CharField(max_length=10)
    des_status = models.CharField(max_length=60)
    ind_fim_tramitacao = models.SmallIntegerField()
    ind_retorno_tramitacao = models.SmallIntegerField()
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'status_tramitacao'


class TipoAfastamento(models.Model):
    tip_afastamento = models.SmallIntegerField(primary_key=True)
    des_afastamento = models.CharField(max_length=50)
    ind_afastamento = models.SmallIntegerField()
    ind_fim_mandato = models.SmallIntegerField()
    des_dispositivo = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_afastamento'


class TipoAutor(models.Model):
    tip_autor = models.SmallIntegerField(primary_key=True)
    des_tipo_autor = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_autor'


class TipoComissao(models.Model):
    tip_comissao = models.SmallIntegerField(primary_key=True)
    nom_tipo_comissao = models.CharField(max_length=50)
    sgl_natureza_comissao = models.CharField(max_length=1)
    sgl_tipo_comissao = models.CharField(max_length=10)
    des_dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_comissao'


class TipoDependente(models.Model):
    tip_dependente = models.SmallIntegerField(primary_key=True)
    des_tipo_dependente = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_dependente'


class TipoDocumento(models.Model):
    tip_documento = models.AutoField(primary_key=True)
    des_tipo_documento = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_documento'


class TipoExpediente(models.Model):
    cod_expediente = models.AutoField(primary_key=True)
    nom_expediente = models.CharField(max_length=100)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_expediente'


class TipoFimRelatoria(models.Model):
    tip_fim_relatoria = models.SmallIntegerField(primary_key=True)
    des_fim_relatoria = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_fim_relatoria'


class TipoMateriaLegislativa(models.Model):
    tip_materia = models.AutoField(primary_key=True)
    sgl_tipo_materia = models.CharField(max_length=5)
    des_tipo_materia = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_materia_legislativa'


class TipoNormaJuridica(models.Model):
    tip_norma = models.SmallIntegerField(primary_key=True)
    sgl_tipo_norma = models.CharField(max_length=3)
    des_tipo_norma = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_norma_juridica'


class TipoProposicao(models.Model):
    tip_proposicao = models.AutoField(primary_key=True)
    des_tipo_proposicao = models.CharField(max_length=50)
    ind_mat_ou_doc = models.CharField(max_length=1)
    tip_mat_ou_doc = models.IntegerField()
    nom_modelo = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_proposicao'


class TipoResultadoVotacao(models.Model):
    tip_resultado_votacao = models.AutoField(primary_key=True)
    nom_resultado = models.CharField(max_length=100)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_resultado_votacao'


class TipoSessaoPlenaria(models.Model):
    tip_sessao = models.SmallIntegerField(primary_key=True)
    nom_sessao = models.CharField(max_length=30)
    ind_excluido = models.SmallIntegerField()
    num_minimo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_sessao_plenaria'


class TipoSituacaoMilitar(models.Model):
    tip_situacao_militar = models.SmallIntegerField(primary_key=True)
    des_tipo_situacao = models.CharField(max_length=50)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_situacao_militar'


class Tramitacao(models.Model):
    cod_tramitacao = models.AutoField(primary_key=True)
    cod_status = models.ForeignKey(StatusTramitacao, db_column='cod_status', blank=True, null=True)
    cod_materia = models.ForeignKey(MateriaLegislativa, db_column='cod_materia')
    dat_tramitacao = models.DateField(blank=True, null=True)
    cod_unid_tram_local = models.ForeignKey('UnidadeTramitacao', db_column='cod_unid_tram_local', blank=True, null=True)
    dat_encaminha = models.DateField(blank=True, null=True)
    cod_unid_tram_dest = models.ForeignKey('UnidadeTramitacao', db_column='cod_unid_tram_dest', blank=True, null=True)
    ind_ult_tramitacao = models.SmallIntegerField()
    ind_urgencia = models.SmallIntegerField()
    sgl_turno = models.CharField(max_length=1, blank=True, null=True)
    txt_tramitacao = models.TextField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'tramitacao'


class UnidadeTramitacao(models.Model):
    cod_unid_tramitacao = models.AutoField(primary_key=True)
    cod_comissao = models.ForeignKey(Comissao, db_column='cod_comissao', blank=True, null=True)
    cod_orgao = models.ForeignKey(Orgao, db_column='cod_orgao', blank=True, null=True)
    cod_parlamentar = models.IntegerField(blank=True, null=True)
    ind_excluido = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'unidade_tramitacao'


class VinculoNormaJuridica(models.Model):
    cod_vinculo = models.AutoField(primary_key=True)
    cod_norma_referente = models.ForeignKey(NormaJuridica, db_column='cod_norma_referente')
    cod_norma_referida = models.ForeignKey(NormaJuridica, db_column='cod_norma_referida')
    tip_vinculo = models.CharField(max_length=1, blank=True, null=True)
    ind_excluido = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'vinculo_norma_juridica'
