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
    cod_cadastro = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField()
    end_email = models.CharField(max_length=100)
    txt_hash = models.CharField(max_length=8)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'acomp_materia'
        unique_together = (('cod_materia', 'end_email'),)


class Afastamento(models.Model):
    cod_afastamento = models.AutoField(primary_key=True)
    cod_parlamentar = models.IntegerField()
    cod_mandato = models.IntegerField()
    num_legislatura = models.IntegerField()
    tip_afastamento = models.IntegerField()
    dat_inicio_afastamento = models.DateField()
    dat_fim_afastamento = models.DateField(blank=True, null=True)
    cod_parlamentar_suplente = models.IntegerField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'afastamento'


class Anexada(models.Model):
    cod_materia_principal = models.IntegerField()
    cod_materia_anexada = models.IntegerField()
    dat_anexacao = models.DateField()
    dat_desanexacao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'anexada'
        unique_together = (('cod_materia_principal', 'cod_materia_anexada'),)


class Apenso(models.Model):
    cod_materia_principal = models.IntegerField()
    cod_materia_apensada = models.IntegerField()
    dat_apensacao = models.DateField()
    dat_desapensacao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'apenso'
        unique_together = (('cod_materia_principal', 'cod_materia_apensada'),)


class AssuntoMateria(models.Model):
    cod_assunto = models.IntegerField(primary_key=True)
    des_assunto = models.CharField(max_length=200)
    des_dispositivo = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'assunto_materia'


class AssuntoNorma(models.Model):
    cod_assunto = models.AutoField(primary_key=True)
    des_assunto = models.CharField(max_length=50)
    des_estendida = models.CharField(max_length=250, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'assunto_norma'


class Autor(models.Model):
    cod_autor = models.AutoField(primary_key=True)
    cod_partido = models.IntegerField(blank=True, null=True)
    cod_comissao = models.IntegerField(blank=True, null=True)
    cod_bancada = models.IntegerField(blank=True, null=True)
    cod_parlamentar = models.IntegerField(blank=True, null=True)
    tip_autor = models.IntegerField()
    nom_autor = models.CharField(max_length=50, blank=True, null=True)
    des_cargo = models.CharField(max_length=50, blank=True, null=True)
    col_username = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'autor'


class Autoria(models.Model):
    cod_autor = models.IntegerField()
    cod_materia = models.IntegerField()
    ind_primeiro_autor = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'autoria'
        unique_together = (('cod_autor', 'cod_materia'),)


class Bancada(models.Model):
    cod_bancada = models.AutoField(primary_key=True)
    num_legislatura = models.IntegerField()
    cod_partido = models.IntegerField(blank=True, null=True)
    nom_bancada = models.CharField(max_length=60)
    descricao = models.TextField(blank=True, null=True)
    dat_criacao = models.DateField(blank=True, null=True)
    dat_extincao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'bancada'


class CargoBancada(models.Model):
    cod_cargo = models.AutoField(primary_key=True)
    des_cargo = models.CharField(max_length=50, blank=True, null=True)
    ind_unico = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cargo_bancada'


class CargoComissao(models.Model):
    cod_cargo = models.AutoField(primary_key=True)
    des_cargo = models.CharField(max_length=50)
    ind_unico = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cargo_comissao'


class CargoMesa(models.Model):
    cod_cargo = models.AutoField(primary_key=True)
    des_cargo = models.CharField(max_length=50)
    ind_unico = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cargo_mesa'


class Coligacao(models.Model):
    cod_coligacao = models.AutoField(primary_key=True)
    num_legislatura = models.IntegerField()
    nom_coligacao = models.CharField(max_length=50)
    num_votos_coligacao = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'coligacao'


class Comissao(models.Model):
    cod_comissao = models.AutoField(primary_key=True)
    tip_comissao = models.IntegerField()
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
    ind_unid_deliberativa = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'comissao'


class ComposicaoBancada(models.Model):
    cod_comp_bancada = models.AutoField(primary_key=True)
    cod_parlamentar = models.IntegerField()
    cod_bancada = models.IntegerField()
    cod_cargo = models.IntegerField()
    ind_titular = models.IntegerField()
    dat_designacao = models.DateField()
    dat_desligamento = models.DateField(blank=True, null=True)
    des_motivo_desligamento = models.CharField(max_length=150, blank=True, null=True)
    obs_composicao = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_bancada'


class ComposicaoColigacao(models.Model):
    cod_partido = models.IntegerField()
    cod_coligacao = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_coligacao'
        unique_together = (('cod_partido', 'cod_coligacao'),)


class ComposicaoComissao(models.Model):
    cod_comp_comissao = models.AutoField(primary_key=True)
    cod_parlamentar = models.IntegerField()
    cod_comissao = models.IntegerField()
    cod_periodo_comp = models.IntegerField()
    cod_cargo = models.IntegerField()
    ind_titular = models.IntegerField()
    dat_designacao = models.DateField()
    dat_desligamento = models.DateField(blank=True, null=True)
    des_motivo_desligamento = models.CharField(max_length=150, blank=True, null=True)
    obs_composicao = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_comissao'


class ComposicaoMesa(models.Model):
    cod_parlamentar = models.IntegerField()
    cod_sessao_leg = models.IntegerField(blank=True, null=True)
    cod_periodo_comp = models.IntegerField()
    cod_cargo = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'composicao_mesa'
        unique_together = (('cod_parlamentar', 'cod_periodo_comp', 'cod_cargo'),)


class CronometroAparte(models.Model):
    int_reset = models.IntegerField()
    int_start = models.IntegerField()
    int_stop = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cronometro_aparte'


class CronometroDiscurso(models.Model):
    int_reset = models.IntegerField()
    int_start = models.IntegerField()
    int_stop = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cronometro_discurso'


class CronometroOrdem(models.Model):
    int_reset = models.IntegerField()
    int_start = models.IntegerField()
    int_stop = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'cronometro_ordem'


class Dependente(models.Model):
    cod_dependente = models.AutoField(primary_key=True)
    tip_dependente = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    nom_dependente = models.CharField(max_length=50)
    sex_dependente = models.CharField(max_length=1)
    dat_nascimento = models.DateField(blank=True, null=True)
    num_cpf = models.CharField(max_length=14, blank=True, null=True)
    num_rg = models.CharField(max_length=15, blank=True, null=True)
    num_tit_eleitor = models.CharField(max_length=15, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'dependente'


class DespachoInicial(models.Model):
    cod_materia = models.IntegerField()
    num_ordem = models.IntegerField()
    cod_comissao = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'despacho_inicial'
        unique_together = (('cod_materia', 'num_ordem'),)


class DocumentoAcessorio(models.Model):
    cod_documento = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField()
    tip_documento = models.IntegerField()
    nom_documento = models.CharField(max_length=50, blank=True, null=True)
    dat_documento = models.DateField(blank=True, null=True)
    nom_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_ementa = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'documento_acessorio'


class DocumentoAcessorioAdministrativo(models.Model):
    cod_documento_acessorio = models.AutoField(primary_key=True)
    cod_documento = models.IntegerField()
    tip_documento = models.IntegerField()
    nom_documento = models.CharField(max_length=30)
    nom_arquivo = models.CharField(max_length=100)
    dat_documento = models.DateField(blank=True, null=True)
    nom_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_assunto = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'documento_acessorio_administrativo'


class DocumentoAdministrativo(models.Model):
    cod_documento = models.AutoField(primary_key=True)
    tip_documento = models.IntegerField()
    num_documento = models.IntegerField()
    ano_documento = models.SmallIntegerField()
    dat_documento = models.DateField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    txt_interessado = models.CharField(max_length=50, blank=True, null=True)
    cod_autor = models.IntegerField(blank=True, null=True)
    num_dias_prazo = models.IntegerField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_tramitacao = models.IntegerField()
    txt_assunto = models.TextField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'documento_administrativo'


class Emenda(models.Model):
    cod_emenda = models.AutoField(primary_key=True)
    tip_emenda = models.CharField(max_length=15)
    num_emenda = models.IntegerField()
    cod_materia = models.IntegerField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    dat_apresentacao = models.DateField(blank=True, null=True)
    txt_ementa = models.CharField(max_length=400, blank=True, null=True)
    txt_observacao = models.CharField(max_length=150, blank=True, null=True)
    cod_autor = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'emenda'
        unique_together = (('num_emenda', 'cod_materia', 'ind_excluido'),)


class EncerramentoPresenca(models.Model):
    cod_presenca_encerramento = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    dat_ordem = models.DateField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'encerramento_presenca'
        unique_together = (('cod_sessao_plen', 'cod_parlamentar'),)


class ExpedienteMateria(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_materia = models.IntegerField()
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()
    ind_votacao_iniciada = models.IntegerField()
    dat_ultima_votacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'expediente_materia'


class ExpedientePresenca(models.Model):
    cod_presenca_expediente = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    dat_ordem = models.DateField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'expediente_presenca'
        unique_together = (('cod_sessao_plen', 'cod_parlamentar'),)


class ExpedienteSessaoPlenaria(models.Model):
    cod_sessao_plen = models.IntegerField()
    cod_expediente = models.IntegerField()
    txt_expediente = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'expediente_sessao_plenaria'
        unique_together = (('cod_sessao_plen', 'cod_expediente'),)


class Filiacao(models.Model):
    dat_filiacao = models.DateField()
    cod_parlamentar = models.IntegerField()
    cod_partido = models.IntegerField()
    dat_desfiliacao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'filiacao'
        unique_together = (('dat_filiacao', 'cod_parlamentar', 'cod_partido'),)


class Instituicao(models.Model):
    cod_instituicao = models.AutoField(primary_key=True)
    tip_instituicao = models.IntegerField()
    nom_instituicao = models.CharField(max_length=200, blank=True, null=True)
    end_instituicao = models.TextField(blank=True, null=True)
    nom_bairro = models.CharField(max_length=80, blank=True, null=True)
    cod_localidade = models.IntegerField(blank=True, null=True)
    num_cep = models.CharField(max_length=9, blank=True, null=True)
    num_telefone = models.CharField(max_length=50, blank=True, null=True)
    num_fax = models.CharField(max_length=50, blank=True, null=True)
    end_email = models.CharField(max_length=100, blank=True, null=True)
    end_web = models.CharField(max_length=100, blank=True, null=True)
    nom_responsavel = models.CharField(max_length=50, blank=True, null=True)
    des_cargo = models.CharField(max_length=80, blank=True, null=True)
    txt_forma_tratamento = models.CharField(max_length=30, blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    dat_insercao = models.DateTimeField(blank=True, null=True)
    txt_user_insercao = models.CharField(max_length=20, blank=True, null=True)
    txt_ip_insercao = models.CharField(max_length=15, blank=True, null=True)
    timestamp_alteracao = models.DateTimeField()
    txt_user_alteracao = models.CharField(max_length=20, blank=True, null=True)
    txt_ip_alteracao = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'instituicao'


class LegislacaoCitada(models.Model):
    cod_materia = models.IntegerField()
    cod_norma = models.IntegerField()
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
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'legislacao_citada'
        unique_together = (('cod_materia', 'cod_norma'),)


class Legislatura(models.Model):
    num_legislatura = models.IntegerField(primary_key=True)
    dat_inicio = models.DateField()
    dat_fim = models.DateField()
    dat_eleicao = models.DateField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'legislatura'


class LexmlRegistroProvedor(models.Model):
    cod_provedor = models.AutoField(primary_key=True)
    id_provedor = models.IntegerField()
    nom_provedor = models.CharField(max_length=255)
    sgl_provedor = models.CharField(max_length=15)
    adm_email = models.CharField(max_length=50, blank=True, null=True)
    nom_responsavel = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50)
    id_responsavel = models.IntegerField(blank=True, null=True)
    xml_provedor = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lexml_registro_provedor'


class LexmlRegistroPublicador(models.Model):
    cod_publicador = models.AutoField(primary_key=True)
    id_publicador = models.IntegerField()
    nom_publicador = models.CharField(max_length=255)
    adm_email = models.CharField(max_length=50, blank=True, null=True)
    sigla = models.CharField(max_length=255, blank=True, null=True)
    nom_responsavel = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50)
    id_responsavel = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'lexml_registro_publicador'


class Localidade(models.Model):
    cod_localidade = models.IntegerField(primary_key=True)
    nom_localidade = models.CharField(max_length=50, blank=True, null=True)
    nom_localidade_pesq = models.CharField(max_length=50, blank=True, null=True)
    tip_localidade = models.CharField(max_length=1, blank=True, null=True)
    sgl_uf = models.CharField(max_length=2, blank=True, null=True)
    sgl_regiao = models.CharField(max_length=2, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'localidade'


class Mandato(models.Model):
    cod_mandato = models.AutoField(primary_key=True)
    cod_parlamentar = models.IntegerField()
    tip_afastamento = models.IntegerField(blank=True, null=True)
    num_legislatura = models.IntegerField()
    cod_coligacao = models.IntegerField(blank=True, null=True)
    dat_inicio_mandato = models.DateField(blank=True, null=True)
    tip_causa_fim_mandato = models.IntegerField(blank=True, null=True)
    dat_fim_mandato = models.DateField(blank=True, null=True)
    num_votos_recebidos = models.IntegerField(blank=True, null=True)
    dat_expedicao_diploma = models.DateField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_titular = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'mandato'


class MateriaApresentadaSessao(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_materia = models.IntegerField()
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    num_ordem = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'materia_apresentada_sessao'


class MateriaAssunto(models.Model):
    cod_assunto = models.IntegerField()
    cod_materia = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'materia_assunto'
        unique_together = (('cod_assunto', 'cod_materia'),)


class MateriaLegislativa(models.Model):
    cod_materia = models.AutoField(primary_key=True)
    tip_id_basica = models.IntegerField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    num_protocolo_spdo = models.CharField(max_length=18, blank=True, null=True)
    num_ident_basica = models.IntegerField()
    ano_ident_basica = models.SmallIntegerField()
    dat_apresentacao = models.DateField(blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1, blank=True, null=True)
    cod_regime_tramitacao = models.IntegerField()
    dat_publicacao = models.DateField(blank=True, null=True)
    tip_origem_externa = models.IntegerField(blank=True, null=True)
    num_origem_externa = models.CharField(max_length=5, blank=True, null=True)
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True)
    dat_origem_externa = models.DateField(blank=True, null=True)
    cod_local_origem_externa = models.IntegerField(blank=True, null=True)
    nom_apelido = models.CharField(max_length=50, blank=True, null=True)
    num_dias_prazo = models.IntegerField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_tramitacao = models.IntegerField()
    ind_polemica = models.IntegerField(blank=True, null=True)
    des_objeto = models.CharField(max_length=150, blank=True, null=True)
    ind_complementar = models.IntegerField(blank=True, null=True)
    txt_ementa = models.TextField()
    txt_indexacao = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    cod_situacao = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    txt_cep = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'materia_legislativa'


class MesaSessaoPlenaria(models.Model):
    cod_cargo = models.IntegerField()
    cod_sessao_leg = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    cod_sessao_plen = models.IntegerField()
    ind_excluido = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mesa_sessao_plenaria'
        unique_together = (('cod_cargo', 'cod_sessao_leg', 'cod_parlamentar', 'cod_sessao_plen'),)


class NivelInstrucao(models.Model):
    cod_nivel_instrucao = models.AutoField(primary_key=True)
    des_nivel_instrucao = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'nivel_instrucao'


class NormaJuridica(models.Model):
    cod_norma = models.AutoField(primary_key=True)
    tip_norma = models.IntegerField()
    cod_materia = models.IntegerField(blank=True, null=True)
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
    ind_complemento = models.IntegerField(blank=True, null=True)
    cod_assunto = models.CharField(max_length=16)
    cod_situacao = models.IntegerField(blank=True, null=True)
    dat_vigencia = models.DateField(blank=True, null=True)
    timestamp = models.DateTimeField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'norma_juridica'


class Numeracao(models.Model):
    cod_materia = models.IntegerField()
    num_ordem = models.IntegerField()
    tip_materia = models.IntegerField()
    num_materia = models.CharField(max_length=5)
    ano_materia = models.SmallIntegerField()
    dat_materia = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'numeracao'
        unique_together = (('cod_materia', 'num_ordem'),)


class Oradores(models.Model):
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'oradores'
        unique_together = (('cod_sessao_plen', 'cod_parlamentar'),)


class OradoresExpediente(models.Model):
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    num_ordem = models.IntegerField()
    url_discurso = models.CharField(max_length=150, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'oradores_expediente'
        unique_together = (('cod_sessao_plen', 'cod_parlamentar'),)


class OrdemDia(models.Model):
    cod_ordem = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_materia = models.IntegerField()
    dat_ordem = models.DateField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    num_ordem = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)
    tip_votacao = models.IntegerField()
    ind_votacao_iniciada = models.IntegerField()
    tip_quorum = models.IntegerField(blank=True, null=True)
    dat_ultima_votacao = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ordem_dia'


class OrdemDiaPresenca(models.Model):
    cod_presenca_ordem_dia = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    dat_ordem = models.DateField()
    dat_presenca = models.DateTimeField()
    cod_ip = models.CharField(max_length=50)
    cod_mac = models.CharField(max_length=50)
    cod_perfil = models.CharField(max_length=45)
    ind_recontagem = models.IntegerField()
    num_id_quorum = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'ordem_dia_presenca'


class Orgao(models.Model):
    cod_orgao = models.AutoField(primary_key=True)
    nom_orgao = models.CharField(max_length=60)
    sgl_orgao = models.CharField(max_length=10)
    ind_unid_deliberativa = models.IntegerField()
    end_orgao = models.CharField(max_length=100, blank=True, null=True)
    num_tel_orgao = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'orgao'


class Origem(models.Model):
    cod_origem = models.AutoField(primary_key=True)
    sgl_origem = models.CharField(max_length=10)
    nom_origem = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'origem'


class Parecer(models.Model):
    cod_relatoria = models.IntegerField()
    cod_materia = models.IntegerField()
    tip_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1)
    txt_parecer = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'parecer'
        unique_together = (('cod_relatoria', 'cod_materia'),)


class Parlamentar(models.Model):
    cod_parlamentar = models.AutoField(primary_key=True)
    cod_nivel_instrucao = models.IntegerField(blank=True, null=True)
    tip_situacao_militar = models.IntegerField(blank=True, null=True)
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
    cod_localidade_resid = models.IntegerField(blank=True, null=True)
    num_cep_resid = models.CharField(max_length=9, blank=True, null=True)
    num_tel_resid = models.CharField(max_length=50, blank=True, null=True)
    num_fax_resid = models.CharField(max_length=50, blank=True, null=True)
    end_web = models.CharField(max_length=100, blank=True, null=True)
    nom_profissao = models.CharField(max_length=50, blank=True, null=True)
    end_email = models.CharField(max_length=100, blank=True, null=True)
    des_local_atuacao = models.CharField(max_length=100, blank=True, null=True)
    ind_ativo = models.IntegerField()
    txt_biografia = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_unid_deliberativa = models.IntegerField()
    txt_login = models.CharField(max_length=45)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'parlamentar'


class Partido(models.Model):
    cod_partido = models.AutoField(primary_key=True)
    sgl_partido = models.CharField(max_length=9, blank=True, null=True)
    nom_partido = models.CharField(max_length=50, blank=True, null=True)
    dat_criacao = models.DateField(blank=True, null=True)
    dat_extincao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'partido'


class PartidoOld(models.Model):
    cod_partido = models.AutoField(primary_key=True)
    sgl_partido = models.CharField(max_length=9)
    nom_partido = models.CharField(max_length=50)
    dat_criacao = models.DateField(blank=True, null=True)
    dat_extincao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'partido_old'


class PeriodoCompComissao(models.Model):
    cod_periodo_comp = models.AutoField(primary_key=True)
    dat_inicio_periodo = models.DateField()
    dat_fim_periodo = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'periodo_comp_comissao'


class PeriodoCompMesa(models.Model):
    cod_periodo_comp = models.AutoField(primary_key=True)
    num_legislatura = models.IntegerField()
    dat_inicio_periodo = models.DateField()
    dat_fim_periodo = models.DateField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'periodo_comp_mesa'


class PresencaEndereco(models.Model):
    cod_presenca_endereco = models.AutoField(primary_key=True)
    txt_mac_address = models.CharField(max_length=45)
    txt_ip_address = models.CharField(max_length=45)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'presenca_endereco'


class Proposicao(models.Model):
    cod_proposicao = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField(blank=True, null=True)
    cod_autor = models.IntegerField()
    tip_proposicao = models.IntegerField()
    dat_envio = models.DateTimeField()
    dat_recebimento = models.DateTimeField(blank=True, null=True)
    txt_descricao = models.CharField(max_length=400)
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)
    dat_devolucao = models.DateTimeField(blank=True, null=True)
    txt_justif_devolucao = models.CharField(max_length=200, blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    num_proposicao = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'proposicao'


class PropsPainel(models.Model):
    cod_props_painel = models.IntegerField(primary_key=True)
    txt_jornal = models.TextField(blank=True, null=True)
    txt_jornal_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_jornal_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_mensagem = models.TextField(blank=True, null=True)
    txt_mensagem_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_fonte = models.CharField(max_length=45)
    txt_painel_cor_fonte = models.CharField(max_length=45)
    txt_painel_cor_fundo = models.CharField(max_length=45)
    txt_apartante_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_apartante_exp_tempo = models.CharField(max_length=45, blank=True, null=True)
    txt_apartante_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_questao_ordem_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_questao_ordem_exp_tempo = models.CharField(max_length=45, blank=True, null=True)
    txt_questao_ordem_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_orador_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_orador_exp_tempo = models.CharField(max_length=45, blank=True, null=True)
    txt_orador_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_mesa_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_mesa_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_presenca_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_presenca_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_ausencia_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_ausencia_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_presenca_total_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_presenca_total_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_ausencia_total_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_ausencia_total_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_sim_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_sim_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_nao_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_nao_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_abstencao_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_abstencao_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_nao_votou_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_nao_votou_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_votos_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_votos_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_presentes_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_presentes_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_total_ausentes_cor = models.CharField(max_length=45, blank=True, null=True)
    txt_total_ausentes_fonte = models.CharField(max_length=5, blank=True, null=True)
    txt_apartante_ord_tempo = models.CharField(max_length=45, blank=True, null=True)
    txt_questao_ordem_ord_tempo = models.CharField(max_length=45, blank=True, null=True)
    txt_orador_ord_tempo = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'props_painel'


class Protocolo(models.Model):
    cod_protocolo = models.AutoField(primary_key=True)
    num_protocolo = models.IntegerField(blank=True, null=True)
    ano_protocolo = models.SmallIntegerField()
    dat_protocolo = models.DateField()
    hor_protocolo = models.TimeField()
    dat_timestamp = models.DateTimeField()
    tip_protocolo = models.IntegerField()
    tip_processo = models.IntegerField()
    txt_interessado = models.CharField(max_length=60, blank=True, null=True)
    cod_autor = models.IntegerField(blank=True, null=True)
    txt_assunto_ementa = models.TextField(blank=True, null=True)
    tip_documento = models.IntegerField(blank=True, null=True)
    tip_materia = models.IntegerField(blank=True, null=True)
    num_paginas = models.IntegerField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_anulado = models.IntegerField()
    txt_user_anulacao = models.CharField(max_length=20, blank=True, null=True)
    txt_ip_anulacao = models.CharField(max_length=15, blank=True, null=True)
    txt_just_anulacao = models.CharField(max_length=60, blank=True, null=True)
    timestamp_anulacao = models.DateTimeField(blank=True, null=True)
    num_protocolo_spdo = models.CharField(unique=True, max_length=18, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'protocolo'


class RegimeTramitacao(models.Model):
    cod_regime_tramitacao = models.AutoField(primary_key=True)
    des_regime_tramitacao = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'regime_tramitacao'


class RegistroPresencaOrdem(models.Model):
    cod_registro_pre = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    num_id_quorum = models.IntegerField()
    ind_status_pre = models.IntegerField()
    dat_abre_pre = models.DateTimeField()
    dat_fecha_pre = models.DateTimeField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'registro_presenca_ordem'


class RegistroPresencaSessao(models.Model):
    cod_registro_pre = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    num_id_quorum = models.IntegerField()
    ind_status_pre = models.IntegerField()
    dat_abre_pre = models.DateTimeField()
    dat_fecha_pre = models.DateTimeField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'registro_presenca_sessao'


class RegistroVotacao(models.Model):
    cod_votacao = models.AutoField(primary_key=True)
    tip_resultado_votacao = models.IntegerField()
    cod_materia = models.IntegerField()
    cod_ordem = models.IntegerField()
    cod_emenda = models.IntegerField(blank=True, null=True)
    cod_subemenda = models.IntegerField(blank=True, null=True)
    cod_substitutivo = models.IntegerField(blank=True, null=True)
    num_votos_sim = models.IntegerField()
    num_votos_nao = models.IntegerField()
    num_abstencao = models.IntegerField()
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()
    num_nao_votou = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'registro_votacao'


class RegistroVotacaoParlamentar(models.Model):
    cod_votacao = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    ind_excluido = models.IntegerField()
    vot_parlamentar = models.CharField(max_length=10)
    txt_login = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'registro_votacao_parlamentar'
        unique_together = (('cod_votacao', 'cod_parlamentar'),)


class Relatoria(models.Model):
    cod_relatoria = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    tip_fim_relatoria = models.IntegerField(blank=True, null=True)
    cod_comissao = models.IntegerField(blank=True, null=True)
    dat_desig_relator = models.DateField()
    dat_destit_relator = models.DateField(blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1, blank=True, null=True)
    txt_parecer = models.TextField(blank=True, null=True)
    tip_conclusao = models.CharField(max_length=1, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'relatoria'


class ReuniaoComissao(models.Model):
    cod_reuniao = models.AutoField(primary_key=True)
    cod_comissao = models.IntegerField()
    num_reuniao = models.IntegerField()
    dat_inicio_reuniao = models.DateField()
    hr_inicio_reuniao = models.CharField(max_length=5, blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'reuniao_comissao'


class SessaoLegislativa(models.Model):
    cod_sessao_leg = models.AutoField(primary_key=True)
    num_legislatura = models.IntegerField()
    num_sessao_leg = models.IntegerField()
    tip_sessao_leg = models.CharField(max_length=1)
    dat_inicio = models.DateField()
    dat_fim = models.DateField()
    dat_inicio_intervalo = models.DateField(blank=True, null=True)
    dat_fim_intervalo = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sessao_legislativa'


class SessaoPlenaria(models.Model):
    cod_sessao_plen = models.AutoField(primary_key=True)
    cod_andamento_sessao = models.IntegerField(blank=True, null=True)
    tip_sessao = models.IntegerField()
    cod_sessao_leg = models.IntegerField()
    num_legislatura = models.IntegerField()
    tip_expediente = models.CharField(max_length=10)
    dat_inicio_sessao = models.DateField()
    dia_sessao = models.CharField(max_length=15)
    hr_inicio_sessao = models.CharField(max_length=5)
    hr_fim_sessao = models.CharField(max_length=5, blank=True, null=True)
    num_sessao_plen = models.IntegerField()
    dat_fim_sessao = models.DateField(blank=True, null=True)
    url_audio = models.CharField(max_length=150, blank=True, null=True)
    url_video = models.CharField(max_length=150, blank=True, null=True)
    ind_iniciada = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sessao_plenaria'


class SessaoPlenariaLog(models.Model):
    cod_sessao_plen_log = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField(blank=True, null=True)
    txt_login = models.CharField(max_length=45)
    txt_ip = models.CharField(max_length=45)
    txt_mac = models.CharField(max_length=45)
    txt_acao = models.CharField(max_length=45)
    txt_mensagem = models.CharField(max_length=500)
    dat_log = models.DateTimeField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sessao_plenaria_log'


class SessaoPlenariaPresenca(models.Model):
    cod_presenca_sessao = models.AutoField(primary_key=True)
    cod_sessao_plen = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    dat_sessao = models.DateField(blank=True, null=True)
    dat_presenca = models.DateTimeField()
    cod_ip = models.CharField(max_length=50)
    cod_mac = models.CharField(max_length=50)
    cod_perfil = models.CharField(max_length=20)
    ind_recontagem = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'sessao_plenaria_presenca'


class SpdoUsers(models.Model):
    cod_spdo_users = models.AutoField(primary_key=True)
    txt_login_sapl = models.CharField(max_length=45)
    txt_login_spdo = models.CharField(max_length=45)
    txt_senha_spdo = models.CharField(max_length=45, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'spdo_users'


class StatusTramitacao(models.Model):
    cod_status = models.AutoField(primary_key=True)
    sgl_status = models.CharField(max_length=10)
    des_status = models.CharField(max_length=60)
    ind_fim_tramitacao = models.IntegerField()
    ind_retorno_tramitacao = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'status_tramitacao'


class StatusTramitacaoAdministrativo(models.Model):
    cod_status = models.AutoField(primary_key=True)
    sgl_status = models.CharField(max_length=10)
    des_status = models.CharField(max_length=60)
    ind_fim_tramitacao = models.IntegerField()
    ind_retorno_tramitacao = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'status_tramitacao_administrativo'


class Subemenda(models.Model):
    cod_subemenda = models.AutoField(primary_key=True)
    tip_subemenda = models.CharField(max_length=15)
    num_subemenda = models.IntegerField()
    cod_emenda = models.IntegerField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    dat_apresentacao = models.DateField(blank=True, null=True)
    txt_ementa = models.CharField(max_length=400, blank=True, null=True)
    txt_observacao = models.CharField(max_length=150, blank=True, null=True)
    cod_autor = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'subemenda'
        unique_together = (('num_subemenda', 'cod_emenda', 'ind_excluido'),)


class Substitutivo(models.Model):
    cod_substitutivo = models.AutoField(primary_key=True)
    num_substitutivo = models.IntegerField()
    cod_materia = models.IntegerField()
    num_protocolo = models.IntegerField(blank=True, null=True)
    dat_apresentacao = models.DateField(blank=True, null=True)
    txt_ementa = models.CharField(max_length=150, blank=True, null=True)
    txt_observacao = models.CharField(max_length=150, blank=True, null=True)
    cod_autor = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'substitutivo'
        unique_together = (('num_substitutivo', 'cod_materia', 'ind_excluido'),)


class TipoAfastamento(models.Model):
    tip_afastamento = models.AutoField(primary_key=True)
    des_afastamento = models.CharField(max_length=50)
    ind_afastamento = models.IntegerField()
    ind_fim_mandato = models.IntegerField()
    des_dispositivo = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_afastamento'


class TipoAutor(models.Model):
    tip_autor = models.IntegerField(primary_key=True)
    des_tipo_autor = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_autor'


class TipoComissao(models.Model):
    tip_comissao = models.AutoField(primary_key=True)
    nom_tipo_comissao = models.CharField(max_length=50)
    sgl_natureza_comissao = models.CharField(max_length=1)
    sgl_tipo_comissao = models.CharField(max_length=10)
    des_dispositivo_regimental = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_comissao'


class TipoDependente(models.Model):
    tip_dependente = models.AutoField(primary_key=True)
    des_tipo_dependente = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_dependente'


class TipoDocumento(models.Model):
    tip_documento = models.AutoField(primary_key=True)
    des_tipo_documento = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_documento'


class TipoDocumentoAdministrativo(models.Model):
    tip_documento = models.AutoField(primary_key=True)
    sgl_tipo_documento = models.CharField(max_length=5)
    des_tipo_documento = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_documento_administrativo'


class TipoExpediente(models.Model):
    cod_expediente = models.AutoField(primary_key=True)
    nom_expediente = models.CharField(max_length=100)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_expediente'


class TipoFimRelatoria(models.Model):
    tip_fim_relatoria = models.AutoField(primary_key=True)
    des_fim_relatoria = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_fim_relatoria'


class TipoInstituicao(models.Model):
    tip_instituicao = models.AutoField(primary_key=True)
    nom_tipo_instituicao = models.CharField(max_length=80, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_instituicao'


class TipoMateriaLegislativa(models.Model):
    tip_materia = models.AutoField(primary_key=True)
    sgl_tipo_materia = models.CharField(max_length=5)
    des_tipo_materia = models.CharField(max_length=50)
    ind_num_automatica = models.IntegerField()
    quorum_minimo_votacao = models.IntegerField()
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_materia_legislativa'


class TipoNormaJuridica(models.Model):
    tip_norma = models.AutoField(primary_key=True)
    voc_lexml = models.CharField(max_length=50, blank=True, null=True)
    sgl_tipo_norma = models.CharField(max_length=3)
    des_tipo_norma = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_norma_juridica'


class TipoProposicao(models.Model):
    tip_proposicao = models.AutoField(primary_key=True)
    des_tipo_proposicao = models.CharField(max_length=50)
    ind_mat_ou_doc = models.CharField(max_length=1)
    tip_mat_ou_doc = models.IntegerField()
    nom_modelo = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_proposicao'


class TipoResultadoVotacao(models.Model):
    tip_resultado_votacao = models.AutoField(primary_key=True)
    nom_resultado = models.CharField(max_length=100)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_resultado_votacao'


class TipoSessaoPlenaria(models.Model):
    tip_sessao = models.AutoField(primary_key=True)
    nom_sessao = models.CharField(max_length=30)
    ind_excluido = models.IntegerField()
    num_minimo = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_sessao_plenaria'


class TipoSituacaoMateria(models.Model):
    tip_situacao_materia = models.AutoField(primary_key=True)
    des_tipo_situacao = models.CharField(max_length=100, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_situacao_materia'


class TipoSituacaoMilitar(models.Model):
    tip_situacao_militar = models.IntegerField(primary_key=True)
    des_tipo_situacao = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_situacao_militar'


class TipoSituacaoNorma(models.Model):
    tip_situacao_norma = models.AutoField(primary_key=True)
    des_tipo_situacao = models.CharField(max_length=100, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tipo_situacao_norma'


class Tramitacao(models.Model):
    cod_tramitacao = models.AutoField(primary_key=True)
    cod_status = models.IntegerField(blank=True, null=True)
    cod_materia = models.IntegerField()
    dat_tramitacao = models.DateField(blank=True, null=True)
    cod_unid_tram_local = models.IntegerField(blank=True, null=True)
    dat_encaminha = models.DateField(blank=True, null=True)
    cod_unid_tram_dest = models.IntegerField(blank=True, null=True)
    ind_ult_tramitacao = models.IntegerField()
    ind_urgencia = models.IntegerField()
    sgl_turno = models.CharField(max_length=1, blank=True, null=True)
    txt_tramitacao = models.TextField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tramitacao'


class TramitacaoAdministrativo(models.Model):
    cod_tramitacao = models.AutoField(primary_key=True)
    cod_documento = models.IntegerField()
    dat_tramitacao = models.DateField(blank=True, null=True)
    cod_unid_tram_local = models.IntegerField(blank=True, null=True)
    dat_encaminha = models.DateField(blank=True, null=True)
    cod_unid_tram_dest = models.IntegerField(blank=True, null=True)
    cod_status = models.IntegerField(blank=True, null=True)
    ind_ult_tramitacao = models.IntegerField()
    txt_tramitacao = models.TextField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tramitacao_administrativo'


class UnidadeTramitacao(models.Model):
    cod_unid_tramitacao = models.AutoField(primary_key=True)
    cod_comissao = models.IntegerField(blank=True, null=True)
    cod_orgao = models.IntegerField(blank=True, null=True)
    cod_parlamentar = models.IntegerField(blank=True, null=True)
    cod_unid_spdo = models.IntegerField(blank=True, null=True)
    txt_unid_spdo = models.CharField(max_length=45, blank=True, null=True)
    ind_excluido = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'unidade_tramitacao'


class VinculoNormaJuridica(models.Model):
    cod_vinculo = models.AutoField(primary_key=True)
    cod_norma_referente = models.IntegerField()
    cod_norma_referida = models.IntegerField()
    tip_vinculo = models.CharField(max_length=1, blank=True, null=True)
    ind_excluido = models.CharField(max_length=1)

    class Meta:
        managed = False
        db_table = 'vinculo_norma_juridica'
