from django.db import models


class AcompMateria(models.Model):
    cod_cadastro = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField()
    end_email = models.CharField(max_length=100)
    txt_hash = models.CharField(max_length=8)
    ind_excluido = models.IntegerField()


class Anexada(models.Model):
    cod_materia_principal = models.IntegerField()
    cod_materia_anexada = models.IntegerField()
    dat_anexacao = models.DateField()
    dat_desanexacao = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class AssuntoMateria(models.Model):
    cod_assunto = models.IntegerField(primary_key=True)
    des_assunto = models.CharField(max_length=200)
    des_dispositivo = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class Autor(models.Model):
    cod_autor = models.AutoField(primary_key=True)
    cod_partido = models.IntegerField(blank=True, null=True)
    cod_comissao = models.IntegerField(blank=True, null=True)
    cod_parlamentar = models.IntegerField(blank=True, null=True)
    tip_autor = models.IntegerField()
    nom_autor = models.CharField(max_length=50, blank=True, null=True)
    des_cargo = models.CharField(max_length=50, blank=True, null=True)
    col_username = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()


class Autoria(models.Model):
    cod_autor = models.IntegerField()
    cod_materia = models.IntegerField()
    ind_primeiro_autor = models.IntegerField()
    ind_excluido = models.IntegerField()


class DespachoInicial(models.Model):
    cod_materia = models.IntegerField()
    num_ordem = models.IntegerField()
    cod_comissao = models.IntegerField()
    ind_excluido = models.IntegerField()


class DocumentoAcessorio(models.Model):
    cod_documento = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField()
    tip_documento = models.IntegerField()
    nom_documento = models.CharField(max_length=30)
    dat_documento = models.DateField(blank=True, null=True)
    nom_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_ementa = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()


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


class MateriaAssunto(models.Model):
    cod_assunto = models.IntegerField()
    cod_materia = models.IntegerField()
    ind_excluido = models.IntegerField()


class MateriaLegislativa(models.Model):
    cod_materia = models.AutoField(primary_key=True)
    tip_id_basica = models.IntegerField()
    num_protocolo = models.IntegerField(blank=True, null=True)
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
    ind_excluido = models.IntegerField()
    txt_resultado = models.TextField(blank=True, null=True)


class Numeracao(models.Model):
    cod_materia = models.IntegerField()
    num_ordem = models.IntegerField()
    tip_materia = models.IntegerField()
    num_materia = models.CharField(max_length=5)
    ano_materia = models.SmallIntegerField()
    dat_materia = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class Orgao(models.Model):
    cod_orgao = models.AutoField(primary_key=True)
    nom_orgao = models.CharField(max_length=60)
    sgl_orgao = models.CharField(max_length=10)
    ind_unid_deliberativa = models.IntegerField()
    end_orgao = models.CharField(max_length=100, blank=True, null=True)
    num_tel_orgao = models.CharField(max_length=50, blank=True, null=True)
    ind_excluido = models.IntegerField()


class Origem(models.Model):
    cod_origem = models.AutoField(primary_key=True)
    sgl_origem = models.CharField(max_length=10)
    nom_origem = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class Parecer(models.Model):
    cod_relatoria = models.IntegerField()
    cod_materia = models.IntegerField()
    tip_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1)
    txt_parecer = models.TextField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class Proposicao(models.Model):
    cod_proposicao = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField(blank=True, null=True)
    cod_autor = models.IntegerField()
    tip_proposicao = models.IntegerField()
    dat_envio = models.DateTimeField()
    dat_recebimento = models.DateTimeField(blank=True, null=True)
    txt_descricao = models.CharField(max_length=100)
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)
    dat_devolucao = models.DateTimeField(blank=True, null=True)
    txt_justif_devolucao = models.CharField(max_length=200, blank=True, null=True)
    num_proposicao = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class RegimeTramitacao(models.Model):
    cod_regime_tramitacao = models.AutoField(primary_key=True)
    des_regime_tramitacao = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class Relatoria(models.Model):
    cod_relatoria = models.AutoField(primary_key=True)
    cod_materia = models.IntegerField()
    cod_parlamentar = models.IntegerField()
    tip_fim_relatoria = models.IntegerField(blank=True, null=True)
    cod_comissao = models.IntegerField(blank=True, null=True)
    dat_desig_relator = models.DateField()
    dat_destit_relator = models.DateField(blank=True, null=True)
    ind_excluido = models.IntegerField()


class StatusTramitacao(models.Model):
    cod_status = models.AutoField(primary_key=True)
    sgl_status = models.CharField(max_length=10)
    des_status = models.CharField(max_length=60)
    ind_fim_tramitacao = models.IntegerField()
    ind_retorno_tramitacao = models.IntegerField()
    ind_excluido = models.IntegerField()


class TipoAutor(models.Model):
    tip_autor = models.IntegerField(primary_key=True)
    des_tipo_autor = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class TipoDocumento(models.Model):
    tip_documento = models.AutoField(primary_key=True)
    des_tipo_documento = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class TipoFimRelatoria(models.Model):
    tip_fim_relatoria = models.AutoField(primary_key=True)
    des_fim_relatoria = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


class TipoMateriaLegislativa(models.Model):
    tip_materia = models.AutoField(primary_key=True)
    sgl_tipo_materia = models.CharField(max_length=5)
    des_tipo_materia = models.CharField(max_length=50)
    ind_num_automatica = models.IntegerField()
    quorum_minimo_votacao = models.IntegerField()
    ind_excluido = models.IntegerField()


class TipoProposicao(models.Model):
    tip_proposicao = models.AutoField(primary_key=True)
    des_tipo_proposicao = models.CharField(max_length=50)
    ind_mat_ou_doc = models.CharField(max_length=1)
    tip_mat_ou_doc = models.IntegerField()
    nom_modelo = models.CharField(max_length=50)
    ind_excluido = models.IntegerField()


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


class UnidadeTramitacao(models.Model):
    cod_unid_tramitacao = models.AutoField(primary_key=True)
    cod_comissao = models.IntegerField(blank=True, null=True)
    cod_orgao = models.IntegerField(blank=True, null=True)
    cod_parlamentar = models.IntegerField(blank=True, null=True)
    ind_excluido = models.IntegerField()
