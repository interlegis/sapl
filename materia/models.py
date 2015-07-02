# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from comissoes.models import Comissao
from parlamentares.models import Parlamentar, Partido


class TipoMateriaLegislativa(models.Model):
    sigla_tipo_materia = models.CharField(max_length=5, verbose_name=_(u'Sigla'))          # sgl_tipo_materia
    descricao_tipo_materia = models.CharField(max_length=50, verbose_name=_(u'Descrição '))     # des_tipo_materia
    num_automatica = models.BooleanField()                       # ind_num_automatica
    quorum_minimo_votacao = models.IntegerField()                # quorum_minimo_votacao

    class Meta:
        verbose_name = _(u'Tipo de Matéria Legislativa')
        verbose_name_plural = _(u'Tipos de Matérias Legislativas')


class RegimeTramitacao(models.Model):
    descricao_regime_tramitacao = models.CharField(max_length=50)  # des_regime_tramitacao

    class Meta:
        verbose_name = _(u'Regime Tramitação')
        verbose_name_plural = _(u'Regimes Tramitação')


class Origem(models.Model):
    sigla_origem = models.CharField(max_length=10, verbose_name=_(u'Sigla'))  # sgl_origem
    nome_origem = models.CharField(max_length=50, verbose_name=_(u'Nome'))    # nom_origem

    class Meta:
        verbose_name = _(u'Origem')
        verbose_name_plural = _(u'Origens')


class MateriaLegislativa(models.Model):
    tipo_id_basica = models.ForeignKey(TipoMateriaLegislativa, verbose_name=_(u'Tipo'))                                                # tip_id_basica
    numero_protocolo = models.IntegerField(blank=True, null=True,verbose_name=_(u'Núm. Protocolo'))                                                                      # num_protocolo
    numero_ident_basica = models.IntegerField(verbose_name=_(u'Número'))                                                               # num_ident_basica
    ano_ident_basica = models.SmallIntegerField(verbose_name=_(u'Ano'))                                                                # ano_ident_basica
    data_apresentacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Apresentação'))                                  # dat_apresentacao
    tipo_apresentacao = models.CharField(max_length=1, blank=True, null=True, verbose_name=_(u'Tipo de Apresentação'))                    # tip_apresentacao
    regime_tramitacao = models.ForeignKey(RegimeTramitacao, verbose_name=_(u'Regime Tramitação'))                                      # cod_regime_tramitacao
    data_publicacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Publicação'))                                      # dat_publicacao
    tipo_origem_externa = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, related_name='+', verbose_name=_(u'Tipo'))  # tip_origem_externa
    numero_origem_externa = models.CharField(max_length=5, blank=True, null=True, verbose_name=_(u'Número'))                           # num_origem_externa
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True, verbose_name=_(u'Ano'))                                       # ano_origem_externa
    data_origem_externa = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))                                             # dat_origem_externa
    local_origem_externa = models.ForeignKey(Origem, blank=True, null=True, verbose_name=_(u'Local Origem'))                           # cod_local_origem_externa
    nome_apelido = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Apelido'))                                  # nom_apelido
    numero_dias_prazo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Dias Prazo'))                                      # num_dias_prazo
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim Prazo'))                                        # dat_fim_prazo
    indicador_tramitacao = models.BooleanField(verbose_name=_(u'Em Tramitação?'))                                                      # ind_tramitacao
    polemica = models.NullBooleanField(blank=True, verbose_name=_(u'Matéria Polêmica?'))                                               # ind_polemica
    descricao_objeto = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Objeto'))                              # des_objeto
    complementar = models.NullBooleanField(blank=True, verbose_name=_(u'É Complementar?'))                                             # ind_complementar
    ementa = models.TextField(verbose_name=_(u'Ementa'))                                                                           # txt_ementa
    indexacao = models.TextField(blank=True, null=True, verbose_name=_(u'Indexação'))                                              # txt_indexacao
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))                                            # txt_observacao
    resultado = models.TextField(blank=True, null=True)                                                                            # txt_resultado
    # XXX novo
    anexadas = models.ManyToManyField('self', through='Anexada',
                                      symmetrical=False, related_name='anexo_de',
                                      through_fields=('materia_principal', 'materia_anexada'))

    class Meta:
        verbose_name = _(u'Matéria Legislativa')
        verbose_name_plural = _(u'Matérias Legislativas')


class AcompMateria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                           # cod_materia
    endereco_email = models.CharField(max_length=100, verbose_name=_(u'Endereço de E-mail'))  # end_email
    hash = models.CharField(max_length=8)                                                 # txt_hash

    class Meta:
        verbose_name = _(u'Acompanhamento de Matéria')
        verbose_name_plural = _(u'Acompanhamentos de Matéria')


class Anexada(models.Model):
    materia_principal = models.ForeignKey(MateriaLegislativa, related_name='+')                      # cod_materia_principal
    materia_anexada = models.ForeignKey(MateriaLegislativa, related_name='+')                        # cod_materia_anexada
    data_anexacao = models.DateField(verbose_name=_(u'Data Anexação'))                               # dat_anexacao
    data_desanexacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desanexação'))  # dat_desanexacao

    class Meta:
        verbose_name = _(u'Anexada')
        verbose_name_plural = _(u'Anexadas')


class AssuntoMateria(models.Model):
    descricao_assunto = models.CharField(max_length=200)     # des_assunto
    descricao_dispositivo = models.CharField(max_length=50)  # des_dispositivo

    class Meta:
        verbose_name = _(u'Assunto de Matéria')
        verbose_name_plural = _(u'Assuntos de Matéria')


class TipoAutor(models.Model):
    descricao_tipo_autor = models.CharField(max_length=50, verbose_name=_(u'Descrição'))  # des_tipo_autor

    class Meta:
        verbose_name = _(u'Tipo de Autor')
        verbose_name_plural = _(u'Tipos de Autor')


class Autor(models.Model):
    partido = models.ForeignKey(Partido, blank=True, null=True)                                    # cod_partido
    comissao = models.ForeignKey(Comissao, blank=True, null=True)                                  # cod_comissao
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)                            # cod_parlamentar
    tipo = models.ForeignKey(TipoAutor, verbose_name=_(u'Tipo'))                                   # tip_autor
    nome_autor = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Autor'))  # nom_autor
    descricao_cargo = models.CharField(max_length=50, blank=True, null=True)                       # des_cargo
    col_username = models.CharField(max_length=50, blank=True, null=True)                          # col_username

    class Meta:
        verbose_name = _(u'Autor')
        verbose_name_plural = _(u'Autores')


class Autoria(models.Model):
    autor = models.ForeignKey(Autor)                                         # cod_autor
    materia = models.ForeignKey(MateriaLegislativa)                          # cod_materia
    primeiro_autor = models.BooleanField(verbose_name=_(u'Primeiro Autor'))  # ind_primeiro_autor

    class Meta:
        verbose_name = _(u'Autoria')
        verbose_name_plural = _(u'Autorias')


class DespachoInicial(models.Model):
    # TODO M2M?
    materia = models.ForeignKey(MateriaLegislativa)     # cod_materia
    numero_ordem = models.IntegerField()                # num_ordem
    comissao = models.ForeignKey(Comissao)              # cod_comissao

    class Meta:
        verbose_name = _(u'Despacho Inicial')
        verbose_name_plural = _(u'Despachos Iniciais')


class TipoDocumento(models.Model):
    descricao_tipo_documento = models.CharField(max_length=50, verbose_name=_(u'Tipo Documento'))  # des_tipo_documento

    class Meta:
        verbose_name = _(u'Tipo de Documento')
        verbose_name_plural = _(u'Tipos de Documento')


class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                                          # cod_materia
    tipo = models.ForeignKey(TipoDocumento, verbose_name=_(u'Tipo'))                                         # tip_documento
    nome_documento = models.CharField(max_length=30, verbose_name=_(u'Descrição'))                           # nom_documento
    data_documento = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))                        # dat_documento
    nome_autor_documento = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Autor'))  # nom_autor_documento
    ementa = models.TextField(blank=True, null=True, verbose_name=_(u'Ementa'))                          # txt_ementa
    indexacao = models.TextField(blank=True, null=True)                                                  # txt_indexacao

    class Meta:
        verbose_name = _(u'Documento Acessório')
        verbose_name_plural = _(u'Documentos Acessórios')


class MateriaAssunto(models.Model):
    # TODO M2M ??
    assunto = models.ForeignKey(AssuntoMateria)        # cod_assunto
    materia = models.ForeignKey(MateriaLegislativa)    # cod_materia

    class Meta:
        verbose_name = _(u'Relação Matéria - Assunto')
        verbose_name_plural = _(u'Relações Matéria - Assunto')


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                            # cod_materia
    numero_ordem = models.IntegerField()                                                       # num_ordem
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, verbose_name=_(u'Tipo de Matéria'))  # tip_materia
    numero_materia = models.CharField(max_length=5, verbose_name=_(u'Número'))                 # num_materia
    ano_materia = models.SmallIntegerField(verbose_name=_(u'Ano'))                             # ano_materia
    data_materia = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))            # dat_materia

    class Meta:
        verbose_name = _(u'Numeração')
        verbose_name_plural = _(u'Numerações')


class Orgao(models.Model):
    nome_orgao = models.CharField(max_length=60, verbose_name=_(u'Nome'))                                   # nom_orgao
    sigla_orgao = models.CharField(max_length=10, verbose_name=_(u'Sigla'))                                 # sgl_orgao
    unid_deliberativa = models.BooleanField(verbose_name=_(u'Unidade Deliberativa'))                                                               # ind_unid_deliberativa
    endereco_orgao = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço'))   # end_orgao
    numero_tel_orgao = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone'))  # num_tel_orgao

    class Meta:
        verbose_name = _(u'Órgão')
        verbose_name_plural = _(u'Órgãos')


class TipoFimRelatoria(models.Model):
    descricao_fim_relatoria = models.CharField(max_length=50, verbose_name=_(u'Tipo Fim Relatoria'))  # des_fim_relatoria

    class Meta:
        verbose_name = _(u'Tipo Fim de Relatoria')
        verbose_name_plural = _(u'Tipos Fim de Relatoria')


class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)                                                                           # cod_materia
    parlamentar = models.ForeignKey(Parlamentar, verbose_name=_(u'Parlamentar'))                                                                              # cod_parlamentar
    tipo_fim_relatoria = models.ForeignKey(TipoFimRelatoria, blank=True, null=True, verbose_name=_(u'Motivo Fim Relatoria'))  # tip_fim_relatoria
    comissao = models.ForeignKey(Comissao, blank=True, null=True, verbose_name=_(u'Localização Atual'))                                                             # cod_comissao
    data_desig_relator = models.DateField(verbose_name=_(u'Data Designação'))                                                 # dat_desig_relator
    data_destit_relator = models.DateField(blank=True, null=True, verbose_name=_(u'Data Destituição'))                        # dat_destit_relator

    class Meta:
        verbose_name = _(u'Relatoria')
        verbose_name_plural = _(u'Relatorias')


class Parecer(models.Model):
    relatoria = models.ForeignKey(Relatoria)                                # cod_relatoria
    materia = models.ForeignKey(MateriaLegislativa)                         # cod_materia
    tipo_conclusao = models.CharField(max_length=3, blank=True, null=True)  # tip_conclusao
    tipo_apresentacao = models.CharField(max_length=1)                      # tip_apresentacao
    parecer = models.TextField(blank=True, null=True)                   # txt_parecer

    class Meta:
        verbose_name = _(u'Parecer')
        verbose_name_plural = _(u'Pareceres')


class TipoProposicao(models.Model):
    descricao_tipo_proposicao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))  # des_tipo_proposicao
    mat_ou_doc = models.BooleanField(verbose_name=_(u'Gera'))                           # ind_mat_ou_doc
    tipo_mat_ou_doc = models.IntegerField(verbose_name=_(u'Tipo Documento'))                      # tip_mat_ou_doc
    nome_modelo = models.CharField(max_length=50, verbose_name=_(u'Modelo XML'))                # nom_modelo

    class Meta:
        verbose_name = _(u'Tipo de Proposição')
        verbose_name_plural = _(u'Tipos de Proposições')


class Proposicao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)          # cod_materia
    autor = models.ForeignKey(Autor)                                                # cod_autor
    tipo = models.ForeignKey(TipoProposicao, verbose_name=_(u'Tipo'))               # tip_proposicao
    # XXX data_envio was not null, but actual data said otherwise!!!
    data_envio = models.DateTimeField(null=True)                                    # dat_envio
    data_recebimento = models.DateTimeField(blank=True, null=True)                  # dat_recebimento
    descricao = models.CharField(max_length=100, verbose_name=_(u'Descrição'))               # tip_proposicao
    # XXX data_envio was not null, but actual data said otherwise!!!)                                # txt_descricao
    cod_mat_ou_doc = models.IntegerField(blank=True, null=True)                     # cod_mat_ou_doc
    data_devolucao = models.DateTimeField(blank=True, null=True)                    # dat_devolucao
    justif_devolucao = models.CharField(max_length=200, blank=True, null=True)  # txt_justif_devolucao
    numero_proposicao = models.IntegerField(blank=True, null=True)                  # num_proposicao

    class Meta:
        verbose_name = _(u'Proposição')
        verbose_name_plural = _(u'Proposições')


class StatusTramitacao(models.Model):
    sigla_status = models.CharField(max_length=10, verbose_name=_(u'Sigla'))          # sgl_status
    descricao_status = models.CharField(max_length=60, verbose_name=_(u'Descrição'))  # des_status
    fim_tramitacao = models.BooleanField()                                            # ind_fim_tramitacao
    retorno_tramitacao = models.BooleanField()                                        # ind_retorno_tramitacao

    class Meta:
        verbose_name = _(u'Status de Tramitação')
        verbose_name_plural = _(u'Status de Tramitação')


class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(Comissao, blank=True, null=True, verbose_name=_(u'Comissão'))           # cod_comissao
    orgao = models.ForeignKey(Orgao, blank=True, null=True, verbose_name=_(u'Órgão'))                    # cod_orgao
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True, verbose_name=_(u'Parlamentar'))  # cod_parlamentar

    class Meta:
        verbose_name = _(u'Unidade de Tramitação')
        verbose_name_plural = _(u'Unidades de Tramitação')


class Tramitacao(models.Model):
    status = models.ForeignKey(StatusTramitacao, blank=True, null=True, verbose_name=_(u'Status'))                                      # cod_status
    materia = models.ForeignKey(MateriaLegislativa)                                                                                     # cod_materia
    data_tramitacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Tramitação'))                                                                           # dat_tramitacao
    unid_tram_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Local'))   # cod_unid_tram_local
    data_encaminha = models.DateField(blank=True, null=True, verbose_name=_(u'Data Encaminhamento'))                                    # dat_encaminha
    unid_tram_dest = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Destino'))  # cod_unid_tram_dest
    ult_tramitacao = models.BooleanField()                                                                                              # ind_ult_tramitacao
    urgencia = models.BooleanField(verbose_name=_(u'Urgente ?'))                                                                        # ind_urgencia
    sigla_turno = models.CharField(max_length=1, blank=True, null=True, verbose_name=_(u'Turno'))                                       # sgl_turno
    tramitacao = models.TextField(blank=True, null=True, verbose_name=_(u'Texto da Ação'))                                          # txt_tramitacao
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim Prazo'))                                         # dat_fim_prazo

    class Meta:
        verbose_name = _(u'Tramitação')
        verbose_name_plural = _(u'Tramitações')
