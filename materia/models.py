from django.db import models

from comissoes.models import Comissao
from parlamentares.models import Parlamentar, Partido


class TipoMateriaLegislativa(models.Model):
    sigla_tipo_materia = models.CharField(max_length=5)       # sgl_tipo_materia
    descricao_tipo_materia = models.CharField(max_length=50)  # des_tipo_materia
    num_automatica = models.BooleanField()                    # ind_num_automatica
    quorum_minimo_votacao = models.IntegerField()             # quorum_minimo_votacao


class RegimeTramitacao(models.Model):
    descricao_regime_tramitacao = models.CharField(max_length=50)  # des_regime_tramitacao


class Origem(models.Model):
    sigla_origem = models.CharField(max_length=10)  # sgl_origem
    nome_origem = models.CharField(max_length=50)   # nom_origem


class MateriaLegislativa(models.Model):
    tipo_id_basica = models.ForeignKey(TipoMateriaLegislativa)                                                # tip_id_basica
    numero_protocolo = models.IntegerField(blank=True, null=True)                                             # num_protocolo
    numero_ident_basica = models.IntegerField()                                                               # num_ident_basica
    ano_ident_basica = models.SmallIntegerField()                                                             # ano_ident_basica
    data_apresentacao = models.DateField(blank=True, null=True)                                               # dat_apresentacao
    tipo_apresentacao = models.CharField(max_length=1, blank=True, null=True)                                 # tip_apresentacao
    regime_tramitacao = models.ForeignKey(RegimeTramitacao)                                                   # cod_regime_tramitacao
    data_publicacao = models.DateField(blank=True, null=True)                                                 # dat_publicacao
    tipo_origem_externa = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, related_name='+')  # tip_origem_externa
    numero_origem_externa = models.CharField(max_length=5, blank=True, null=True)                             # num_origem_externa
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True)                                      # ano_origem_externa
    data_origem_externa = models.DateField(blank=True, null=True)                                             # dat_origem_externa
    local_origem_externa = models.ForeignKey(Origem, blank=True, null=True)                                   # cod_local_origem_externa
    nome_apelido = models.CharField(max_length=50, blank=True, null=True)                                     # nom_apelido
    numero_dias_prazo = models.IntegerField(blank=True, null=True)                                            # num_dias_prazo
    data_fim_prazo = models.DateField(blank=True, null=True)                                                  # dat_fim_prazo
    indicador_tramitacao = models.BooleanField()                                                              # ind_tramitacao
    polemica = models.NullBooleanField(blank=True)                                                            # ind_polemica
    descricao_objeto = models.CharField(max_length=150, blank=True, null=True)                                # des_objeto
    complementar = models.NullBooleanField(blank=True)                                                        # ind_complementar
    txt_ementa = models.TextField()                                                                           # txt_ementa
    txt_indexacao = models.TextField(blank=True, null=True)                                                   # txt_indexacao
    txt_observacao = models.TextField(blank=True, null=True)                                                  # txt_observacao
    txt_resultado = models.TextField(blank=True, null=True)                                                   # txt_resultado
    # XXX novo
    anexadas = models.ManyToManyField('self', through='Anexada',
                                      symmetrical=False, related_name='anexo_de',
                                      through_fields=('materia_principal', 'materia_anexada'))


class AcompMateria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)    # cod_materia
    endereco_email = models.CharField(max_length=100)  # end_email
    txt_hash = models.CharField(max_length=8)          # txt_hash


class Anexada(models.Model):
    materia_principal = models.ForeignKey(MateriaLegislativa, related_name='+')  # cod_materia_principal
    materia_anexada = models.ForeignKey(MateriaLegislativa, related_name='+')    # cod_materia_anexada
    data_anexacao = models.DateField()                                           # dat_anexacao
    data_desanexacao = models.DateField(blank=True, null=True)                   # dat_desanexacao


class AssuntoMateria(models.Model):
    descricao_assunto = models.CharField(max_length=200)     # des_assunto
    descricao_dispositivo = models.CharField(max_length=50)  # des_dispositivo


class TipoAutor(models.Model):
    descricao_tipo_autor = models.CharField(max_length=50)  # des_tipo_autor


class Autor(models.Model):
    partido = models.ForeignKey(Partido, blank=True, null=True)               # cod_partido
    comissao = models.ForeignKey(Comissao, blank=True, null=True)             # cod_comissao
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)       # cod_parlamentar
    tipo = models.ForeignKey(TipoAutor)                                       # tip_autor
    nome_autor = models.CharField(max_length=50, blank=True, null=True)       # nom_autor
    descricao_cargo = models.CharField(max_length=50, blank=True, null=True)  # des_cargo
    col_username = models.CharField(max_length=50, blank=True, null=True)     # col_username


class Autoria(models.Model):
    autor = models.ForeignKey(Autor)                 # cod_autor
    materia = models.ForeignKey(MateriaLegislativa)  # cod_materia
    primeiro_autor = models.BooleanField()           # ind_primeiro_autor


class DespachoInicial(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)  # cod_materia
    numero_ordem = models.IntegerField()             # num_ordem
    comissao = models.ForeignKey(Comissao)           # cod_comissao


class TipoDocumento(models.Model):
    descricao_tipo_documento = models.CharField(max_length=50)  # des_tipo_documento


class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                # cod_materia
    tipo = models.ForeignKey(TipoDocumento)                                        # tip_documento
    nome_documento = models.CharField(max_length=30)                               # nom_documento
    data_documento = models.DateField(blank=True, null=True)                       # dat_documento
    nome_autor_documento = models.CharField(max_length=50, blank=True, null=True)  # nom_autor_documento
    txt_ementa = models.TextField(blank=True, null=True)                           # txt_ementa
    txt_indexacao = models.TextField(blank=True, null=True)                        # txt_indexacao


class MateriaAssunto(models.Model):
    assunto = models.ForeignKey(AssuntoMateria)      # cod_assunto
    materia = models.ForeignKey(MateriaLegislativa)  # cod_materia


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)           # cod_materia
    numero_ordem = models.IntegerField()                      # num_ordem
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa)  # tip_materia
    numero_materia = models.CharField(max_length=5)           # num_materia
    ano_materia = models.SmallIntegerField()                  # ano_materia
    data_materia = models.DateField(blank=True, null=True)    # dat_materia


class Orgao(models.Model):
    nome_orgao = models.CharField(max_length=60)                               # nom_orgao
    sigla_orgao = models.CharField(max_length=10)                              # sgl_orgao
    unid_deliberativa = models.BooleanField()                                  # ind_unid_deliberativa
    endereco_orgao = models.CharField(max_length=100, blank=True, null=True)   # end_orgao
    numero_tel_orgao = models.CharField(max_length=50, blank=True, null=True)  # num_tel_orgao


class TipoFimRelatoria(models.Model):
    descricao_fim_relatoria = models.CharField(max_length=50)  # des_fim_relatoria


class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                  # cod_materia
    parlamentar = models.ForeignKey(Parlamentar)                                     # cod_parlamentar
    tipo_fim_relatoria = models.ForeignKey(TipoFimRelatoria, blank=True, null=True)  # tip_fim_relatoria
    comissao = models.ForeignKey(Comissao, blank=True, null=True)                    # cod_comissao
    data_desig_relator = models.DateField()                                          # dat_desig_relator
    data_destit_relator = models.DateField(blank=True, null=True)                    # dat_destit_relator


class Parecer(models.Model):
    relatoria = models.ForeignKey(Relatoria)                                # cod_relatoria
    materia = models.ForeignKey(MateriaLegislativa)                         # cod_materia
    tipo_conclusao = models.CharField(max_length=3, blank=True, null=True)  # tip_conclusao
    tipo_apresentacao = models.CharField(max_length=1)                      # tip_apresentacao
    txt_parecer = models.TextField(blank=True, null=True)                   # txt_parecer


class TipoProposicao(models.Model):
    descricao_tipo_proposicao = models.CharField(max_length=50)  # des_tipo_proposicao
    mat_ou_doc = models.BooleanField()                           # ind_mat_ou_doc
    tipo_mat_ou_doc = models.IntegerField()                      # tip_mat_ou_doc
    nome_modelo = models.CharField(max_length=50)                # nom_modelo


class Proposicao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)          # cod_materia
    autor = models.ForeignKey(Autor)                                                # cod_autor
    tipo = models.ForeignKey(TipoProposicao)                                        # tip_proposicao
    # XXX data_envio was not null, but actual data said otherwise!!!
    data_envio = models.DateTimeField(null=True)                                    # dat_envio
    data_recebimento = models.DateTimeField(blank=True, null=True)                  # dat_recebimento
    txt_descricao = models.CharField(max_length=100)                                # txt_descricao
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)                     # cod_mat_ou_doc
    data_devolucao = models.DateTimeField(blank=True, null=True)                    # dat_devolucao
    txt_justif_devolucao = models.CharField(max_length=200, blank=True, null=True)  # txt_justif_devolucao
    numero_proposicao = models.IntegerField(blank=True, null=True)                  # num_proposicao


class StatusTramitacao(models.Model):
    sigla_status = models.CharField(max_length=10)      # sgl_status
    descricao_status = models.CharField(max_length=60)  # des_status
    fim_tramitacao = models.BooleanField()              # ind_fim_tramitacao
    retorno_tramitacao = models.BooleanField()          # ind_retorno_tramitacao


class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(Comissao, blank=True, null=True)        # cod_comissao
    orgao = models.ForeignKey(Orgao, blank=True, null=True)              # cod_orgao
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)  # cod_parlamentar


class Tramitacao(models.Model):
    status = models.ForeignKey(StatusTramitacao, blank=True, null=True)                              # cod_status
    materia = models.ForeignKey(MateriaLegislativa)                                                  # cod_materia
    data_tramitacao = models.DateField(blank=True, null=True)                                        # dat_tramitacao
    unid_tram_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+')  # cod_unid_tram_local
    data_encaminha = models.DateField(blank=True, null=True)                                         # dat_encaminha
    unid_tram_dest = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+')   # cod_unid_tram_dest
    ult_tramitacao = models.BooleanField()                                                           # ind_ult_tramitacao
    urgencia = models.BooleanField()                                                                 # ind_urgencia
    sigla_turno = models.CharField(max_length=1, blank=True, null=True)                              # sgl_turno
    txt_tramitacao = models.TextField(blank=True, null=True)                                         # txt_tramitacao
    data_fim_prazo = models.DateField(blank=True, null=True)                                         # dat_fim_prazo
