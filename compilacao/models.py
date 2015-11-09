from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from django.db.models.aggregates import Max
from django.utils.translation import ugettext_lazy as _

from norma.models import NormaJuridica
from sapl import utils
from sapl.utils import YES_NO_CHOICES


class BaseModel(models.Model):

    class Meta:
        abstract = True

    def clean(self):
        """
        Check for instances with null values in unique_together fields.
        """
        from django.core.exceptions import ValidationError

        super(BaseModel, self).clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter['%s__isnull' % field_name] = True
                    null_found = True
                else:
                    unique_filter['%s' % field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(
                    **unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(
                        self.__class__, tuple(unique_fields))
                    raise ValidationError(msg)


class TipoNota(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    modelo = models.TextField(
        blank=True, verbose_name=_('Modelo'))

    class Meta:
        verbose_name = _('Tipo de Nota')
        verbose_name_plural = _('Tipos de Nota')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


class TipoVide(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Tipo de Vide')
        verbose_name_plural = _('Tipos de Vide')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


class TipoDispositivo(BaseModel):
    """
    - para class_css articulacao, omissis, ementa,
                     bloco_alteracao, artigo, caput e paragrafo
      são palavras chaves usadas no código e de existência obrigatória.

    - apenas articulacao recebe nivel zero

    - no attributo rotulo_prefixo_texto, caso haja um ';' (ponto e vírgula), e
      só pode haver 1 ';', o método [def rotulo_padrao] considerará que o
      rótulo do dispositivo deverá ser escrito com o contéudo após o ';'
      caso para o pai do dispositivo em processamento exista apenas
      o próprio como filho

    - ao o usuário trocar manualmente o rotulo para a opção após o ';'
      necessáriamente o numeração do dispositivo deve ser redusida a 0,
      podendo manter as variações

    -tipo de dispositivos com contagem continua são continua porém encapsuladas
      em articulação... mudando articulação, reinicia-se a contagem

    - revogação de dispositivo_de_articulacao revogam todo o conteúdo
    """
    FNC1 = '1'
    FNCI = 'I'
    FNCi = 'i'
    FNCA = 'A'
    FNCa = 'a'
    FNC8 = '*'
    FNCN = 'N'
    FORMATO_NUMERACAO_CHOICES = (
        (FNC1, _('1-Numérico')),
        (FNCI, _('I-Romano Maiúsculo')),
        (FNCi, _('i-Romano Minúsculo')),
        (FNCA, _('A-Alfabético Maiúsculo')),
        (FNCa, _('a-Alfabético Minúsculo')),
        (FNC8, _('Tópico - Sem contagem')),
        (FNCN, _('Sem renderização')),
    )

    # Choice básico. Porém pode ser melhorado dando a opção de digitar outro
    # valor maior que zero e diferente de nove. A App de edição de rótulo,
    # entenderá que deverá colocar ordinal até o valor armazenado ou em tudo
    # se for igual -1.
    TNRT = -1
    TNRN = 0
    TNR9 = 9
    TIPO_NUMERO_ROTULO = (
        (TNRN, _('Numeração Cardinal.')),
        (TNRT, _('Numeração Ordinal.')),
        (TNR9, _('Numeração Ordinal até o item nove.')),
    )

    nome = models.CharField(
        max_length=50, unique=True, verbose_name=_('Nome'))
    class_css = models.CharField(
        blank=True,
        max_length=20,
        verbose_name=_('Classe CSS'))
    rotulo_prefixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Prefixo html do rótulo'))
    rotulo_prefixo_texto = models.CharField(
        blank=True,
        max_length=30,
        verbose_name=_('Prefixo de Edição do rótulo'))
    rotulo_ordinal = models.IntegerField(
        choices=TIPO_NUMERO_ROTULO,
        verbose_name=_('Tipo de número do rótulo'))
    rotulo_separador_variacao01 = models.CharField(
        blank=False,
        max_length=1,
        default="-",
        verbose_name=_('Separador entre Numeração e Variação 1'))
    rotulo_separador_variacao12 = models.CharField(
        blank=False,
        max_length=1,
        default="-",
        verbose_name=_('Separador entre Variação 1 e Variação 2'))
    rotulo_separador_variacao23 = models.CharField(
        blank=False,
        max_length=1,
        default="-",
        verbose_name=_('Separador entre Variação 2 e Variação 3'))
    rotulo_separador_variacao34 = models.CharField(
        blank=False,
        max_length=1,
        default="-",
        verbose_name=_('Separador entre Variação 3 e Variação 4'))
    rotulo_separador_variacao45 = models.CharField(
        blank=False,
        max_length=1,
        default="-",
        verbose_name=_('Separador entre Variação 4 e Variação 5'))
    rotulo_sufixo_texto = models.CharField(
        blank=True,
        max_length=30,
        verbose_name=_('Sufixo de Edição do rótulo'))
    rotulo_sufixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Sufixo html do rótulo'))
    texto_prefixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Prefixo html do texto'))
    texto_sufixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Sufixo html do texto'))
    nota_automatica_prefixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Prefixo html da nota automática'))
    nota_automatica_sufixo_html = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_('Sufixo html da nota automática'))
    contagem_continua = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Contagem contínua'))
    dispositivo_de_articulacao = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=False,
        verbose_name=_('Dispositivo de Articulação (Sem Texto)'))
    formato_variacao0 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Numeração'))
    formato_variacao1 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 1'))
    formato_variacao2 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 2'))
    formato_variacao3 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 3'))
    formato_variacao4 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 4'))
    formato_variacao5 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO_CHOICES,
        default=FNC1,
        verbose_name=_('Formato da Variação 5'))

    relacoes_diretas_pai_filho = models.ManyToManyField(
        'self',
        through='TipoDispositivoRelationship',
        through_fields=('pai', 'filho_permitido'),
        symmetrical=False,
        related_name='+')

    quantidade_permitida = models.IntegerField(
        default=-1,
        verbose_name=_('Quantidade permitida dentro de uma Norma'))

    class Meta:
        verbose_name = _('Tipo de Dispositivo')
        verbose_name_plural = _('Tipos de Dispositivo')
        ordering = ['id']

    def __str__(self):
        return self.nome

    def permitido_inserir_in(self, base, excluir_autos=False):
        pp = self.possiveis_pais.filter(pai=base)
        if pp.exists():
            if excluir_autos:
                if pp[0].filho_de_insercao_automatica:
                    return False
            return True
        return False


class TipoDispositivoRelationship(BaseModel):
    pai = models.ForeignKey(TipoDispositivo, related_name='filhos_permitidos')
    filho_permitido = models.ForeignKey(
        TipoDispositivo,
        blank=True, null=True, default=None,
        related_name='possiveis_pais')
    filho_de_insercao_automatica = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES, verbose_name=_('Filho de Inserção Automática'))

    class Meta:
        verbose_name = _('Relação Direta Permitida')
        verbose_name_plural = _('Relaçõe Diretas Permitidas')
        ordering = ['pai', 'filho_permitido']
        unique_together = (
            ('pai', 'filho_permitido',),)

    def __str__(self):
        return '%s - %s' % (
            self.pai.nome,
            self.filho_permitido.nome if self.filho_permitido else '')


class TipoPublicacao(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Tipo de Publicação')
        verbose_name_plural = _('Tipos de Publicação')

    def __str__(self):
        return self.sigla + ' - ' + self.nome


class VeiculoPublicacao(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Veículo de Publicação')
        verbose_name_plural = _('Veículos de Publicação')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


class Publicacao(models.Model):
    norma = models.ForeignKey(
        NormaJuridica, verbose_name=_('Norma Jurídica'))
    veiculo_publicacao = models.ForeignKey(
        VeiculoPublicacao, verbose_name=_('Veículo de Publicação'))
    tipo_publicacao = models.ForeignKey(
        TipoPublicacao, verbose_name=_('Tipo de Publicação'))
    publicacao = models.DateTimeField(verbose_name=_('Data de Publicação'))
    pagina_inicio = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Início'))
    pagina_fim = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Fim'))
    timestamp = models.DateTimeField()

    class Meta:
        verbose_name = _('Publicação')
        verbose_name_plural = _('Publicações')

    def __str__(self):
        return '%s: %s' % (self.veiculo_publicacao, self.publicacao)


class Dispositivo(BaseModel):
    TEXTO_PADRAO_DISPOSITIVO_REVOGADO = _('(Revogado)')
    INTERVALO_ORDEM = 1000
    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordem de Renderização'))
    ordem_bloco_atualizador = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordem de Renderização no Bloco Atualizador'))

    # apenas articulacao recebe nivel zero
    nivel = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Nível Estrutural'))

    dispositivo0 = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Número do Dispositivo'))
    dispositivo1 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Primeiro Nível de Variação'))
    dispositivo2 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Segundo Nível de Variação'))
    dispositivo3 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Terceiro Nível de Variação'))
    dispositivo4 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Quarto Nível de Variação'))
    dispositivo5 = models.PositiveIntegerField(
        default=0,
        blank=True,
        null=True,
        verbose_name=_('Quinto Nível de Variação'))

    rotulo = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_('Rótulo'))
    texto = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Texto'))
    texto_atualizador = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Texto no Dispositivo Atualizador'))

    inicio_vigencia = models.DateField(
        verbose_name=_('Início de Vigência'))
    fim_vigencia = models.DateField(
        blank=True, null=True, verbose_name=_('Fim de Vigência'))

    inicio_eficacia = models.DateField(
        verbose_name=_('Início de Eficácia'))
    fim_eficacia = models.DateField(
        blank=True, null=True, verbose_name=_('Fim de Eficácia'))

    inconstitucionalidade = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Inconstitucionalidade'))
    # Relevant attribute only in altering norms
    visibilidade = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Visibilidade na Norma Publicada'))

    timestamp = models.DateTimeField()

    tipo_dispositivo = models.ForeignKey(
        TipoDispositivo,
        related_name='dispositivos_do_tipo_set',
        verbose_name=_('Tipo do Dispositivo'))

    publicacao = models.ForeignKey(
        Publicacao,
        blank=True, null=True, default=None, verbose_name=_('Publicação'))

    norma = models.ForeignKey(
        NormaJuridica,
        related_name='dispositivos_set',
        verbose_name=_('Norma Jurídica'))
    norma_publicada = models.ForeignKey(
        NormaJuridica,
        blank=True, null=True, default=None,
        related_name='dispositivos_alterados_pela_norma_set',
        verbose_name=_('Norma Jurídica Publicada'))

    dispositivo_subsequente = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='+',
        verbose_name=_('Dispositivo Subsequente'))
    dispositivo_substituido = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='+',
        verbose_name=_('Dispositivo Substituido'))
    dispositivo_pai = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivos_filhos_set',
        verbose_name=_('Dispositivo Pai'))
    dispositivo_vigencia = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='+',
        verbose_name=_('Dispositivo de Vigência'))
    dispositivo_atualizador = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivos_alterados_set',
        verbose_name=_('Dispositivo Atualizador'))

    class Meta:
        verbose_name = _('Dispositivo')
        verbose_name_plural = _('Dispositivos')
        ordering = ['norma', 'ordem']
        unique_together = (
            ('norma', 'ordem',),
            ('norma',
             'dispositivo0',
             'dispositivo1',
             'dispositivo2',
             'dispositivo3',
             'dispositivo4',
             'dispositivo5',
             'tipo_dispositivo',
             'dispositivo_pai',
             'norma_publicada',
             'publicacao',),
        )

    def __str__(self):
        return '%(rotulo)s - %(norma)s' % {
            'rotulo': (self.rotulo if self.rotulo else self.tipo_dispositivo),
            'norma': self.norma}

    def rotulo_padrao(self, local_insert=0, for_insert_in=0):
        """
        0 = Sem inserção - com nomeclatura padrao
        1 = Inserção com transformação de parágrafo único para §1º """

        r = ''
        t = self.tipo_dispositivo
        prefixo = t.rotulo_prefixo_texto.split(';')

        if len(prefixo) > 1:

            if for_insert_in:
                irmaos_mesmo_tipo = Dispositivo.objects.filter(
                    tipo_dispositivo=self.tipo_dispositivo,
                    dispositivo_pai=self)
            else:
                irmaos_mesmo_tipo = Dispositivo.objects.filter(
                    tipo_dispositivo=self.tipo_dispositivo,
                    dispositivo_pai=self.dispositivo_pai)

            if not irmaos_mesmo_tipo.exists():
                r += prefixo[1]
            else:
                if self.dispositivo0 == 0:
                    if for_insert_in:
                        if irmaos_mesmo_tipo.count() == 0:
                            r += prefixo[0]
                            r += self.get_nomenclatura_completa()
                        elif irmaos_mesmo_tipo.count() == 1:
                            self.transform_in_next()
                            self.transform_in_next()
                            r += 'Transformar %s em %s%s e criar %s1%s' % (
                                prefixo[1].strip(),
                                prefixo[0],
                                self.get_nomenclatura_completa(),
                                prefixo[0],
                                'º' if
                                self.tipo_dispositivo.rotulo_ordinal >= 0
                                else '',)
                        else:
                            self.dispositivo0 = 1
                            r += prefixo[0]
                            r += self.get_nomenclatura_completa()

                    else:
                        if local_insert:
                            r += prefixo[1].strip()
                            r += self.get_nomenclatura_completa()
                        else:
                            self.dispositivo0 = 1
                            r += prefixo[0]
                            r += self.get_nomenclatura_completa()
                else:
                    if local_insert == 1 and irmaos_mesmo_tipo.count() == 1:

                        if Dispositivo.objects.filter(
                                ordem__gt=self.ordem,
                                ordem__lt=irmaos_mesmo_tipo[0].ordem).exists():
                            self.dispositivo0 = 2
                            r += 'Transformar %s em %s%s e criar %s1%s' % (
                                prefixo[1].strip(),
                                prefixo[0],
                                self.get_nomenclatura_completa(),
                                prefixo[0],
                                'º' if
                                self.tipo_dispositivo.rotulo_ordinal >= 0
                                else '',)
                        else:
                            r += 'Transformar %s em %s%s e criar %s 2%s' % (
                                prefixo[1].strip(),
                                prefixo[0],
                                self.get_nomenclatura_completa(),
                                prefixo[0],
                                'º' if
                                self.tipo_dispositivo.
                                rotulo_ordinal >= 0 else '',)
                    else:
                        r += prefixo[0]
                        r += self.get_nomenclatura_completa()
        else:
            r += prefixo[0]
            r += self.get_nomenclatura_completa()

        r += t.rotulo_sufixo_texto

        return r

    def get_profundidade(self):
        numero = self.get_numero_completo()
        for i in range(len(numero)):
            if numero[i] != 0 or i == 0:
                continue
            return i - 1
        return i

    def transform_in_next(self, direcao_variacao=0):
        """
        direcao_variacao é lida da seguinte forma:
            -1 = reduza 1 variacao e incremente 1
            1  = aumente 1 variacao e incremente 1
            -2 = reduza 2 variacoes e incremente 1
            2 = aumente 2 variacoes e incremente 1

        """
        numero = self.get_numero_completo()

        flag_variacao = 0
        flag_direcao = False

        if direcao_variacao <= 0:
            numero.reverse()
            for i in range(len(numero)):
                if not flag_direcao and numero[i] == 0 and i < len(numero) - 1:
                    continue

                if direcao_variacao < 0:
                    numero[i] = 0
                    direcao_variacao += 1
                    flag_variacao -= 1

                    if i == len(numero) - 1:
                        flag_direcao = False
                    else:
                        flag_direcao = True
                    continue
                break
            numero[i] += 1
            numero.reverse()

        elif direcao_variacao > 0:
            for i in range(len(numero)):
                if numero[i] != 0 or i == 0:
                    continue

                if direcao_variacao > 0:
                    numero[i] = 1
                    direcao_variacao -= 1
                    flag_variacao += 1

                    flag_direcao = True
                    if direcao_variacao == 0:
                        break
                    continue
            if not flag_direcao:
                flag_direcao = True
                numero[i] += 1

        self.set_numero_completo(numero)

        return (flag_direcao, flag_variacao)

    def set_numero_completo(self, *numero):
        numero = numero[0]
        self.dispositivo0 = numero[0]
        self.dispositivo1 = numero[1]
        self.dispositivo2 = numero[2]
        self.dispositivo3 = numero[3]
        self.dispositivo4 = numero[4]
        self.dispositivo5 = numero[5]

    def get_numero_completo(self):
        return [
            self.dispositivo0,
            self.dispositivo1,
            self.dispositivo2,
            self.dispositivo3,
            self.dispositivo4,
            self.dispositivo5]

    def get_nomenclatura_completa(self):

        numero = self.get_numero_completo()

        formato = [
            self.tipo_dispositivo.formato_variacao0,
            self.tipo_dispositivo.formato_variacao1,
            self.tipo_dispositivo.formato_variacao2,
            self.tipo_dispositivo.formato_variacao3,
            self.tipo_dispositivo.formato_variacao4,
            self.tipo_dispositivo.formato_variacao5]

        separadores = [
            '',
            self.tipo_dispositivo.rotulo_separador_variacao01,
            self.tipo_dispositivo.rotulo_separador_variacao12,
            self.tipo_dispositivo.rotulo_separador_variacao23,
            self.tipo_dispositivo.rotulo_separador_variacao34,
            self.tipo_dispositivo.rotulo_separador_variacao45]

        numero.reverse()
        formato.reverse()
        separadores.reverse()

        result = ''

        flag_obrigatorio = False
        for i in range(len(numero)):
            if not flag_obrigatorio and numero[i] == 0:
                continue
            flag_obrigatorio = True

            if i + 1 == len(numero) and numero[i] == 0:
                continue

            if i + 1 == len(numero) and \
                (self.tipo_dispositivo.rotulo_ordinal == -1 or
                 0 < numero[i] <= self.tipo_dispositivo.rotulo_ordinal):
                result = 'º' + result

            if formato[i] == TipoDispositivo.FNC1:
                result = separadores[i] + str(numero[i]) + result
            elif formato[i] == TipoDispositivo.FNCI:
                result = separadores[i] + \
                    utils.int_to_roman(numero[i]) + result
            elif formato[i] == TipoDispositivo.FNCi:
                result = separadores[i] + \
                    utils.int_to_roman(numero[i]).lower() + result
            elif formato[i] == TipoDispositivo.FNCA:
                result = separadores[i] + \
                    utils.int_to_letter(numero[i]) + result
            elif formato[i] == TipoDispositivo.FNCa:
                result = separadores[i] + \
                    utils.int_to_letter(numero[i]).lower() + result
            elif formato[i] == TipoDispositivo.FNC8:
                result = separadores[i] + '*' + result
            elif formato[i] == TipoDispositivo.FNCN:
                result = separadores[i] + result

        return result

    def criar_espaco(self, espaco_a_criar, local):

        if local == 'add_next':
            proximo_bloco = Dispositivo.objects.filter(
                ordem__gt=self.ordem,
                nivel__lte=self.nivel,
                norma_id=self.norma_id)[:1]
        elif local == 'add_in':
            proximo_bloco = Dispositivo.objects.filter(
                ordem__gt=self.ordem,
                nivel__lte=self.nivel + 1,
                norma_id=self.norma_id).exclude(
                    tipo_dispositivo__class_css='caput')[:1]
        else:
            proximo_bloco = Dispositivo.objects.filter(
                ordem__gte=self.ordem,
                norma_id=self.norma_id)[:1]

        if proximo_bloco.exists():
            ordem = proximo_bloco[0].ordem
            proximo_bloco = Dispositivo.objects.order_by('-ordem').filter(
                ordem__gte=ordem,
                norma_id=self.norma_id)

            proximo_bloco.update(ordem=F('ordem') + 1)
            proximo_bloco.update(
                ordem=F('ordem') + (
                    Dispositivo.INTERVALO_ORDEM * espaco_a_criar - 1))
        else:
            # inserção no fim da norma
            ordem_max = Dispositivo.objects.order_by(
                'ordem').filter(norma_id=self.norma_id).aggregate(
                Max('ordem'))
            if ordem_max['ordem__max'] is None:
                raise Exception(
                    'Não existem registros base nesta Norma')
            ordem = ordem_max['ordem__max'] + Dispositivo.INTERVALO_ORDEM
        return ordem

    def organizar_niveis(self):
        if self.dispositivo_pai is None:
            self.nivel = 0
        else:
            self.nivel = self.dispositivo_pai.nivel + 1

        filhos = Dispositivo.objects.filter(
            dispositivo_pai_id=self.pk)

        for filho in filhos:
            filho.nivel = self.nivel + 1
            filho.save()
            filho.organizar_niveis()

    def get_parents(self, ordem='desc'):
        dp = self
        p = []
        while dp.dispositivo_pai is not None:
            dp = dp.dispositivo_pai
            if ordem == 'desc':
                p.append(dp)
            else:
                p.insert(0, dp)

        return p

    def get_parents_asc(self):
        return self.get_parents(ordem='asc')

    def incrementar_irmaos(self, variacao=0, tipoadd=[]):

        if not self.tipo_dispositivo.contagem_continua:
            irmaos = list(Dispositivo.objects.filter(
                Q(ordem__gt=self.ordem) | Q(dispositivo0=0),
                dispositivo_pai_id=self.dispositivo_pai_id,
                tipo_dispositivo_id=self.tipo_dispositivo.pk))

        elif self.dispositivo_pai is None:
            irmaos = list(Dispositivo.objects.filter(
                ordem__gt=self.ordem,
                norma_id=self.norma_id,
                tipo_dispositivo_id=self.tipo_dispositivo.pk))

        else:  # contagem continua restrita a articulacao
            proxima_articulacao = self.get_proxima_articulacao()

            if proxima_articulacao is None:
                irmaos = list(Dispositivo.objects.filter(
                    ordem__gt=self.ordem,
                    norma_id=self.norma_id,
                    tipo_dispositivo_id=self.tipo_dispositivo.pk))
            else:
                irmaos = list(Dispositivo.objects.filter(
                    Q(ordem__gt=self.ordem) &
                    Q(ordem__lt=proxima_articulacao.ordem),
                    norma_id=self.norma_id,
                    tipo_dispositivo_id=self.tipo_dispositivo.pk))

        dp_profundidade = self.get_profundidade()

        irmaos_a_salvar = []
        ultimo_irmao = None
        for irmao in irmaos:

            if irmao.ordem <= self.ordem or irmao.dispositivo0 == 0:
                irmaos_a_salvar.append(irmao)
                continue

            irmao_profundidade = irmao.get_profundidade()
            if irmao_profundidade < dp_profundidade:
                break

            if irmao.get_numero_completo() < self.get_numero_completo():
                if irmao_profundidade > dp_profundidade:
                    if ultimo_irmao is None:
                        irmao.transform_in_next(
                            dp_profundidade - irmao_profundidade)
                        irmao.transform_in_next(
                            irmao_profundidade - dp_profundidade)
                    else:
                        irmao.set_numero_completo(
                            ultimo_irmao.get_numero_completo())

                        irmao.transform_in_next(
                            irmao_profundidade -
                            ultimo_irmao.get_profundidade())

                    ultimo_irmao = irmao
                else:
                    irmao.transform_in_next()
                irmao.rotulo = irmao.rotulo_padrao()
                irmaos_a_salvar.append(irmao)

            elif irmao.get_numero_completo() == self.get_numero_completo():
                irmao_numero = irmao.get_numero_completo()
                irmao_numero[dp_profundidade] += 1
                irmao.set_numero_completo(irmao_numero)
                irmao.rotulo = irmao.rotulo_padrao()
                irmaos_a_salvar.append(irmao)
            else:
                if dp_profundidade < irmao_profundidade and \
                        dp_profundidade > 0 and \
                        self.get_numero_completo()[:dp_profundidade] >= \
                        irmao.get_numero_completo()[:dp_profundidade] and\
                        ultimo_irmao is None:
                    break
                else:
                    ultimo_irmao = irmao
                    irmao_numero = irmao.get_numero_completo()
                    irmao_numero[dp_profundidade] += 1
                    irmao.set_numero_completo(irmao_numero)
                    irmao.rotulo = irmao.rotulo_padrao()
                    irmaos_a_salvar.append(irmao)

        irmaos_a_salvar.reverse()
        for irmao in irmaos_a_salvar:
            if (irmao.dispositivo0 == 0 and
                    irmao.ordem <= self.ordem) and variacao == 0:
                irmao.dispositivo0 = 1
                irmao.rotulo = irmao.rotulo_padrao()
                self.dispositivo0 = 2
                self.rotulo = self.rotulo_padrao()
            elif (irmao.dispositivo0 == 0 and
                    irmao.ordem > self.ordem) and variacao == 0:
                irmao.dispositivo0 = 2
                irmao.rotulo = irmao.rotulo_padrao()
                self.dispositivo0 = 1
                self.rotulo = self.rotulo_padrao()

            irmao.clean()
            irmao.save()

    def get_proxima_articulacao(self):
        proxima_articulacao = Dispositivo.objects.filter(
            ordem__gt=self.ordem,
            nivel=0,
            norma_id=self.norma_id)[:1]

        if not proxima_articulacao.exists():
            return None

        return proxima_articulacao[0]

    def is_relative_auto_insert(self):
        if self.dispositivo_pai is not None:
            # pp possiveis_pais
            pp = self.tipo_dispositivo.possiveis_pais.filter(
                pai=self.dispositivo_pai.tipo_dispositivo)

            if pp.exists():
                if pp[0].filho_de_insercao_automatica:
                    return True
        return False

    def get_raiz(self):
        dp = self
        while dp.dispositivo_pai is not None:
            dp = dp.dispositivo_pai
        return dp

    @staticmethod
    def new_instance_based_on(dispositivo_base, tipo_base):
        dp = Dispositivo()

        dp.tipo_dispositivo = tipo_base

        dp.set_numero_completo(
            dispositivo_base.get_numero_completo())
        dp.nivel = dispositivo_base.nivel
        dp.texto = ''
        dp.norma = dispositivo_base.norma
        dp.dispositivo_pai = dispositivo_base.dispositivo_pai
        dp.inicio_eficacia = dispositivo_base.inicio_eficacia
        dp.inicio_vigencia = dispositivo_base.inicio_vigencia
        dp.publicacao = dispositivo_base.publicacao
        dp.timestamp = datetime.now()
        dp.ordem = dispositivo_base.ordem

        return dp

    @staticmethod
    def set_numero_for_add_in(dispositivo_base, dispositivo, tipo_base):

        if tipo_base.contagem_continua:
            raiz = dispositivo_base.get_raiz()

            disps = Dispositivo.objects.order_by('-ordem').filter(
                tipo_dispositivo_id=tipo_base.pk,
                ordem__lte=dispositivo_base.ordem,
                ordem__gt=raiz.ordem,
                norma_id=dispositivo_base.norma_id)[:1]

            if disps.exists():
                dispositivo.set_numero_completo(
                    disps[0].get_numero_completo())
                dispositivo.transform_in_next()
            else:
                dispositivo.set_numero_completo([1, 0, 0, 0, 0, 0, ])
        else:
            if ';' in tipo_base.rotulo_prefixo_texto:

                if dispositivo != dispositivo_base:
                    irmaos_mesmo_tipo = Dispositivo.objects.filter(
                        tipo_dispositivo=tipo_base,
                        dispositivo_pai=dispositivo_base)

                    dispositivo.set_numero_completo([
                        1 if irmaos_mesmo_tipo.exists() else 0,
                        0, 0, 0, 0, 0, ])
                else:
                    dispositivo.set_numero_completo([0, 0, 0, 0, 0, 0, ])

            else:
                dispositivo.set_numero_completo([1, 0, 0, 0, 0, 0, ])


class Vide(models.Model):
    data_criacao = models.DateTimeField(verbose_name=_('Data de Criação'))
    texto = models.TextField(verbose_name=_('Texto do Vide'))

    tipo = models.ForeignKey(TipoVide, verbose_name=_('Tipo do Vide'))

    dispositivo_base = models.ForeignKey(
        Dispositivo,
        verbose_name=_('Dispositivo Base'),
        related_name='%(class)s_dispositivo_base')
    dispositivo_ref = models.ForeignKey(
        Dispositivo,
        related_name='%(class)s_dispositivo_ref',
        verbose_name=_('Dispositivo Referido'))

    class Meta:
        verbose_name = _('Vide')
        verbose_name_plural = _('Vides')

    def __str__(self):
        return _('Vide %s') % self.texto


class Nota(models.Model):
    NPRIV = 1
    NSTRL = 2
    NINST = 3
    NPUBL = 4
    PUBLICIDADE_CHOICES = (
        # Only the owner of the note has visibility.
        (NPRIV, _('Nota Privada')),
        # All of the same group have visibility.
        (NSTRL, _('Nota Setorial')),
        # All authenticated users have visibility.
        (NINST, _('Nota Institucional')),
        # All users have visibility.
        (NPUBL, _('Nota Pública')),
    )

    texto = models.TextField(verbose_name=_('Texto da Nota'))
    url_externa = models.CharField(
        max_length=1024,
        blank=True,
        verbose_name=_('Url externa'))

    data_criacao = models.DateTimeField(verbose_name=_('Data de Criação'))
    publicacao = models.DateTimeField(verbose_name=_('Data de Publicação'))
    efetifidade = models.DateTimeField(verbose_name=_('Data de Efeito'))

    tipo = models.ForeignKey(TipoNota, verbose_name=_('Tipo da Nota'))
    dispositivo = models.ForeignKey(
        Dispositivo,
        verbose_name=_('Dispositivo da Nota'))

    owner = models.ForeignKey(User, verbose_name=_('Dono da Nota'))
    publicidade = models.PositiveSmallIntegerField(
        choices=PUBLICIDADE_CHOICES,
        verbose_name=_('Nível de Publicidade'))

    class Meta:
        verbose_name = _('Nota')
        verbose_name_plural = _('Notas')

    def __str__(self):
        return '%s: %s' % (
            self.tipo,
            self.PUBLICIDADE_CHOICES[self.publicidade][1]
        )
