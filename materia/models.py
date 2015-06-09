from django.db import models

from comissoes.models import Comissao
from parlamentares.models import Parlamentar, Partido


class TipoMateriaLegislativa(models.Model):
    sigla_tipo_materia = models.CharField(max_length=5)
    descricao_tipo_materia = models.CharField(max_length=50)
    num_automatica = models.BooleanField()
    quorum_minimo_votacao = models.IntegerField()


class RegimeTramitacao(models.Model):
    descricao_regime_tramitacao = models.CharField(max_length=50)


class Origem(models.Model):
    sigla_origem = models.CharField(max_length=10)
    nome_origem = models.CharField(max_length=50)


class MateriaLegislativa(models.Model):
    tipo_id_basica = models.ForeignKey(TipoMateriaLegislativa)
    numero_protocolo = models.IntegerField(blank=True, null=True)
    numero_ident_basica = models.IntegerField()
    ano_ident_basica = models.SmallIntegerField()
    data_apresentacao = models.DateField(blank=True, null=True)
    tipo_apresentacao = models.CharField(max_length=1, blank=True, null=True)
    regime_tramitacao = models.ForeignKey(RegimeTramitacao)
    data_publicacao = models.DateField(blank=True, null=True)
    tipo_origem_externa = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, related_name='+')
    numero_origem_externa = models.CharField(max_length=5, blank=True, null=True)
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True)
    data_origem_externa = models.DateField(blank=True, null=True)
    local_origem_externa = models.ForeignKey(Origem, blank=True, null=True)
    nome_apelido = models.CharField(max_length=50, blank=True, null=True)
    numero_dias_prazo = models.IntegerField(blank=True, null=True)
    data_fim_prazo = models.DateField(blank=True, null=True)
    indicador_tramitacao = models.BooleanField()
    polemica = models.NullBooleanField(blank=True)
    descricao_objeto = models.CharField(max_length=150, blank=True, null=True)
    complementar = models.NullBooleanField(blank=True)
    txt_ementa = models.TextField()
    txt_indexacao = models.TextField(blank=True, null=True)
    txt_observacao = models.TextField(blank=True, null=True)
    txt_resultado = models.TextField(blank=True, null=True)
    # XXX novo
    anexadas = models.ManyToManyField('self', through='Anexada',
                                      symmetrical=False, related_name='anexo_de',
                                      through_fields=('materia_principal', 'materia_anexada'))


class AcompMateria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    endereco_email = models.CharField(max_length=100)
    txt_hash = models.CharField(max_length=8)


class Anexada(models.Model):
    materia_principal = models.ForeignKey(MateriaLegislativa, related_name='+')
    materia_anexada = models.ForeignKey(MateriaLegislativa, related_name='+')
    data_anexacao = models.DateField()
    data_desanexacao = models.DateField(blank=True, null=True)


class AssuntoMateria(models.Model):
    descricao_assunto = models.CharField(max_length=200)
    descricao_dispositivo = models.CharField(max_length=50)


class TipoAutor(models.Model):
    descricao_tipo_autor = models.CharField(max_length=50)


class Autor(models.Model):
    partido = models.ForeignKey(Partido, blank=True, null=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)
    tipo = models.ForeignKey(TipoAutor)
    nome_autor = models.CharField(max_length=50, blank=True, null=True)
    descricao_cargo = models.CharField(max_length=50, blank=True, null=True)
    col_username = models.CharField(max_length=50, blank=True, null=True)


class Autoria(models.Model):
    autor = models.ForeignKey(Autor)
    materia = models.ForeignKey(MateriaLegislativa)
    primeiro_autor = models.BooleanField()


class DespachoInicial(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    numero_ordem = models.IntegerField()
    comissao = models.ForeignKey(Comissao)


class TipoDocumento(models.Model):
    descricao_tipo_documento = models.CharField(max_length=50)


class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    tipo = models.ForeignKey(TipoDocumento)
    nome_documento = models.CharField(max_length=30)
    data_documento = models.DateField(blank=True, null=True)
    nome_autor_documento = models.CharField(max_length=50, blank=True, null=True)
    txt_ementa = models.TextField(blank=True, null=True)
    txt_indexacao = models.TextField(blank=True, null=True)


class MateriaAssunto(models.Model):
    assunto = models.ForeignKey(AssuntoMateria)
    materia = models.ForeignKey(MateriaLegislativa)


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    numero_ordem = models.IntegerField()
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa)
    numero_materia = models.CharField(max_length=5)
    ano_materia = models.SmallIntegerField()
    data_materia = models.DateField(blank=True, null=True)


class Orgao(models.Model):
    nome_orgao = models.CharField(max_length=60)
    sigla_orgao = models.CharField(max_length=10)
    unid_deliberativa = models.BooleanField()
    endereco_orgao = models.CharField(max_length=100, blank=True, null=True)
    numero_tel_orgao = models.CharField(max_length=50, blank=True, null=True)


class TipoFimRelatoria(models.Model):
    descricao_fim_relatoria = models.CharField(max_length=50)


class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    parlamentar = models.ForeignKey(Parlamentar)
    tipo_fim_relatoria = models.ForeignKey(TipoFimRelatoria, blank=True, null=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    data_desig_relator = models.DateField()
    data_destit_relator = models.DateField(blank=True, null=True)


class Parecer(models.Model):
    relatoria = models.ForeignKey(Relatoria)
    materia = models.ForeignKey(MateriaLegislativa)
    tipo_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tipo_apresentacao = models.CharField(max_length=1)
    txt_parecer = models.TextField(blank=True, null=True)


class TipoProposicao(models.Model):
    descricao_tipo_proposicao = models.CharField(max_length=50)
    mat_ou_doc = models.BooleanField()
    tipo_mat_ou_doc = models.IntegerField()
    nome_modelo = models.CharField(max_length=50)


class Proposicao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)
    autor = models.ForeignKey(Autor)
    tipo = models.ForeignKey(TipoProposicao)
    data_envio = models.DateTimeField()
    data_recebimento = models.DateTimeField(blank=True, null=True)
    txt_descricao = models.CharField(max_length=100)
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)
    data_devolucao = models.DateTimeField(blank=True, null=True)
    txt_justif_devolucao = models.CharField(max_length=200, blank=True, null=True)
    numero_proposicao = models.IntegerField(blank=True, null=True)


class StatusTramitacao(models.Model):
    sigla_status = models.CharField(max_length=10)
    descricao_status = models.CharField(max_length=60)
    fim_tramitacao = models.BooleanField()
    retorno_tramitacao = models.BooleanField()


class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    orgao = models.ForeignKey(Orgao, blank=True, null=True)
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)


class Tramitacao(models.Model):
    status = models.ForeignKey(StatusTramitacao, blank=True, null=True)
    materia = models.ForeignKey(MateriaLegislativa)
    data_tramitacao = models.DateField(blank=True, null=True)
    unid_tram_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+')
    data_encaminha = models.DateField(blank=True, null=True)
    unid_tram_dest = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+')
    ult_tramitacao = models.BooleanField()
    urgencia = models.BooleanField()
    sigla_turno = models.CharField(max_length=1, blank=True, null=True)
    txt_tramitacao = models.TextField(blank=True, null=True)
    data_fim_prazo = models.DateField(blank=True, null=True)
