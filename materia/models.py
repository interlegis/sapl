# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext as _

from comissoes.models import Comissao
from parlamentares.models import Parlamentar, Partido


class TipoMateriaLegislativa(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_(u'Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição '))
    # XXX o que é isso ?
    num_automatica = models.BooleanField()
    # XXX o que é isso ?
    quorum_minimo_votacao = models.IntegerField()

    class Meta:
        verbose_name = _(u'Tipo de Matéria Legislativa')
        verbose_name_plural = _(u'Tipos de Matérias Legislativas')

    def __unicode__(self):
        return self.descricao


class RegimeTramitacao(models.Model):
    descricao = models.CharField(max_length=50)

    class Meta:
        verbose_name = _(u'Regime Tramitação')
        verbose_name_plural = _(u'Regimes Tramitação')

    def __unicode__(self):  
        return self.descricao


class Origem(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_(u'Nome'))

    class Meta:
        verbose_name = _(u'Origem')
        verbose_name_plural = _(u'Origens')

    def __unicode__(self):
        return self.nome


class MateriaLegislativa(models.Model):
    ORAL, ESCRITA = 'O', 'E'
    TIPO_APRESENTACAO_CHOICES = ((ORAL, _(u'Oral')),
                                 (ESCRITA, _(u'Escrita')))

    tipo = models.ForeignKey(TipoMateriaLegislativa, verbose_name=_(u'Tipo'))
    numero = models.IntegerField(verbose_name=_(u'Número'))
    ano = models.SmallIntegerField(verbose_name=_(u'Ano'))
    numero_protocolo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Núm. Protocolo'))
    data_apresentacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Apresentação'))
    tipo_apresentacao = models.CharField(max_length=1, blank=True, null=True, verbose_name=_(u'Tipo de Apresentação'), choices=TIPO_APRESENTACAO_CHOICES)
    regime_tramitacao = models.ForeignKey(RegimeTramitacao, verbose_name=_(u'Regime Tramitação'))
    data_publicacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Publicação'))
    tipo_origem_externa = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, related_name='+', verbose_name=_(u'Tipo'))
    numero_origem_externa = models.CharField(max_length=5, blank=True, null=True, verbose_name=_(u'Número'))
    ano_origem_externa = models.SmallIntegerField(blank=True, null=True, verbose_name=_(u'Ano'))
    data_origem_externa = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))
    local_origem_externa = models.ForeignKey(Origem, blank=True, null=True, verbose_name=_(u'Local Origem'))
    apelido = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Apelido'))
    dias_prazo = models.IntegerField(blank=True, null=True, verbose_name=_(u'Dias Prazo'))
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim Prazo'))
    em_tramitacao = models.BooleanField(verbose_name=_(u'Em Tramitação?'))
    polemica = models.NullBooleanField(blank=True, verbose_name=_(u'Matéria Polêmica?'))
    objeto = models.CharField(max_length=150, blank=True, null=True, verbose_name=_(u'Objeto'))
    complementar = models.NullBooleanField(blank=True, verbose_name=_(u'É Complementar?'))
    ementa = models.TextField(verbose_name=_(u'Ementa'))
    indexacao = models.TextField(blank=True, null=True, verbose_name=_(u'Indexação'))
    observacao = models.TextField(blank=True, null=True, verbose_name=_(u'Observação'))
    resultado = models.TextField(blank=True, null=True)
    # XXX novo
    anexadas = models.ManyToManyField('self', through='Anexada',
                                      symmetrical=False, related_name='anexo_de',
                                      through_fields=('materia_principal', 'materia_anexada'))

    class Meta:
        verbose_name = _(u'Matéria Legislativa')
        verbose_name_plural = _(u'Matérias Legislativas')

    def __unicode__(self):
        return _(u'%(tipo)s nº %(numero)s de %(ano)s') % {
            'tipo': self.tipo, 'numero': self.numero, 'ano': self.ano}


class AcompanhamentoMateria(models.Model):  # AcompMateria
    materia = models.ForeignKey(MateriaLegislativa)
    email = models.CharField(max_length=100, verbose_name=_(u'Endereço de E-mail'))
    hash = models.CharField(max_length=8)

    class Meta:
        verbose_name = _(u'Acompanhamento de Matéria')
        verbose_name_plural = _(u'Acompanhamentos de Matéria')

    def __unicode__ (self):
        return self.materia

class Anexada(models.Model):
    materia_principal = models.ForeignKey(MateriaLegislativa, related_name='+')
    materia_anexada = models.ForeignKey(MateriaLegislativa, related_name='+')
    data_anexacao = models.DateField(verbose_name=_(u'Data Anexação'))
    data_desanexacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Desanexação'))

    class Meta:
        verbose_name = _(u'Anexada')
        verbose_name_plural = _(u'Anexadas')

    def __unicode__(self):
        return _(u'Principal: %(materia_principal)s - Anexada: %(materia_anexada)s') % {
            'materia_principal': self.materia_principal, 'materia_anexada': self.materia_anexada}


class AssuntoMateria(models.Model):
    assunto = models.CharField(max_length=200)
    dispositivo = models.CharField(max_length=50)

    class Meta:
        verbose_name = _(u'Assunto de Matéria')
        verbose_name_plural = _(u'Assuntos de Matéria')

    def __unicode__(self):
        return self.assunto


class TipoAutor(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))

    class Meta:
        verbose_name = _(u'Tipo de Autor')
        verbose_name_plural = _(u'Tipos de Autor')

    def __unicode__(self):
        return self.descricao


class Autor(models.Model):
    partido = models.ForeignKey(Partido, blank=True, null=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)
    tipo = models.ForeignKey(TipoAutor, verbose_name=_(u'Tipo'))
    nome = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Autor'))
    cargo = models.CharField(max_length=50, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _(u'Autor')
        verbose_name_plural = _(u'Autores')

    def __unicode__(self):
        if unicode(self.tipo) == 'Parlamentar':
            return unicode(self.parlamentar)
        elif unicode(self.tipo) == 'Comissao':
            return unicode(self.comissao)
        elif unicode(self.tipo) == 'Partido':
            return unicode(self.partido)
        else:
            if unicode(self.cargo):
                return  _(u'%(nome)s - %(cargo)s') % {'nome': self.nome, 'cargo': self.cargo}
            else:
                return unicode(self.nome)


class Autoria(models.Model):
    autor = models.ForeignKey(Autor)
    materia = models.ForeignKey(MateriaLegislativa)
    primeiro_autor = models.BooleanField(verbose_name=_(u'Primeiro Autor'))

    class Meta:
        verbose_name = _(u'Autoria')
        verbose_name_plural = _(u'Autorias')

    def __unicode__(self):
        return  _(u'%(autor)s - %(materia)s') % {'autor': self.autor, 'materia': self.materia}

class DespachoInicial(models.Model):
    # TODO M2M?
    materia = models.ForeignKey(MateriaLegislativa)
    numero_ordem = models.IntegerField()
    comissao = models.ForeignKey(Comissao)

    class Meta:
        verbose_name = _(u'Despacho Inicial')
        verbose_name_plural = _(u'Despachos Iniciais')

    def __unicode__(self):
        return  _(u'Nº %(numero)s - %(materia)s - %(comissao)s') % {'numero': self.numero_ordem, 'materia': self.materia, 'comissao': self.comissao}

class TipoDocumento(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Tipo Documento'))

    class Meta:
        verbose_name = _(u'Tipo de Documento')
        verbose_name_plural = _(u'Tipos de Documento')

    def __unicode__ (self):
        return self.descricao


class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    tipo = models.ForeignKey(TipoDocumento, verbose_name=_(u'Tipo'))
    nome = models.CharField(max_length=30, verbose_name=_(u'Descrição'))
    data = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))
    autor = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Autor'))
    ementa = models.TextField(blank=True, null=True, verbose_name=_(u'Ementa'))
    indexacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'Documento Acessório')
        verbose_name_plural = _(u'Documentos Acessórios')

    def __unicode__(self):
        return _(u'%(tipo)s - %(nome)s de %(data)s por %(autor)s') % {
            'tipo': self.tipo, 'nome': self.nome, 'ano': self.data, 'autor': self.autor} 


class MateriaAssunto(models.Model):
    # TODO M2M ??
    assunto = models.ForeignKey(AssuntoMateria)
    materia = models.ForeignKey(MateriaLegislativa)

    class Meta:
        verbose_name = _(u'Relação Matéria - Assunto')
        verbose_name_plural = _(u'Relações Matéria - Assunto')

    def __unicode__(self):
        return _(u'%(materia)s - %(assunto)s') % { 'materia': self.materia, 'assunto': self.assunto}


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    numero_ordem = models.IntegerField()
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, verbose_name=_(u'Tipo de Matéria'))
    numero_materia = models.CharField(max_length=5, verbose_name=_(u'Número'))
    ano_materia = models.SmallIntegerField(verbose_name=_(u'Ano'))
    data_materia = models.DateField(blank=True, null=True, verbose_name=_(u'Data'))

    class Meta:
        verbose_name = _(u'Numeração')
        verbose_name_plural = _(u'Numerações')

    def __unicode_ (self):
        return _(u'Nº%(numero)s %(tipo)s - %(data)s') % { 
             'numero': self.numero_materia, 'tipo': self.tipo_materia, 'data': self.data_materia }


class Orgao(models.Model):
    nome = models.CharField(max_length=60, verbose_name=_(u'Nome'))
    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))
    unidade_deliberativa = models.BooleanField(verbose_name=_(u'Unidade Deliberativa'))
    endereco = models.CharField(max_length=100, blank=True, null=True, verbose_name=_(u'Endereço'))
    telefone = models.CharField(max_length=50, blank=True, null=True, verbose_name=_(u'Telefone'))

    class Meta:
        verbose_name = _(u'Órgão')
        verbose_name_plural = _(u'Órgãos')

    def __unicode__(self):
        return _(u'%(nome)s - %(sigla)s') % { 'nome': self.nome, 'sigla':self.sigla }


class TipoFimRelatoria(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_(u'Tipo Fim Relatoria'))

    class Meta:
        verbose_name = _(u'Tipo Fim de Relatoria')
        verbose_name_plural = _(u'Tipos Fim de Relatoria')

    def __unicode__(self):
        return self.descricao

class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    parlamentar = models.ForeignKey(Parlamentar, verbose_name=_(u'Parlamentar'))
    tipo_fim_relatoria = models.ForeignKey(TipoFimRelatoria, blank=True, null=True, verbose_name=_(u'Motivo Fim Relatoria'))
    comissao = models.ForeignKey(Comissao, blank=True, null=True, verbose_name=_(u'Localização Atual'))
    data_designacao_relator = models.DateField(verbose_name=_(u'Data Designação'))
    data_destituicao_relator = models.DateField(blank=True, null=True, verbose_name=_(u'Data Destituição'))

    class Meta:
        verbose_name = _(u'Relatoria')
        verbose_name_plural = _(u'Relatorias')

    def __unicode__ (self):
        return _(u'%(materia)s - %(tipo)s - %(data)s') % {
           'materia': self.materia, 'tipo': self.tipo_fim_relatoria, 'data': self.data_designacao_relator
        }


class Parecer(models.Model):
    ORAL = 'O'
    ESCRITA = 'E'
    APRESENTACAO_CHOICES = ((ORAL, _(u'Oral')),
                            (ESCRITA, _(u'Escrita')))

    relatoria = models.ForeignKey(Relatoria)
    materia = models.ForeignKey(MateriaLegislativa)
    tipo_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tipo_apresentacao = models.CharField(max_length=1, choices=APRESENTACAO_CHOICES)
    parecer = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'Parecer')
        verbose_name_plural = _(u'Pareceres')

    def __unicode__ (self):
        return _(u'%(relatoria)s - %(tipo)s') % {
            'relatoria': self.relatoria, 'tipo': self.tipo_apresentacao
        }


class TipoProposicao(models.Model):
    MATERIA = 'M'
    DOCUMENTO = 'D'
    MAT_OU_DOC_CHOICES = ((MATERIA, _(u'Matéria')),
                          (DOCUMENTO, _(u'Documento')))

    descricao = models.CharField(max_length=50, verbose_name=_(u'Descrição'))
    materia_ou_documento = models.CharField(max_length=1, verbose_name=_(u'Gera'), choices=MAT_OU_DOC_CHOICES)
    modelo = models.CharField(max_length=50, verbose_name=_(u'Modelo XML'))

    # mutually exclusive (depend on materia_ou_documento)
    tipo_materia = models.ForeignKey(TipoMateriaLegislativa, blank=True, null=True, verbose_name=_(u'Tipo Matéria'))
    tipo_documento = models.ForeignKey(TipoDocumento, blank=True, null=True, verbose_name=_(u'Tipo Documento'))

    class Meta:
        verbose_name = _(u'Tipo de Proposição')
        verbose_name_plural = _(u'Tipos de Proposições')

    def __unicode__ (self):
        return self.descricao


class Proposicao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)
    autor = models.ForeignKey(Autor)
    tipo = models.ForeignKey(TipoProposicao, verbose_name=_(u'Tipo'))
    # XXX data_envio was not null, but actual data said otherwise!!!
    data_envio = models.DateTimeField(null=True, verbose_name=_(u'Data de Envio'))
    data_recebimento = models.DateTimeField(blank=True, null=True, verbose_name=_(u'Data de Incorporação'))
    descricao = models.CharField(max_length=100, verbose_name=_(u'Descrição'))
    data_devolucao = models.DateTimeField(blank=True, null=True, verbose_name=_(u'Data de devolução'))
    justificativa_devolucao = models.CharField(max_length=200, blank=True, null=True, verbose_name=_(u'Justificativa da Devolução'))
    numero_proposicao = models.IntegerField(blank=True, null=True, verbose_name=_(u''))

    # mutually exclusive (depend on tipo.materia_ou_documento)
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True, verbose_name=_(u'Matéria'))
    documento = models.ForeignKey(DocumentoAcessorio, blank=True, null=True, verbose_name=_(u'Documento'))

    class Meta:
        verbose_name = _(u'Proposição')
        verbose_name_plural = _(u'Proposições')

    def __unicode__ (self):
        return self.descricao


class StatusTramitacao(models.Model):
    FIM = 'F'
    RETORNO = 'R'
    INDICADOR_CHOICES = ((FIM, _(u'Fim')),
                         (RETORNO, _(u'Retorno')))

    sigla = models.CharField(max_length=10, verbose_name=_(u'Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_(u'Descrição'))
    # TODO make specific migration considering both ind_fim_tramitacao, ind_retorno_tramitacao
    indicador = models.CharField(max_length=1, verbose_name=_(u'Indicador da Tramitação'), choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _(u'Status de Tramitação')
        verbose_name_plural = _(u'Status de Tramitação')

    def __unicode__(self):
        return _(u'%(sigla)s - %(descricao)s - %(indicador)s') % {
            'sigla': self.sigla, 'descricao': self.descricao, 'indicador': self.indicador
        }


class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(Comissao, blank=True, null=True, verbose_name=_(u'Comissão'))
    orgao = models.ForeignKey(Orgao, blank=True, null=True, verbose_name=_(u'Órgão'))
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True, verbose_name=_(u'Parlamentar'))

    class Meta:
        verbose_name = _(u'Unidade de Tramitação')
        verbose_name_plural = _(u'Unidades de Tramitação')

    def __unicode__ (self):
        return _(u'%(orgao)s %(comissao)s') % {
            'orgao': self.orgao, 'comissao': self.comissao
        }


class Tramitacao(models.Model):
    PRIMEIRO = 'P'
    SEGUNDO = 'S'
    UNICO = 'Ú'
    SUPLEMENTAR = 'L'
    FINAL = 'F'
    VOTACAO_UNICA = 'A'
    PRIMEIRA_VOTACAO = 'B'
    SEGUNDA_TERCEIRA_VOTACAO = 'C'
    TURNO_CHOICES = ((PRIMEIRO, _(u'Primeiro')),
                     (SEGUNDO, _(u'Segundo')),
                     (UNICO, _(u'Único')),
                     (SUPLEMENTAR, _(u'Suplementar')),
                     (FINAL, _(u'Final')),
                     (VOTACAO_UNICA, _(u'Votação única em Regime de Urgência')),
                     (PRIMEIRA_VOTACAO, _(u'1ª Votação')),
                     (SEGUNDA_TERCEIRA_VOTACAO, _(u'2ª e 3ª Votação')))

    status = models.ForeignKey(StatusTramitacao, blank=True, null=True, verbose_name=_(u'Status'))
    materia = models.ForeignKey(MateriaLegislativa)
    data_tramitacao = models.DateField(blank=True, null=True, verbose_name=_(u'Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Local'))
    data_encaminhamento = models.DateField(blank=True, null=True, verbose_name=_(u'Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(UnidadeTramitacao, blank=True, null=True, related_name='+', verbose_name=_(u'Unidade Destino'))
    ultima = models.BooleanField()
    urgente = models.BooleanField(verbose_name=_(u'Urgente ?'))
    turno = models.CharField(max_length=1, blank=True, null=True, verbose_name=_(u'Turno'), choices=TURNO_CHOICES)
    texto = models.TextField(blank=True, null=True, verbose_name=_(u'Texto da Ação'))
    data_fim_prazo = models.DateField(blank=True, null=True, verbose_name=_(u'Data Fim Prazo'))

    class Meta:
        verbose_name = _(u'Tramitação')
        verbose_name_plural = _(u'Tramitações')

    def __unicode__ (self):
        return _(u'%(materia)s | %(status)s | %(data)s') % {
            'materia': self.materia, 'status': self.status, 'data': self.data_tramitacao
        }
