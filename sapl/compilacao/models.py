from datetime import datetime

from django.contrib import messages
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, Q
from django.db.models.aggregates import Max
from django.db.models.deletion import PROTECT
from django.http.response import Http404
from django.template import defaultfilters
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _
import reversion

from sapl.compilacao.utils import (get_integrations_view_names, int_to_letter,
                                   int_to_roman)
from sapl.utils import YES_NO_CHOICES, get_settings_auth_user_model


@reversion.register()
class TimestampedMixin(models.Model):
    created = models.DateTimeField(
        verbose_name=_('created'),
        editable=False, blank=True, auto_now_add=True)
    modified = models.DateTimeField(
        verbose_name=_('modified'), editable=False, blank=True, auto_now=True)

    class Meta:
        abstract = True


@reversion.register()
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

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, clean=True):
        if clean:
            self.clean()
        return models.Model.save(
            self,
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields)


@reversion.register()
class PerfilEstruturalTextoArticulado(BaseModel):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    padrao = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES, verbose_name=_('Padrão'))

    parent = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='perfil_parent_set',
        on_delete=PROTECT,
        verbose_name=_('Perfil Herdado'))

    class Meta:
        verbose_name = _('Perfil Estrutural de Texto Articulado')
        verbose_name_plural = _('Perfis Estruturais de Textos Articulados')

        ordering = ['-padrao', 'sigla']

    def __str__(self):
        return self.nome


@reversion.register()
class TipoTextoArticulado(models.Model):
    sigla = models.CharField(max_length=3, verbose_name=_('Sigla'))
    descricao = models.CharField(max_length=50, verbose_name=_('Descrição'))
    content_type = models.OneToOneField(
        ContentType,
        null=True, default=None,
        verbose_name=_('Modelo Integrado'))
    participacao_social = models.NullBooleanField(
        default=False,
        blank=True, null=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Participação Social'))

    publicacao_func = models.NullBooleanField(
        default=False,
        blank=True, null=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Histórico de Publicação'))

    perfis = models.ManyToManyField(
        PerfilEstruturalTextoArticulado,
        blank=True, verbose_name=_('Perfis Estruturais de Textos Articulados'),
        help_text=_("""
                    Apenas os perfis selecionados aqui estarão disponíveis
                    para o editor de Textos Articulados cujo Tipo seja este
                    em edição.
                    """))

    class Meta:
        verbose_name = _('Tipo de Texto Articulado')
        verbose_name_plural = _('Tipos de Texto Articulados')

    def __str__(self):
        return self.descricao


PARTICIPACAO_SOCIAL_CHOICES = [
    (None, _('Padrão definido no Tipo')),
    (True, _('Sim')),
    (False, _('Não'))]


STATUS_TA_PRIVATE = 99  # Só os donos podem ver
STATUS_TA_EDITION = 89
STATUS_TA_IMMUTABLE_RESTRICT = 79

STATUS_TA_IMMUTABLE_PUBLIC = 69

STATUS_TA_PUBLIC = 0

PRIVACIDADE_STATUS = (
    (STATUS_TA_PRIVATE, _('Privado')),  # só dono ve e edita
    # só quem tem permissão para ver
    (STATUS_TA_IMMUTABLE_RESTRICT, _('Imotável Restrito')),
    # só quem tem permissão para ver
    (STATUS_TA_IMMUTABLE_PUBLIC, _('Imutável Público')),
    (STATUS_TA_EDITION, _('Em Edição')),  # só quem tem permissão para editar
    (STATUS_TA_PUBLIC, _('Público')),  # visualização pública
)


@reversion.register()
class TextoArticulado(TimestampedMixin):
    data = models.DateField(blank=True, null=True, verbose_name=_('Data'))
    ementa = models.TextField(verbose_name=_('Ementa'))
    observacao = models.TextField(blank=True, verbose_name=_('Observação'))
    numero = models.PositiveIntegerField(verbose_name=_('Número'))
    ano = models.PositiveSmallIntegerField(verbose_name=_('Ano'))
    tipo_ta = models.ForeignKey(
        TipoTextoArticulado,
        blank=True, null=True, default=None,
        verbose_name=_('Tipo de Texto Articulado'))
    participacao_social = models.NullBooleanField(
        default=None,
        blank=True, null=True,
        choices=PARTICIPACAO_SOCIAL_CHOICES,
        verbose_name=_('Participação Social'))

    content_type = models.ForeignKey(
        ContentType,
        blank=True, null=True, default=None)
    object_id = models.PositiveIntegerField(
        blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    owners = models.ManyToManyField(
        get_settings_auth_user_model(),
        blank=True, verbose_name=_('Donos do Texto Articulado'))

    editable_only_by_owners = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=True,
        verbose_name=_('Editável apenas pelos donos do Texto Articulado'))

    editing_locked = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=True,
        verbose_name=_('Texto Articulado em Edição'))

    privacidade = models.IntegerField(
        _('Privacidade'),
        choices=PRIVACIDADE_STATUS,
        default=STATUS_TA_PRIVATE)

    class Meta:
        verbose_name = _('Texto Articulado')
        verbose_name_plural = _('Textos Articulados')
        ordering = ['-data', '-numero']
        permissions = (
            ('view_restricted_textoarticulado',
             _('Pode ver qualquer Texto Articulado')),
            ('lock_unlock_textoarticulado',
             _('Pode bloquear/desbloquear edição de Texto Articulado')),
        )

    def __str__(self):
        if self.content_object:
            return str(self.content_object)
        else:
            return _('%(tipo)s nº %(numero)s de %(data)s') % {
                'tipo': self.tipo_ta,
                'numero': self.numero,
                'data': defaultfilters.date(self.data, "d \d\e F \d\e Y")}

    def hash(self):
        from django.core import serializers
        import hashlib
        data = serializers.serialize(
            "xml", Dispositivo.objects.filter(
                Q(ta_id=self.id) | Q(ta_publicado_id=self.id)))
        md5 = hashlib.md5()
        md5.update(data.encode('utf-8'))
        return md5.hexdigest()

    def can_use_dynamic_editing(self, user):
        return not self.editing_locked and\
            (not self.editable_only_by_owners and
             user.has_perm(
                 'compilacao.change_dispositivo_edicao_dinamica') or
             self.editable_only_by_owners and user in self.owners.all() and
             user.has_perm(
                 'compilacao.change_your_dispositivo_edicao_dinamica'))

    def has_view_permission(self, request):
        if self.privacidade in (STATUS_TA_IMMUTABLE_PUBLIC, STATUS_TA_PUBLIC):
            return True

        if request.user in self.owners.all():
            return True

        if self.privacidade == STATUS_TA_IMMUTABLE_RESTRICT and\
                request.user.has_perm(
                    'compilacao.view_restricted_textoarticulado'):
            return True

        elif self.privacidade == STATUS_TA_EDITION:
            if request.user.has_perm(
                    'compilacao.change_dispositivo_edicao_dinamica'):
                return True
            else:
                messages.error(request, _(
                    'Este Texto Articulado está em edição.'))

        elif self.privacidade == STATUS_TA_PRIVATE:
            if request.user in self.owners.all():
                return True
            else:
                raise Http404()

        return False

    def has_edit_permission(self, request):

        if self.privacidade == STATUS_TA_PRIVATE:
            if request.user not in self.owners.all():
                raise Http404()

            if not self.can_use_dynamic_editing(request.user):
                messages.error(request, _(
                    'Usuário sem permissão para edição.'))
                return False
            else:
                return True

        if self.privacidade == STATUS_TA_IMMUTABLE_RESTRICT:
            messages.error(request, _(
                'A edição deste Texto Articulado está bloqueada. '
                'Este documento é imutável e de acesso é restrito.'))
            return False

        if self.privacidade == STATUS_TA_IMMUTABLE_PUBLIC:
            messages.error(request, _(
                'A edição deste Texto Articulado está bloqueada. '
                'Este documento é imutável.'))
            return False

        if self.editing_locked and\
            self.privacidade in (STATUS_TA_PUBLIC, STATUS_TA_EDITION) and\
                not request.user.has_perm(
                    'compilacao.lock_unlock_textoarticulado'):
            messages.error(request, _(
                'A edição deste Texto Articulado está bloqueada. '
                'É necessário acessar com usuário que possui '
                'permissão de desbloqueio.'))
            return False

        if not request.user.has_perm(
                'compilacao.change_dispositivo_edicao_dinamica'):
            messages.error(request, _(
                'Usuário sem permissão para edição.'))
            return False

        if self.editable_only_by_owners and\
                request.user not in self.owners.all():
            messages.error(request, _(
                'Apenas usuários donos do Texto Articulado podem editá-lo.'))
            return False

        return True

    @classonlymethod
    def update_or_create(cls, view_integracao, obj):

        map_fields = view_integracao.map_fields
        ta_values = getattr(view_integracao, 'ta_values', {})

        related_object_type = ContentType.objects.get_for_model(obj)
        ta = TextoArticulado.objects.filter(
            object_id=obj.pk,
            content_type=related_object_type)

        ta_exists = bool(ta.exists())

        if not ta_exists:
            tipo_ta = TipoTextoArticulado.objects.filter(
                content_type=related_object_type).first()

            ta = TextoArticulado()
            ta.tipo_ta = tipo_ta
            ta.content_object = obj

            ta.privacidade = ta_values.get('privacidade', STATUS_TA_EDITION)
            ta.editing_locked = ta_values.get('editing_locked', False)
            ta.editable_only_by_owners = ta_values.get(
                'editable_only_by_owners', False)

        else:
            ta = ta[0]

        if not ta.data:
            ta.data = getattr(obj, map_fields['data']
                              if map_fields['data'] else 'xxx',
                              datetime.now())
            if not ta.data:
                ta.data = datetime.now()

        ta.ementa = getattr(
            obj, map_fields['ementa']
            if map_fields['ementa'] else 'xxx', _(
                'Integração com %s sem ementa.') % obj)

        ta.observacao = getattr(
            obj, map_fields['observacao']
            if map_fields['observacao'] else 'xxx', '')

        ta.numero = getattr(
            obj, map_fields['numero']
            if map_fields['numero'] else 'xxx', int('%s%s%s' % (
                int(datetime.now().year),
                int(datetime.now().month),
                int(datetime.now().day))))

        ta.ano = getattr(obj, map_fields['ano']
                         if map_fields['ano'] else 'xxx', datetime.now().year)

        ta.save()
        return ta

    def clone_for(self, obj):
        # O clone gera um texto válido original dada a base self,
        # mesmo sendo esta base um texto compilado.
        # Os dispositivos a clonar será com base no texto compilado

        assert self.tipo_ta and self.tipo_ta.content_type, _(
            'Não é permitido chamar o método clone_for '
            'para Textos Articulados independentes.')

        view_integracao = list(filter(lambda x:
                                      x.model == obj._meta.model,
                                      get_integrations_view_names()))

        assert len(view_integracao) > 0, _(
            'Não é permitido chamar o método clone_for '
            'se não existe integração.')

        assert len(view_integracao) == 1, _(
            'Não é permitido haver mais de uma integração para um Model.')

        view_integracao = view_integracao[0]

        ta = TextoArticulado.update_or_create(view_integracao, obj)

        dispositivos = Dispositivo.objects.filter(ta=self).order_by('ordem')

        map_ids = {}
        for d in dispositivos:
            id_old = d.id

            # TODO
            # validar isso: é o suficiente para pegar apenas o texto válido?
            # exemplo:
            #  quando uma matéria for alterada por uma emenda
            #  ao usar esta função para gerar uma norma deve vir apenas
            #  o texto válido, compilado...
            if d.dispositivo_subsequente:
                continue

            d.id = None
            d.inicio_vigencia = ta.data
            d.fim_vigencia = None
            d.inicio_eficacia = ta.data
            d.fim_eficacia = None
            d.publicacao = None
            d.ta = ta
            d.ta_publicado = None
            d.dispositivo_subsequente = None
            d.dispositivo_substituido = None
            d.dispositivo_vigencia = None
            d.dispositivo_atualizador = None
            d.save()
            map_ids[id_old] = d.id

        dispositivos = Dispositivo.objects.filter(ta=ta).order_by('ordem')

        for d in dispositivos:
            if not d.dispositivo_pai:
                continue

            d.dispositivo_pai_id = map_ids[d.dispositivo_pai_id]
            d.save()

        return ta

    def reagrupar_ordem_de_dispositivos(self):

        dpts = Dispositivo.objects.filter(ta=self)

        if not dpts.exists():
            return

        ordem_max = dpts.last().ordem
        dpts.update(ordem=F('ordem') + ordem_max)

        dpts = Dispositivo.objects.filter(
            ta=self).values_list('pk', flat=True).order_by('ordem')

        count = 0
        for d in dpts:
            count += Dispositivo.INTERVALO_ORDEM
            Dispositivo.objects.filter(pk=d).update(ordem=count)

    def reordenar_dispositivos(self):

        dpts = Dispositivo.objects.filter(ta=self)

        if not dpts.exists():
            return

        ordem_max = dpts.last().ordem
        dpts.update(ordem=F('ordem') + ordem_max)

        raizes = Dispositivo.objects.filter(
            ta=self,
            dispositivo_pai__isnull=True).values_list(
                'pk', flat=True).order_by('ordem')

        count = []
        count.append(Dispositivo.INTERVALO_ORDEM)

        def update(dpk):
            Dispositivo.objects.filter(pk=dpk).update(ordem=count[0])
            count[0] = count[0] + Dispositivo.INTERVALO_ORDEM
            filhos = Dispositivo.objects.filter(
                dispositivo_pai_id=dpk).values_list(
                'pk', flat=True).order_by('ordem')

            for dpk in filhos:
                update(dpk)

        for dpk in raizes:
            update(dpk)


@reversion.register()
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


@reversion.register()
class TipoVide(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Tipo de Vide')
        verbose_name_plural = _('Tipos de Vide')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


@reversion.register()
class TipoDispositivo(BaseModel):
    """
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
    rotulo_prefixo_html = models.TextField(
        blank=True,
        verbose_name=_('Prefixo html do rótulo'))
    rotulo_prefixo_texto = models.TextField(
        blank=True,
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
    rotulo_sufixo_texto = models.TextField(
        blank=True,
        verbose_name=_('Sufixo de Edição do rótulo'))
    rotulo_sufixo_html = models.TextField(
        blank=True,
        verbose_name=_('Sufixo html do rótulo'))
    texto_prefixo_html = models.TextField(
        blank=True,
        verbose_name=_('Prefixo html do texto'))
    texto_sufixo_html = models.TextField(
        blank=True,
        verbose_name=_('Sufixo html do texto'))
    nota_automatica_prefixo_html = models.TextField(
        blank=True,
        verbose_name=_('Prefixo html da nota automática'))
    nota_automatica_sufixo_html = models.TextField(
        blank=True,
        verbose_name=_('Sufixo html da nota automática'))
    contagem_continua = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Contagem contínua'))
    dispositivo_de_articulacao = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=False,
        verbose_name=_('Dispositivo de Articulação (Sem Texto)'))
    dispositivo_de_alteracao = models.BooleanField(
        choices=YES_NO_CHOICES,
        default=False,
        verbose_name=_('Dispositivo de Alteração'))
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
        related_name='relacaoes_pai_filho')

    class Meta:
        verbose_name = _('Tipo de Dispositivo')
        verbose_name_plural = _('Tipos de Dispositivo')
        ordering = ['id']

    def __str__(self):
        return self.nome

    def permitido_inserir_in(
            self, pai_relativo, include_relative_autos=True, perfil_pk=None):

        perfil = PerfilEstruturalTextoArticulado.objects.all()
        if not perfil_pk:
            perfil = perfil.filter(padrao=True)

        else:
            perfil = perfil.filter(pk=perfil_pk)

        if not perfil.exists():
            return False

        perfil = perfil[0]

        while perfil:
            pp = self.possiveis_pais.filter(pai=pai_relativo, perfil=perfil)
            if pp.exists():
                if not include_relative_autos:
                    if pp[0].filho_de_insercao_automatica:
                        return False
                return True
            perfil = perfil.parent
        return False

    def permitido_variacao(self, base, perfil_pk=None):

        perfil = PerfilEstruturalTextoArticulado.objects.all()
        if not perfil_pk:
            perfil = perfil.filter(padrao=True)

        else:
            perfil = perfil.filter(pk=perfil_pk)

        if not perfil.exists():
            return False

        perfil = perfil[0]

        while perfil:
            pp = self.possiveis_pais.filter(pai=base, perfil=perfil)
            if pp.exists():
                if pp[0].permitir_variacao:
                    return True
            perfil = perfil.parent
        return False


@reversion.register()
class TipoDispositivoRelationship(BaseModel):
    pai = models.ForeignKey(TipoDispositivo, related_name='filhos_permitidos')
    filho_permitido = models.ForeignKey(
        TipoDispositivo,
        related_name='possiveis_pais')
    perfil = models.ForeignKey(PerfilEstruturalTextoArticulado)
    filho_de_insercao_automatica = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Filho de Inserção Automática'))
    permitir_variacao = models.BooleanField(
        default=True,
        choices=YES_NO_CHOICES,
        verbose_name=_('Permitir Variação Numérica'))

    quantidade_permitida = models.IntegerField(
        default=-1,
        verbose_name=_('Quantidade permitida nesta relação'))

    class Meta:
        verbose_name = _('Relação Direta Permitida')
        verbose_name_plural = _('Relaçõe Diretas Permitidas')
        ordering = ['pai', 'filho_permitido']
        unique_together = (
            ('pai', 'filho_permitido', 'perfil'),)

    def __str__(self):
        return '%s - %s' % (
            self.pai.nome,
            self.filho_permitido.nome if self.filho_permitido else '')


@reversion.register()
class TipoPublicacao(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Tipo de Publicação')
        verbose_name_plural = _('Tipos de Publicação')

    def __str__(self):
        return self.nome


@reversion.register()
class VeiculoPublicacao(models.Model):
    sigla = models.CharField(
        max_length=10, unique=True, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=60, verbose_name=_('Nome'))

    class Meta:
        verbose_name = _('Veículo de Publicação')
        verbose_name_plural = _('Veículos de Publicação')

    def __str__(self):
        return '%s: %s' % (self.sigla, self.nome)


@reversion.register()
class Publicacao(TimestampedMixin):
    ta = models.ForeignKey(
        TextoArticulado, verbose_name=_('Texto Articulado'))
    veiculo_publicacao = models.ForeignKey(
        VeiculoPublicacao, verbose_name=_('Veículo de Publicação'))
    tipo_publicacao = models.ForeignKey(
        TipoPublicacao, verbose_name=_('Tipo de Publicação'))

    data = models.DateField(verbose_name=_('Data de Publicação'))
    hora = models.TimeField(
        blank=True, null=True, verbose_name=_('Horário de Publicação'))

    numero = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Número'))

    ano = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Ano'))

    edicao = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Edição'))

    url_externa = models.URLField(
        max_length=1024,
        blank=True,
        verbose_name=_('Link para Versão Eletrônica'))
    pagina_inicio = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Início'))
    pagina_fim = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_('Pg. Fim'))

    class Meta:
        verbose_name = _('Publicação')
        verbose_name_plural = _('Publicações')

    def __str__(self):
        return _('%s realizada em %s \n <small>%s</small>') % (
            self.tipo_publicacao,
            defaultfilters.date(self.data, "d \d\e F \d\e Y"),
            self.ta)


@reversion.register()
class Dispositivo(BaseModel, TimestampedMixin):
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
        verbose_name=_('Texto do Dispositivo'))
    texto_atualizador = models.TextField(
        blank=True,
        default='',
        verbose_name=_('Texto do Dispositivo no Dispositivo Atualizador'))

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
        verbose_name=_('Declarado Inconstitucional'))
    auto_inserido = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Auto Inserido'))
    visibilidade = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Visibilidade no Texto Articulado Publicado'))

    dispositivo_de_revogacao = models.BooleanField(
        default=False,
        choices=YES_NO_CHOICES,
        verbose_name=_('Dispositivo de Revogação'))

    tipo_dispositivo = models.ForeignKey(
        TipoDispositivo,
        on_delete=models.PROTECT,
        related_name='dispositivos_do_tipo_set',
        verbose_name=_('Tipo do Dispositivo'))

    publicacao = models.ForeignKey(
        Publicacao,
        blank=True, null=True, default=None, verbose_name=_('Publicação'))

    ta = models.ForeignKey(
        TextoArticulado,
        on_delete=models.CASCADE,
        related_name='dispositivos_set',
        verbose_name=_('Texto Articulado'))
    ta_publicado = models.ForeignKey(
        TextoArticulado,
        on_delete=models.PROTECT,
        blank=True, null=True, default=None,
        related_name='dispositivos_alterados_pelo_ta_set',
        verbose_name=_('Texto Articulado Publicado'))

    dispositivo_subsequente = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivo_subsequente_set',
        on_delete=models.SET_NULL,
        verbose_name=_('Dispositivo Subsequente'))
    dispositivo_substituido = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivo_substituido_set',
        on_delete=models.SET_NULL,
        verbose_name=_('Dispositivo Substituido'))
    dispositivo_pai = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivos_filhos_set',
        verbose_name=_('Dispositivo Pai'))
    dispositivo_vigencia = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        on_delete=models.SET_NULL,
        related_name='dispositivos_vigencias_set',
        verbose_name=_('Dispositivo de Vigência'))
    dispositivo_atualizador = models.ForeignKey(
        'self',
        blank=True, null=True, default=None,
        related_name='dispositivos_alterados_set',
        verbose_name=_('Dispositivo Atualizador'))

    class Meta:
        verbose_name = _('Dispositivo')
        verbose_name_plural = _('Dispositivos')
        ordering = ['ta', 'ordem']
        unique_together = (
            ('ta', 'ordem',),
            ('ta',
             'dispositivo0',
             'dispositivo1',
             'dispositivo2',
             'dispositivo3',
             'dispositivo4',
             'dispositivo5',
             'tipo_dispositivo',
             'dispositivo_pai',
             'dispositivo_atualizador',
             'ta_publicado',
             'publicacao',),
        )
        permissions = (
            ('change_dispositivo_edicao_dinamica', _(
                'Permissão de edição de dispositivos originais '
                'via editor dinâmico.')),
            ('change_your_dispositivo_edicao_dinamica', _(
                'Permissão de edição de dispositivos originais '
                'via editor dinâmico desde que seja dono.')),
            ('change_dispositivo_edicao_avancada', _(
                'Permissão de edição de dispositivos originais '
                'via formulários de edição avançada.')),
            ('change_dispositivo_registros_compilacao', _(
                'Permissão de registro de compilação via editor dinâmico.')),
            ('view_dispositivo_notificacoes', _(
                'Permissão de acesso às notificações de pendências.')),
            ('change_dispositivo_de_vigencia_global', _(
                'Permissão alteração global do dispositivo de vigência')),
        )

    def __str__(self):
        return '%(rotulo)s' % {
            'rotulo': (self.rotulo if self.rotulo else self.tipo_dispositivo)}

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
                            r += _('Transformar %s em %s%s e criar %s1%s') % (
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
                            r += _('Transformar %s em %s%s e criar %s1%s') % (
                                prefixo[1].strip(),
                                prefixo[0],
                                self.get_nomenclatura_completa(),
                                prefixo[0],
                                'º' if
                                self.tipo_dispositivo.rotulo_ordinal >= 0
                                else '',)
                        else:
                            r += _('Transformar %s em %s%s e criar %s 2%s') % (
                                prefixo[1].strip(),
                                prefixo[0],
                                self.get_nomenclatura_completa(),
                                prefixo[0],
                                'º' if
                                self.tipo_dispositivo.
                                rotulo_ordinal >= 0 else '',)
                    elif irmaos_mesmo_tipo.count() == 1 and\
                            irmaos_mesmo_tipo[0].dispositivo0 == 0 and\
                            self.dispositivo0 == 1:
                        irmao = irmaos_mesmo_tipo[0]
                        irmao.dispositivo0 = 1
                        rr = prefixo[0]
                        rr += irmao.get_nomenclatura_completa()
                        irmao.rotulo = rr + t.rotulo_sufixo_texto
                        irmao.save()
                        r += prefixo[0]

                        self.dispositivo0 = 2
                        r += self.get_nomenclatura_completa()

                    else:
                        r += prefixo[0]
                        r += self.get_nomenclatura_completa()
        else:
            if self.dispositivo0 == 0:
                self.dispositivo0 = 1
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

    def transform_in_prior(self, profundidade=-1):
        numero = self.get_numero_completo()

        numero.reverse()

        if profundidade != -1:
            profundidade = len(numero) - profundidade - 1

        for i in range(len(numero)):
            if not numero[i]:
                continue

            if i > profundidade:
                continue

            numero[i] -= 1
            break

        numero.reverse()
        self.set_numero_completo(numero)

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
                    int_to_roman(numero[i]) + result
            elif formato[i] == TipoDispositivo.FNCi:
                result = separadores[i] + \
                    int_to_roman(numero[i]).lower() + result
            elif formato[i] == TipoDispositivo.FNCA:
                result = separadores[i] + \
                    int_to_letter(numero[i]) + result
            elif formato[i] == TipoDispositivo.FNCa:
                result = separadores[i] + \
                    int_to_letter(numero[i]).lower() + result
            elif formato[i] == TipoDispositivo.FNC8:
                result = separadores[i] + '*' + result
            elif formato[i] == TipoDispositivo.FNCN:
                result = separadores[i] + result

        return result

    def criar_espaco(self, espaco_a_criar, local):

        if local == 'json_add_next':
            proximo_bloco = Dispositivo.objects.filter(
                ordem__gt=self.ordem,
                nivel__lte=self.nivel,
                ta_id=self.ta_id)[:1]
        elif local == 'json_add_in':
            # FIXME: o exclude não deve estar limitado a uma class_css caput e
            # sim a qualquer filho de inserção automática
            proximo_bloco = Dispositivo.objects.filter(
                ordem__gt=self.ordem,
                nivel__lte=self.nivel + 1,
                ta_id=self.ta_id).exclude(
                    tipo_dispositivo__class_css='caput')[:1]
        else:
            proximo_bloco = Dispositivo.objects.filter(
                ordem__gte=self.ordem,
                ta_id=self.ta_id)[:1]

        if proximo_bloco.exists():
            ordem = proximo_bloco[0].ordem
            proximo_bloco = Dispositivo.objects.order_by('-ordem').filter(
                ordem__gte=ordem,
                ta_id=self.ta_id)

            proximo_bloco.update(ordem=F('ordem') + 1)
            proximo_bloco.update(
                ordem=F('ordem') + (
                    Dispositivo.INTERVALO_ORDEM * espaco_a_criar - 1))
        else:
            # inserção no fim do ta
            ordem_max = Dispositivo.objects.order_by(
                'ordem').filter(
                ta_id=self.ta_id).aggregate(
                Max('ordem'))
            if ordem_max['ordem__max'] is None:
                raise Exception(
                    _('Não existem registros base neste Texto Articulado'))
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
        while dp.dispositivo_pai:
            dp = dp.dispositivo_pai
            if ordem == 'desc':
                p.append(dp)
            else:
                p.insert(0, dp)

        return p

    def get_parents_asc(self):
        return self.get_parents(ordem='asc')

    def incrementar_irmaos(self, variacao=0, tipoadd=[], force=True):

        if not self.tipo_dispositivo.contagem_continua:
            irmaos = list(Dispositivo.objects.filter(
                Q(ordem__gt=self.ordem) | Q(dispositivo0=0),
                dispositivo_pai_id=self.dispositivo_pai_id,
                tipo_dispositivo_id=self.tipo_dispositivo.pk))

        elif self.dispositivo_pai is None:
            irmaos = list(Dispositivo.objects.filter(
                ordem__gt=self.ordem,
                ta_id=self.ta_id,
                tipo_dispositivo_id=self.tipo_dispositivo.pk))

        else:  # contagem continua restrita a articulacao
            proxima_articulacao = self.get_proximo_nivel_zero()

            if proxima_articulacao is None:
                irmaos = list(Dispositivo.objects.filter(
                    ordem__gt=self.ordem,
                    ta_id=self.ta_id,
                    tipo_dispositivo_id=self.tipo_dispositivo.pk))
            else:
                irmaos = list(Dispositivo.objects.filter(
                    Q(ordem__gt=self.ordem) &
                    Q(ordem__lt=proxima_articulacao.ordem),
                    ta_id=self.ta_id,
                    tipo_dispositivo_id=self.tipo_dispositivo.pk))

        dp_profundidade = self.get_profundidade()

        if (not force and not variacao and len(irmaos) > 0 and
                irmaos[0].get_numero_completo() > self.get_numero_completo()):
            return

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

    def get_proximo_nivel_zero(self):
        proxima_articulacao = Dispositivo.objects.order_by('ordem').filter(
            ordem__gt=self.ordem,
            nivel=0,
            ta_id=self.ta_id).first()
        return proxima_articulacao

    def get_nivel_zero_anterior(self):
        anterior_articulacao = Dispositivo.objects.order_by('ordem').filter(
            ordem__lt=self.ordem,
            nivel=0,
            ta_id=self.ta_id).last()
        return anterior_articulacao

    def get_niveis_zero(self):
        niveis_zero = Dispositivo.objects.order_by('ordem').filter(
            nivel=0,
            ta_id=self.ta_id)
        return niveis_zero

    # metodo obsoleto, foi acrescentado o campo auto_inserido no modelo
    def is_relative_auto_insert__obsoleto(self, perfil_pk=None):
        if self.dispositivo_pai is not None:
            # pp possiveis_pais

            if not perfil_pk:
                perfis = PerfilEstruturalTextoArticulado.objects.filter(
                    padrao=True)[:1]
                if perfis.exists():
                    perfil_pk = perfis[0].pk

            pp = self.tipo_dispositivo.possiveis_pais.filter(
                pai=self.dispositivo_pai.tipo_dispositivo,
                perfil_id=perfil_pk)

            if pp.exists():
                if pp[0].filho_de_insercao_automatica:
                    return True
        return False

    def get_raiz(self):
        dp = self
        while dp.dispositivo_pai is not None:
            dp = dp.dispositivo_pai
        return dp

    def history(self):
        ultimo = self
        while ultimo.dispositivo_subsequente:
            ultimo = ultimo.dispositivo_subsequente

        yield ultimo
        while ultimo.dispositivo_substituido:
            ultimo = ultimo.dispositivo_substituido
            yield ultimo

    @staticmethod
    def new_instance_based_on(dispositivo_base, tipo_base):
        dp = Dispositivo()

        dp.tipo_dispositivo = tipo_base

        dp.set_numero_completo(
            dispositivo_base.get_numero_completo())
        dp.nivel = dispositivo_base.nivel
        dp.texto = ''
        dp.visibilidade = True
        # dp.auto_inserido = dispositivo_base.auto_inserido
        dp.ta = dispositivo_base.ta
        dp.dispositivo_pai = dispositivo_base.dispositivo_pai
        dp.publicacao = dispositivo_base.publicacao

        dp.dispositivo_vigencia = dispositivo_base.dispositivo_vigencia
        if dp.dispositivo_vigencia:
            dp.inicio_eficacia = dp.dispositivo_vigencia.inicio_eficacia
            dp.inicio_vigencia = dp.dispositivo_vigencia.inicio_vigencia
            dp.fim_eficacia = dp.dispositivo_vigencia.fim_eficacia
            dp.fim_vigencia = dp.dispositivo_vigencia.fim_vigencia
        else:
            dp.inicio_eficacia = dispositivo_base.inicio_eficacia
            dp.inicio_vigencia = dispositivo_base.inicio_vigencia
            dp.fim_eficacia = dispositivo_base.fim_eficacia
            dp.fim_vigencia = dispositivo_base.fim_vigencia

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
                ta_id=dispositivo_base.ta_id)[:1]

            if disps.exists():
                dispositivo.set_numero_completo(
                    disps[0].get_numero_completo())
                # dispositivo.transform_in_next()
            else:
                dispositivo.set_numero_completo([0, 0, 0, 0, 0, 0, ])
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

    def ordenar_bloco_alteracao(self):
        if not self.tipo_dispositivo.dispositivo_de_articulacao or\
           not self.tipo_dispositivo.dispositivo_de_alteracao:
            return

        filhos = Dispositivo.objects.order_by(
            'ordem_bloco_atualizador').filter(
            Q(dispositivo_pai_id=self.pk) |
            Q(dispositivo_atualizador_id=self.pk))

        if not filhos.exists():
            return

        ordem_max = filhos.last().ordem_bloco_atualizador
        filhos.update(
            ordem_bloco_atualizador=F('ordem_bloco_atualizador') + ordem_max)

        filhos = filhos.values_list(
            'pk', flat=True).order_by('ordem_bloco_atualizador')

        count = 0
        for d in filhos:
            count += Dispositivo.INTERVALO_ORDEM
            Dispositivo.objects.filter(pk=d).update(
                ordem_bloco_atualizador=count)


@reversion.register()
class Vide(TimestampedMixin):
    texto = models.TextField(verbose_name=_('Texto do Vide'))

    tipo = models.ForeignKey(TipoVide, verbose_name=_('Tipo do Vide'))

    dispositivo_base = models.ForeignKey(
        Dispositivo,
        verbose_name=_('Dispositivo Base'),
        related_name='dispositivo_base_set')
    dispositivo_ref = models.ForeignKey(
        Dispositivo,
        related_name='dispositivo_citado_set',
        verbose_name=_('Dispositivo Referido'))

    class Meta:
        verbose_name = _('Vide')
        verbose_name_plural = _('Vides')
        unique_together = ['dispositivo_base', 'dispositivo_ref', 'tipo']

    def __str__(self):
        return _('Vide %s') % self.texto


NPRIV = 1
NINST = 2
NPUBL = 3
NOTAS_PUBLICIDADE_CHOICES = (
    # Only the owner of the note has visibility.
    (NPRIV, _('Nota Privada')),
    # All authenticated users have visibility.
    (NINST, _('Nota Institucional')),
    # All users have visibility.
    (NPUBL, _('Nota Pública')),
)


@reversion.register()
class Nota(TimestampedMixin):

    NPRIV = 1
    NINST = 2
    NPUBL = 3

    titulo = models.CharField(
        verbose_name=_('Título'),
        max_length=100,
        default='',
        blank=True)
    texto = models.TextField(verbose_name=_('Texto'))
    url_externa = models.URLField(
        max_length=1024,
        blank=True,
        verbose_name=_('Url externa'))

    publicacao = models.DateTimeField(verbose_name=_('Data de Publicação'))
    efetividade = models.DateTimeField(verbose_name=_('Data de Efeito'))

    tipo = models.ForeignKey(TipoNota, verbose_name=_('Tipo da Nota'))
    dispositivo = models.ForeignKey(
        Dispositivo,
        verbose_name=_('Dispositivo da Nota'),
        related_name='dispositivo_nota_set')

    owner = models.ForeignKey(
        get_settings_auth_user_model(), verbose_name=_('Dono da Nota'))
    publicidade = models.PositiveSmallIntegerField(
        choices=NOTAS_PUBLICIDADE_CHOICES,
        verbose_name=_('Nível de Publicidade'))

    class Meta:
        verbose_name = _('Nota')
        verbose_name_plural = _('Notas')
        ordering = ['-publicacao', '-modified']

    def __str__(self):
        return '%s: %s' % (
            self.tipo,
            self.get_publicidade_display()
        )
