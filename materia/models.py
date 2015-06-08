from django.db import models

from comissoes.models import Comissao
from parlamentares.models import Parlamentar, Partido


class TipoMateriaLegislativa(models.Model):
    tip_materia = models.AutoField(primary_key=True)
    sgl_tipo_materia = models.CharField(max_length=5)
    des_tipo_materia = models.CharField(max_length=50)
    ind_num_automatica = models.IntegerField()
    quorum_minimo_votacao = models.IntegerField()


class RegimeTramitacao(models.Model):
    cod_regime_tramitacao = models.AutoField(primary_key=True)
    des_regime_tramitacao = models.CharField(max_length=50)


class Origem(models.Model):
    cod_origem = models.AutoField(primary_key=True)
    sgl_origem = models.CharField(max_length=10)
    nom_origem = models.CharField(max_length=50)


class MateriaLegislativa(models.Model):
    cod_materia = models.AutoField(primary_key=True)
    tip_id_basica = models.ForeignKey(TipoMateriaLegislativa)
    num_protocolo = models.IntegerField(blank=True, null=True)
    num_ident_basica = models.IntegerField()
    ano_ident_basica = models.SmallIntegerField()
    dat_apresentacao = models.DateField(blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1, blank=True, null=True)
    regime_tramitacao = models.ForeignKey(RegimeTramitacao)
    dat_publicacao = models.DateField(blank=True, null=True)
    tip_origem_externa = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True)
    num_origem_externa = models.CharField(max_length=5, blank=True, null=True)
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True)
    dat_origem_externa = models.DateField(blank=True, null=True)
    local_origem_externa = models.ForeignKey(Origem, blank=True, null=True)
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
    txt_resultado = models.TextField(blank=True, null=True)


class AcompMateria(models.Model):
    cod_cadastro = models.AutoField(primary_key=True)
    materia = models.ForeignKey(MateriaLegislativa)
    end_email = models.CharField(max_length=100)
    txt_hash = models.CharField(max_length=8)


class Anexada(models.Model):
    materia_principal = models.ForeignKey(MateriaLegislativa)
    materia_anexada = models.ForeignKey(MateriaLegislativa)
    dat_anexacao = models.DateField()
    dat_desanexacao = models.DateField(blank=True, null=True)


class AssuntoMateria(models.Model):
    cod_assunto = models.IntegerField(primary_key=True)
    des_assunto = models.CharField(max_length=200)
    des_dispositivo = models.CharField(max_length=50)


class TipoAutor(models.Model):
    tip_autor = models.IntegerField(primary_key=True)
    des_tipo_autor = models.CharField(max_length=50)


class Autor(models.Model):
    cod_autor = models.AutoField(primary_key=True)
    partido = models.ForeignKey(Partido, blank=True, null=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)
    tip_autor = models.ForeignKey(TipoAutor)
    nom_autor = models.CharField(max_length=50, blank=True, null=True)
    des_cargo = models.CharField(max_length=50, blank=True, null=True)
    col_username = models.CharField(max_length=50, blank=True, null=True)


class Autoria(models.Model):
    autor = models.ForeignKey(Autor)
    materia = models.ForeignKey(MateriaLegislativa)
    ind_primeiro_autor = models.IntegerField()


class DespachoInicial(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    num_ordem = models.IntegerField()
    comissao = models.ForeignKey(Comissao)


class TipoDocumento(models.Model):
    tip_documento = models.AutoField(primary_key=True)
    des_tipo_documento = models.CharField(max_length=50)


class DocumentoAcessorio(models.Model):
    cod_documento = models.AutoField(primary_key=True)
    materia = models.ForeignKey(MateriaLegislativa)
    tip_documento = models.ForeignKey(TipoDocumento)
    nom_documento = models.CharField(max_length=30)
    dat_documento = models.DateField(blank=True, null=True)
    nom_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_ementa = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)


class MateriaAssunto(models.Model):
    assunto = models.ForeignKey(AssuntoMateria)
    materia = models.ForeignKey(MateriaLegislativa)


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    num_ordem = models.IntegerField()
    tip_materia = models.ForeignKey(TipoMateriaLegislativa)
    num_materia = models.CharField(max_length=5)
    ano_materia = models.SmallIntegerField()
    dat_materia = models.DateField(blank=True, null=True)


class Orgao(models.Model):
    cod_orgao = models.AutoField(primary_key=True)
    nom_orgao = models.CharField(max_length=60)
    sgl_orgao = models.CharField(max_length=10)
    ind_unid_deliberativa = models.IntegerField()
    end_orgao = models.CharField(max_length=100, blank=True, null=True)
    num_tel_orgao = models.CharField(max_length=50, blank=True, null=True)


class TipoFimRelatoria(models.Model):
    tip_fim_relatoria = models.AutoField(primary_key=True)
    des_fim_relatoria = models.CharField(max_length=50)


class Relatoria(models.Model):
    cod_relatoria = models.AutoField(primary_key=True)
    materia = models.ForeignKey(MateriaLegislativa)
    parlamentar = models.ForeignKey(Parlamentar)
    tip_fim_relatoria = models.ForeignKey(TipoFimRelatoria, blank=True, null=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    dat_desig_relator = models.DateField()
    dat_destit_relator = models.DateField(blank=True, null=True)


class Parecer(models.Model):
    relatoria = models.ForeignKey(Relatoria)
    materia = models.ForeignKey(MateriaLegislativa)
    tip_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tip_apresentacao = models.CharField(max_length=1)
    txt_parecer = models.TextField(blank=True, null=True)


class TipoProposicao(models.Model):
    tip_proposicao = models.AutoField(primary_key=True)
    des_tipo_proposicao = models.CharField(max_length=50)
    ind_mat_ou_doc = models.CharField(max_length=1)
    tip_mat_ou_doc = models.IntegerField()
    nom_modelo = models.CharField(max_length=50)


class Proposicao(models.Model):
    cod_proposicao = models.AutoField(primary_key=True)
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)
    autor = models.ForeignKey(Autor)
    tip_proposicao = models.ForeignKey(TipoProposicao)
    dat_envio = models.DateTimeField()
    dat_recebimento = models.DateTimeField(blank=True, null=True)
    txt_descricao = models.CharField(max_length=100)
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)
    dat_devolucao = models.DateTimeField(blank=True, null=True)
    txt_justif_devolucao = models.CharField(max_length=200, blank=True, null=True)
    num_proposicao = models.IntegerField(blank=True, null=True)


class StatusTramitacao(models.Model):
    cod_status = models.AutoField(primary_key=True)
    sgl_status = models.CharField(max_length=10)
    des_status = models.CharField(max_length=60)
    ind_fim_tramitacao = models.IntegerField()
    ind_retorno_tramitacao = models.IntegerField()


class UnidadeTramitacao(models.Model):
    cod_unid_tramitacao = models.AutoField(primary_key=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    orgao = models.ForeignKey(Orgao, blank=True, null=True)
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)


class Tramitacao(models.Model):
    cod_tramitacao = models.AutoField(primary_key=True)
    status = models.ForeignKey(StatusTramitacao, blank=True, null=True)
    materia = models.ForeignKey(MateriaLegislativa)
    dat_tramitacao = models.DateField(blank=True, null=True)
    unid_tram_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True)
    dat_encaminha = models.DateField(blank=True, null=True)
    unid_tram_dest = models.ForeignKey(UnidadeTramitacao, blank=True, null=True)
    ind_ult_tramitacao = models.IntegerField()
    ind_urgencia = models.IntegerField()
    sgl_turno = models.CharField(max_length=1, blank=True, null=True)
    txt_tramitacao = models.TextField(blank=True, null=True)
    dat_fim_prazo = models.DateField(blank=True, null=True)
