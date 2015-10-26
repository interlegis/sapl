from django.db import models
from django.utils.translation import ugettext_lazy as _

from comissoes.models import Comissao
from parlamentares.models import Parlamentar, Partido
from sapl.utils import YES_NO_CHOICES, make_choices


class TipoMateriaLegislativa(models.Model):
    sigla = models.CharField(max_length=5, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição '))
    # XXX o que é isso ?
    num_automatica = models.BooleanField()
    # XXX o que é isso ?
    quorum_minimo_votacao = models.PositiveIntegerField()

    class Meta:
        verbose_name = _('Tipo de Matéria Legislativa')
        verbose_name_plural = _('Tipos de Matérias Legislativas')

    def __str__(self):
        return self.descricao


class RegimeTramitacao(models.Model):
    descricao = models.CharField(max_length=50)

    class Meta:
        verbose_name = _('Regime Tramitação')
        verbose_name_plural = _('Regimes Tramitação')

    def __str__(self):
        return self.descricao


class Origem(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Origem')
        verbose_name_plural = _('Origens')

    def __str__(self):
        return self.nome


def get_materia_media_path(instance, subpath, filename):
    return './materia/%s/%s/%s' % (instance.numero, subpath, filename)


def texto_upload_path(instance, filename):
    return get_materia_media_path(instance, 'materia', filename)


class MateriaLegislativa(models.Model):
    TIPO_APRESENTACAO_CHOICES, ORAL, ESCRITA = make_choices(
        'O', _('Oral'),
        'E', _('Escrita'),
    )

    tipo = models.ForeignKey(TipoMateriaLegislativa, verbose_name=_('Tipo'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))
    numero_protocolo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Núm. Protocolo'))
    data_apresentacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Apresentação'))
    tipo_apresentacao = models.CharField(
        max_length=1, blank=True, null=True,
        verbose_name=_('Tipo de Apresentação'),
        choices=TIPO_APRESENTACAO_CHOICES)
    regime_tramitacao = models.ForeignKey(
        RegimeTramitacao, verbose_name=_('Regime Tramitação'))
    data_publicacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Publicação'))
    tipo_origem_externa = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('Tipo'))
    numero_origem_externa = models.CharField(
        max_length=5, blank=True, null=True, verbose_name=_('Número'))
    ano_origem_externa = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_('Ano'))
    data_origem_externa = models.DateField(
        blank=True, null=True, verbose_name=_('Data'))
    local_origem_externa = models.ForeignKey(
        Origem, blank=True, null=True, verbose_name=_('Local Origem'))
    apelido = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_('Apelido'))
    dias_prazo = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Dias Prazo'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))
    em_tramitacao = models.BooleanField(verbose_name=_('Em Tramitação?'))
    polemica = models.NullBooleanField(
        blank=True, verbose_name=_('Matéria Polêmica?'))
    objeto = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_('Objeto'))
    complementar = models.NullBooleanField(
        blank=True, verbose_name=_('É Complementar?'))
    ementa = models.TextField(verbose_name=_('Ementa'))
    indexacao = models.TextField(
        blank=True, null=True, verbose_name=_('Indexação'))
    observacao = models.TextField(
        blank=True, null=True, verbose_name=_('Observação'))
    resultado = models.TextField(blank=True, null=True)
    # XXX novo
    anexadas = models.ManyToManyField(
        'self',
        through='Anexada',
        symmetrical=False,
        related_name='anexo_de',
        through_fields=(
            'materia_principal',
            'materia_anexada'))
    texto_original = models.FileField(
        blank=True,
        null=True,
        upload_to=texto_upload_path,
        verbose_name=_('Texto original (PDF)'))

    class Meta:
        verbose_name = _('Matéria Legislativa')
        verbose_name_plural = _('Matérias Legislativas')
        unique_together = (("tipo", "numero", "ano"),)

    def __str__(self):
        return _('%(tipo)s nº %(numero)s de %(ano)s') % {
            'tipo': self.tipo, 'numero': self.numero, 'ano': self.ano}


class AcompanhamentoMateria(models.Model):  # AcompMateria
    materia = models.ForeignKey(MateriaLegislativa)
    email = models.CharField(
        max_length=100, verbose_name=_('Endereço de E-mail'))
    hash = models.CharField(max_length=8)

    class Meta:
        verbose_name = _('Acompanhamento de Matéria')
        verbose_name_plural = _('Acompanhamentos de Matéria')

    def __str__(self):
        # FIXME str should be human readable, using hash is very strange
        return _('%(materia)s - #%(hash)s') % {
            'materia': self.materia, 'hash': self.hash}


class Anexada(models.Model):
    materia_principal = models.ForeignKey(MateriaLegislativa, related_name='+')
    materia_anexada = models.ForeignKey(MateriaLegislativa, related_name='+')
    data_anexacao = models.DateField(verbose_name=_('Data Anexação'))
    data_desanexacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Desanexação'))

    class Meta:
        verbose_name = _('Anexada')
        verbose_name_plural = _('Anexadas')

    def __str__(self):
        return _('Principal: %(materia_principal)s'
                 ' - Anexada: %(materia_anexada)s') % {
            'materia_principal': self.materia_principal,
            'materia_anexada': self.materia_anexada}


class AssuntoMateria(models.Model):
    assunto = models.CharField(max_length=200)
    dispositivo = models.CharField(max_length=50)

    class Meta:
        verbose_name = _('Assunto de Matéria')
        verbose_name_plural = _('Assuntos de Matéria')

    def __str__(self):
        return self.assunto


class TipoAutor(models.Model):
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))

    class Meta:
        verbose_name = _('Tipo de Autor')
        verbose_name_plural = _('Tipos de Autor')

    def __str__(self):
        return self.descricao


class Autor(models.Model):
    partido = models.ForeignKey(Partido, blank=True, null=True)
    comissao = models.ForeignKey(Comissao, blank=True, null=True)
    parlamentar = models.ForeignKey(Parlamentar, blank=True, null=True)
    tipo = models.ForeignKey(TipoAutor, verbose_name=_('Tipo'))
    nome = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_('Autor'))
    cargo = models.CharField(max_length=50, blank=True, null=True)
    username = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = _('Autor')
        verbose_name_plural = _('Autores')

    def __str__(self):
        if str(self.tipo) == 'Parlamentar':
            return str(self.parlamentar)
        elif str(self.tipo) == 'Comissao':
            return str(self.comissao)
        elif str(self.tipo) == 'Partido':
            return str(self.partido)
        else:
            if str(self.cargo):
                return _('%(nome)s - %(cargo)s') % {
                    'nome': self.nome, 'cargo': self.cargo}
            else:
                return str(self.nome)


class Autoria(models.Model):
    autor = models.ForeignKey(Autor)
    materia = models.ForeignKey(MateriaLegislativa)
    primeiro_autor = models.BooleanField(verbose_name=_('Primeiro Autor'))

    class Meta:
        verbose_name = _('Autoria')
        verbose_name_plural = _('Autorias')

    def __str__(self):
        return _('%(autor)s - %(materia)s') % {
            'autor': self.autor, 'materia': self.materia}


class DespachoInicial(models.Model):
    # TODO M2M?
    materia = models.ForeignKey(MateriaLegislativa)
    numero_ordem = models.PositiveIntegerField()
    comissao = models.ForeignKey(Comissao)

    class Meta:
        verbose_name = _('Despacho Inicial')
        verbose_name_plural = _('Despachos Iniciais')

    def __str__(self):
        return _('Nº %(numero)s - %(materia)s - %(comissao)s') % {
            'numero': self.numero_ordem,
            'materia': self.materia,
            'comissao': self.comissao}


class TipoDocumento(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Tipo Documento'))

    class Meta:
        verbose_name = _('Tipo de Documento')
        verbose_name_plural = _('Tipos de Documento')

    def __str__(self):
        return self.descricao


class DocumentoAcessorio(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    tipo = models.ForeignKey(TipoDocumento, verbose_name=_('Tipo'))
    nome = models.CharField(max_length=30, verbose_name=_('Descrição'))
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    autor = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_('Autor'))
    ementa = models.TextField(blank=True, null=True, verbose_name=_('Ementa'))
    indexacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Documento Acessório')
        verbose_name_plural = _('Documentos Acessórios')

    def __str__(self):
        return _('%(tipo)s - %(nome)s de %(data)s por %(autor)s') % {
            'tipo': self.tipo,
            'nome': self.nome,
            'data': self.data,
            'autor': self.autor}


class MateriaAssunto(models.Model):
    # TODO M2M ??
    assunto = models.ForeignKey(AssuntoMateria)
    materia = models.ForeignKey(MateriaLegislativa)

    class Meta:
        verbose_name = _('Relação Matéria - Assunto')
        verbose_name_plural = _('Relações Matéria - Assunto')

    def __str__(self):
        return _('%(materia)s - %(assunto)s') % {
            'materia': self.materia, 'assunto': self.assunto}


class Numeracao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    numero_ordem = models.PositiveIntegerField()
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa, verbose_name=_('Tipo de Matéria'))
    numero_materia = models.CharField(max_length=5, verbose_name=_('Número'))
    ano_materia = models.PositiveSmallIntegerField(verbose_name=_('Ano'))
    data_materia = models.DateField(
        blank=True, null=True, verbose_name=_('Data'))

    class Meta:
        verbose_name = _('Numeração')
        verbose_name_plural = _('Numerações')

    def __str__(self):
        return _('Nº%(numero)s %(tipo)s - %(data)s') % {
            'numero': self.numero_materia,
            'tipo': self.tipo_materia,
            'data': self.data_materia}


class Orgao(models.Model):
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    unidade_deliberativa = models.BooleanField(
        choices=YES_NO_CHOICES,
        verbose_name=('Unidade Deliberativa'))
    endereco = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_('Endereço'))
    telefone = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_('Telefone'))

    class Meta:
        verbose_name = _('Órgão')
        verbose_name_plural = _('Órgãos')

    def __str__(self):
        return _(
            '%(nome)s - %(sigla)s') % {'nome': self.nome, 'sigla': self.sigla}


class TipoFimRelatoria(models.Model):
    descricao = models.CharField(
        max_length=50, verbose_name=_('Tipo Fim Relatoria'))

    class Meta:
        verbose_name = _('Tipo Fim de Relatoria')
        verbose_name_plural = _('Tipos Fim de Relatoria')

    def __str__(self):
        return self.descricao


class Relatoria(models.Model):
    materia = models.ForeignKey(MateriaLegislativa)
    parlamentar = models.ForeignKey(Parlamentar, verbose_name=_('Parlamentar'))
    tipo_fim_relatoria = models.ForeignKey(
        TipoFimRelatoria,
        blank=True,
        null=True,
        verbose_name=_('Motivo Fim Relatoria'))
    comissao = models.ForeignKey(
        Comissao, blank=True, null=True, verbose_name=_('Localização Atual'))
    data_designacao_relator = models.DateField(
        verbose_name=_('Data Designação'))
    data_destituicao_relator = models.DateField(
        blank=True, null=True, verbose_name=_('Data Destituição'))

    class Meta:
        verbose_name = _('Relatoria')
        verbose_name_plural = _('Relatorias')

    def __str__(self):
        return _('%(materia)s - %(tipo)s - %(data)s') % {
            'materia': self.materia,
            'tipo': self.tipo_fim_relatoria,
            'data': self.data_designacao_relator}


class Parecer(models.Model):
    APRESENTACAO_CHOICES, ORAL, ESCRITA = make_choices(
        'O', _('Oral'),
        'E', _('Escrita'),
    )

    relatoria = models.ForeignKey(Relatoria)
    materia = models.ForeignKey(MateriaLegislativa)
    tipo_conclusao = models.CharField(max_length=3, blank=True, null=True)
    tipo_apresentacao = models.CharField(
        max_length=1, choices=APRESENTACAO_CHOICES)
    parecer = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = _('Parecer')
        verbose_name_plural = _('Pareceres')

    def __str__(self):
        return _('%(relatoria)s - %(tipo)s') % {
            'relatoria': self.relatoria, 'tipo': self.tipo_apresentacao
        }


class TipoProposicao(models.Model):
    MAT_OU_DOC_CHOICES, MATERIA, DOCUMENTO = make_choices(
        'M', _('Matéria'),
        'D', _('Documento'),
    )

    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    materia_ou_documento = models.CharField(
        max_length=1, verbose_name=_('Gera'), choices=MAT_OU_DOC_CHOICES)
    modelo = models.CharField(max_length=50, verbose_name=_('Modelo XML'))

    # mutually exclusive (depend on materia_ou_documento)
    tipo_materia = models.ForeignKey(
        TipoMateriaLegislativa,
        blank=True,
        null=True,
        verbose_name=_('Tipo Matéria'))
    tipo_documento = models.ForeignKey(
        TipoDocumento, blank=True, null=True, verbose_name=_('Tipo Documento'))

    class Meta:
        verbose_name = _('Tipo de Proposição')
        verbose_name_plural = _('Tipos de Proposições')

    def __str__(self):
        return self.descricao


class Proposicao(models.Model):
    materia = models.ForeignKey(MateriaLegislativa, blank=True, null=True)
    autor = models.ForeignKey(Autor)
    tipo = models.ForeignKey(TipoProposicao, verbose_name=_('Tipo'))
    # XXX data_envio was not null, but actual data said otherwise!!!
    data_envio = models.DateTimeField(
        null=True, verbose_name=_('Data de Envio'))
    data_recebimento = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Data de Incorporação'))
    descricao = models.CharField(max_length=100, verbose_name=_('Descrição'))
    data_devolucao = models.DateTimeField(
        blank=True, null=True, verbose_name=_('Data de devolução'))
    justificativa_devolucao = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Justificativa da Devolução'))
    numero_proposicao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número'))

    # ind_enviado and ind_devolvido collapsed as char field (status)

    status = models.CharField(blank=True,
                              null=True,
                              max_length=1,
                              choices=(('E', 'Enviada'),
                                       ('D', 'Devolvida'),
                                       ('I', 'Incorporada')),
                              verbose_name=_('Status Proposição'))

    # mutually exclusive (depend on tipo.materia_ou_documento)
    materia = models.ForeignKey(
        MateriaLegislativa, blank=True, null=True, verbose_name=_('Matéria'))
    documento = models.ForeignKey(
        DocumentoAcessorio, blank=True, null=True, verbose_name=_('Documento'))

    class Meta:
        verbose_name = _('Proposição')
        verbose_name_plural = _('Proposições')

    def __str__(self):
        return self.descricao


class StatusTramitacao(models.Model):
    INDICADOR_CHOICES, FIM, RETORNO = make_choices(
        'F', _('Fim'),
        'R', _('Retorno'),
    )

    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=60, verbose_name=_('Descrição'))
    # TODO make specific migration considering both ind_fim_tramitacao,
    # ind_retorno_tramitacao
    indicador = models.CharField(
        max_length=1, verbose_name=_('Indicador da Tramitação'),
        choices=INDICADOR_CHOICES)

    class Meta:
        verbose_name = _('Status de Tramitação')
        verbose_name_plural = _('Status de Tramitação')

    def __str__(self):
        return _('%(sigla)s - %(descricao)s - %(indicador)s') % {
            'sigla': self.sigla,
            'descricao': self.descricao,
            'indicador': self.indicador}


class UnidadeTramitacao(models.Model):
    comissao = models.ForeignKey(
        Comissao, blank=True, null=True, verbose_name=_('Comissão'))
    orgao = models.ForeignKey(
        Orgao, blank=True, null=True, verbose_name=_('Órgão'))
    parlamentar = models.ForeignKey(
        Parlamentar, blank=True, null=True, verbose_name=_('Parlamentar'))

    class Meta:
        verbose_name = _('Unidade de Tramitação')
        verbose_name_plural = _('Unidades de Tramitação')

    def __str__(self):
        return _('%(orgao)s %(comissao)s') % {
            'orgao': self.orgao, 'comissao': self.comissao
        }


class Tramitacao(models.Model):
    TURNO_CHOICES, \
        PRIMEIRO, SEGUNDO, UNICO, SUPLEMENTAR, FINAL, \
        VOTACAO_UNICA, PRIMEIRA_VOTACAO, \
        SEGUNDA_TERCEIRA_VOTACAO = make_choices(
            'P', _('Primeiro'),
            'S', _('Segundo'),
            'Ú', _('Único'),
            'L', _('Suplementar'),
            'F', _('Final'),
            'A', _('Votação única em Regime de Urgência'),
            'B', _('1ª Votação'),
            'C', _('2ª e 3ª Votação'),
        )

    status = models.ForeignKey(
        StatusTramitacao, blank=True, null=True, verbose_name=_('Status'))
    materia = models.ForeignKey(MateriaLegislativa)
    data_tramitacao = models.DateField(
        blank=True, null=True, verbose_name=_('Data Tramitação'))
    unidade_tramitacao_local = models.ForeignKey(
        UnidadeTramitacao,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('Unidade Local'))
    data_encaminhamento = models.DateField(
        blank=True, null=True, verbose_name=_('Data Encaminhamento'))
    unidade_tramitacao_destino = models.ForeignKey(
        UnidadeTramitacao,
        blank=True,
        null=True,
        related_name='+',
        verbose_name=_('Unidade Destino'))
    ultima = models.BooleanField()
    urgente = models.BooleanField(verbose_name=_('Urgente ?'))
    turno = models.CharField(
        max_length=1, blank=True, null=True, verbose_name=_('Turno'),
        choices=TURNO_CHOICES)
    texto = models.TextField(
        blank=True, null=True, verbose_name=_('Texto da Ação'))
    data_fim_prazo = models.DateField(
        blank=True, null=True, verbose_name=_('Data Fim Prazo'))

    class Meta:
        verbose_name = _('Tramitação')
        verbose_name_plural = _('Tramitações')

    def __str__(self):
        return _('%(materia)s | %(status)s | %(data)s') % {
            'materia': self.materia,
            'status': self.status,
            'data': self.data_tramitacao}
