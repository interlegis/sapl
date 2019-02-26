
import logging
import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models import Q
from django.forms.fields import CharField, MultiValueField
from django.forms.widgets import MultiWidget, TextInput
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_lazy as _
from django_filters.filters import CharFilter, ModelChoiceFilter, DateFilter
from django_filters.rest_framework.backends import DjangoFilterBackend
from django_filters.rest_framework.filterset import FilterSet
from rest_framework import serializers
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, AllowAny)
from rest_framework.viewsets import GenericViewSet

from sapl.api.serializers import ModelChoiceSerializer, AutorSerializer,\
    ChoiceSerializer
from sapl.base.models import TipoAutor, Autor, CasaLegislativa
from sapl.materia.models import MateriaLegislativa
from sapl.parlamentares.models import Legislatura
from sapl.sessao.models import SessaoPlenaria, OrdemDia
from sapl.utils import SaplGenericRelation
from sapl.utils import generic_relations_for_model


class SaplGenericRelationSearchFilterSet(FilterSet):
    q = CharFilter(method='filter_q')

    def filter_q(self, queryset, name, value):

        query = value.split(' ')
        if query:
            q = Q()
            for qtext in query:
                if not qtext:
                    continue
                q_fs = Q(nome__icontains=qtext)

                order_by = []

                for gr in generic_relations_for_model(self._meta.model):
                    sgr = gr[1]
                    for item in sgr:
                        if item.related_model != self._meta.model:

                            continue
                        flag_order_by = True
                        for field in item.fields_search:
                            if flag_order_by:
                                flag_order_by = False
                                order_by.append('%s__%s' % (
                                    item.related_query_name(),
                                    field[0])
                                )
                            # if len(field) == 3 and field[2](qtext) is not
                            # None:
                            q_fs = q_fs | Q(**{'%s__%s%s' % (
                                item.related_query_name(),
                                field[0],
                                field[1]): qtext if len(field) == 2
                                else field[2](qtext)})

                q = q & q_fs

            if q:
                queryset = queryset.filter(q).order_by(*order_by)

        return queryset


class SearchForFieldWidget(MultiWidget):

    def decompress(self, value):
        if value is None:
            return [None, None]
        return value

    def __init__(self, attrs=None):
        widgets = (TextInput, TextInput)
        MultiWidget.__init__(self, widgets, attrs)


class SearchForFieldField(MultiValueField):
    widget = SearchForFieldWidget

    def __init__(self, *args, **kwargs):
        fields = (
            CharField(),
            CharField())
        super(SearchForFieldField, self).__init__(fields, *args, **kwargs)

    def compress(self, parameters):
        if parameters:
            return parameters
        return None


class SearchForFieldFilter(CharFilter):
    field_class = SearchForFieldField


class AutorChoiceFilterSet(SaplGenericRelationSearchFilterSet):
    q = CharFilter(method='filter_q')
    tipo = ModelChoiceFilter(queryset=TipoAutor.objects.all())

    class Meta:
        model = Autor
        fields = ['q',
                  'tipo',
                  'nome', ]

    def filter_q(self, queryset, name, value):
        return super().filter_q(
            queryset, name, value).distinct('nome').order_by('nome')


class AutorSearchForFieldFilterSet(AutorChoiceFilterSet):
    q = SearchForFieldFilter(method='filter_q')

    class Meta(AutorChoiceFilterSet.Meta):
        pass

    def filter_q(self, queryset, name, value):

        value[0] = value[0].split(',')
        value[1] = value[1].split(',')

        params = {}
        for key, v in list(zip(value[0], value[1])):
            if v in ['True', 'False']:
                v = '1' if v == 'True' else '0'
            params[key] = v
        return queryset.filter(**params).distinct('nome').order_by('nome')


class AutoresPossiveisFilterSet(FilterSet):
    logger = logging.getLogger(__name__)
    data_relativa = DateFilter(method='filter_data_relativa')
    tipo = CharFilter(method='filter_tipo')

    class Meta:
        model = Autor
        fields = ['data_relativa', 'tipo', ]

    def filter_data_relativa(self, queryset, name, value):
        return queryset

    def filter_tipo(self, queryset, name, value):

        try:
            self.logger.debug(
                "Tentando obter TipoAutor correspondente à pk {}.".format(value))
            tipo = TipoAutor.objects.get(pk=value)
        except:
            self.logger.error("TipoAutor(pk={}) inexistente.".format(value))
            raise serializers.ValidationError(_('Tipo de Autor inexistente.'))

        qs = queryset.filter(tipo=tipo)

        return qs

    @property
    def qs(self):
        qs = super().qs

        data_relativa = self.form.cleaned_data['data_relativa'] \
            if 'data_relativa' in self.form.cleaned_data else None

        tipo = self.form.cleaned_data['tipo'] \
            if 'tipo' in self.form.cleaned_data else None

        if not tipo:
            return qs

        tipo = TipoAutor.objects.get(pk=tipo)
        if not tipo.content_type:
            return qs

        filter_for_model = 'filter_%s' % tipo.content_type.model

        if not hasattr(self, filter_for_model):
            return qs

        if not data_relativa:
            data_relativa = timezone.now()

        return getattr(self, filter_for_model)(qs, data_relativa).distinct()

    def filter_parlamentar(self, queryset, data_relativa):
        # não leva em conta afastamentos
        legislatura_relativa = Legislatura.objects.filter(
            data_inicio__lte=data_relativa,
            data_fim__gte=data_relativa).first()

        q = Q(
            parlamentar_set__mandato__data_inicio_mandato__lte=data_relativa,
            parlamentar_set__mandato__data_fim_mandato__isnull=True) | Q(
            parlamentar_set__mandato__data_inicio_mandato__lte=data_relativa,
            parlamentar_set__mandato__data_fim_mandato__gte=data_relativa)

        if legislatura_relativa.atual():
            q = q & Q(parlamentar_set__ativo=True)

        return queryset.filter(q)

    def filter_comissao(self, queryset, data_relativa):
        return queryset.filter(
            Q(comissao_set__data_extincao__isnull=True,
              comissao_set__data_fim_comissao__isnull=True) |
            Q(comissao_set__data_extincao__gte=data_relativa,
              comissao_set__data_fim_comissao__isnull=True) |
            Q(comissao_set__data_extincao__gte=data_relativa,
              comissao_set__data_fim_comissao__isnull=True) |
            Q(comissao_set__data_extincao__isnull=True,
              comissao_set__data_fim_comissao__gte=data_relativa) |
            Q(comissao_set__data_extincao__gte=data_relativa,
              comissao_set__data_fim_comissao__gte=data_relativa),
            comissao_set__data_criacao__lte=data_relativa)

    def filter_frente(self, queryset, data_relativa):
        return queryset.filter(
            Q(frente_set__data_extincao__isnull=True) |
            Q(frente_set__data_extincao__gte=data_relativa),
            frente_set__data_criacao__lte=data_relativa)

    def filter_bancada(self, queryset, data_relativa):
        return queryset.filter(
            Q(bancada_set__data_extincao__isnull=True) |
            Q(bancada_set__data_extincao__gte=data_relativa),
            bancada_set__data_criacao__lte=data_relativa)

    def filter_bloco(self, queryset, data_relativa):
        return queryset.filter(
            Q(bloco_set__data_extincao__isnull=True) |
            Q(bloco_set__data_extincao__gte=data_relativa),
            bloco_set__data_criacao__lte=data_relativa)

    def filter_orgao(self, queryset, data_relativa):
        # na implementação, não havia regras a implementar para orgao
        return queryset


class AutorChoiceSerializer(ModelChoiceSerializer):

    def get_text(self, obj):
        return obj.nome

    class Meta:
        model = Autor
        fields = ['id', 'nome']


class MateriaLegislativaOldSerializer(serializers.ModelSerializer):

    class Meta:
        model = MateriaLegislativa
        fields = '__all__'


class SessaoPlenariaOldSerializer(serializers.ModelSerializer):

    codReuniao = serializers.SerializerMethodField('get_pk_sessao')
    codReuniaoPrincipal = serializers.SerializerMethodField('get_pk_sessao')
    txtTituloReuniao = serializers.SerializerMethodField('get_name')
    txtSiglaOrgao = serializers.SerializerMethodField('get_sigla_orgao')
    txtApelido = serializers.SerializerMethodField('get_name')
    txtNomeOrgao = serializers.SerializerMethodField('get_nome_orgao')
    codEstadoReuniao = serializers.SerializerMethodField(
        'get_estadoSessaoPlenaria')
    txtTipoReuniao = serializers.SerializerMethodField('get_tipo_sessao')
    txtObjeto = serializers.SerializerMethodField('get_assunto_sessao')
    txtLocal = serializers.SerializerMethodField('get_endereco_orgao')
    bolReuniaoConjunta = serializers.SerializerMethodField(
        'get_reuniao_conjunta')
    bolHabilitarEventoInterativo = serializers.SerializerMethodField(
        'get_iterativo')
    idYoutube = serializers.SerializerMethodField('get_url')
    codEstadoTransmissaoYoutube = serializers.SerializerMethodField(
        'get_estadoTransmissaoYoutube')
    datReuniaoString = serializers.SerializerMethodField('get_date')

    # Constantes SessaoPlenaria (de 1-9) (apenas 3 serão usados)
    SESSAO_FINALIZADA = 4
    SESSAO_EM_ANDAMENTO = 3
    SESSAO_CONVOCADA = 2

    # Constantes EstadoTranmissaoYoutube (de 0 a 2)
    TRANSMISSAO_ENCERRADA = 2
    TRANSMISSAO_EM_ANDAMENTO = 1
    SEM_TRANSMISSAO = 0

    class Meta:
        model = SessaoPlenaria
        fields = (
            'codReuniao',
            'codReuniaoPrincipal',
            'txtTituloReuniao',
            'txtSiglaOrgao',
            'txtApelido',
            'txtNomeOrgao',
            'codEstadoReuniao',
            'txtTipoReuniao',
            'txtObjeto',
            'txtLocal',
            'bolReuniaoConjunta',
            'bolHabilitarEventoInterativo',
            'idYoutube',
            'codEstadoTransmissaoYoutube',
            'datReuniaoString'
        )

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaOldSerializer, self).__init__(args, kwargs)

    def get_pk_sessao(self, obj):
        return obj.pk

    def get_name(self, obj):
        return obj.__str__()

    def get_estadoSessaoPlenaria(self, obj):
        if obj.finalizada:
            return self.SESSAO_FINALIZADA
        elif obj.iniciada:
            return self.SESSAO_EM_ANDAMENTO
        else:
            return self.SESSAO_CONVOCADA

    def get_tipo_sessao(self, obj):
        return obj.tipo.__str__()

    def get_url(self, obj):
        return obj.url_video if obj.url_video else None

    def get_iterativo(self, obj):
        return obj.interativa if obj.interativa else False

    def get_date(self, obj):
        return "{} {}{}".format(
            obj.data_inicio.strftime("%d/%m/%Y"),
            obj.hora_inicio,
            ":00"
        )

    def get_estadoTransmissaoYoutube(self, obj):
        if obj.url_video:
            if obj.finalizada:
                return self.TRANSMISSAO_ENCERRADA
            else:
                return self.TRANSMISSAO_EM_ANDAMENTO
        else:
            return self.SEM_TRANSMISSAO

    def get_assunto_sessao(self, obj):
        pauta_sessao = ''
        ordem_dia = OrdemDia.objects.filter(sessao_plenaria=obj.pk)
        pauta_sessao = ', '.join([i.materia.__str__() for i in ordem_dia])

        return str(pauta_sessao)

    def get_endereco_orgao(self, obj):
        return self.casa().endereco

    def get_reuniao_conjunta(self, obj):
        return False

    def get_sigla_orgao(self, obj):
        return self.casa().sigla

    def get_nome_orgao(self, obj):
        return self.casa().nome

    def casa(self):
        casa = CasaLegislativa.objects.first()
        return casa


class ModelChoiceView(ListAPIView):
    """
    Deprecated

    TODO Migrar para customização na api automática

    """

    # FIXME aplicar permissão correta de usuário
    permission_classes = (IsAuthenticated,)
    serializer_class = ModelChoiceSerializer

    def get(self, request, *args, **kwargs):
        self.model = ContentType.objects.get_for_id(
            self.kwargs['content_type']).model_class()

        pagination = request.GET.get('pagination', '')

        if pagination == 'False':
            self.pagination_class = None

        return ListAPIView.get(self, request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()


class AutorListView(ListAPIView):
    """
    Deprecated

    TODO Migrar para customização na api automática

    Listagem de Autores com filtro para autores já cadastrados
    e/ou possíveis autores.

    - tr - tipo do resultado
      Prepera Lista de Autores para 2 cenários distintos

          - default = 1

          = 1 -> para (value, text) usados geralmente
              em combobox, radiobox, checkbox, etc com pesquisa básica
              de Autores feita pelo django-filter
              -> processo usado nas pesquisas, o mais usado.


          = 3 -> Devolve instancias da classe Autor filtradas pelo
                 django-filter

    - tipo      - chave primária do Tipo de Autor a ser filtrado

    - q         - busca textual no nome do Autor ou em  fields_search
                  declarados no field SaplGenericRelation das GenericFks
                      A busca textual acontece via django-filter com a
                      variável `tr` igual 1 ou 3. Em caso contrário,
                      o django-filter é desativado e a busca é feita
                      no model do ContentType associado ao tipo.

        - q_0 / q_1 - q_0 é opcional e quando usado, faz o código ignorar "q"...

                  q_0 -> campos lookup a serem filtrados em qualquer Model
                  que implemente SaplGenericRelation
                  q_1 -> o valor que será pesquisado no lookup de q_0

                  q_0 e q_1 podem ser separados por ","... isso dará a
                  possibilidade de filtrar mais de um campo.


                  http://localhost:8000
                      /api/autor?tr=1&q_0=parlamentar_set__ativo&q_1=False
                      /api/autor?tr=1&q_0=parlamentar_set__ativo&q_1=True
                      /api/autor?tr=3&q_0=parlamentar_set__ativo&q_1=False
                      /api/autor?tr=3&q_0=parlamentar_set__ativo&q_1=True

                  http://localhost:8000
                      /api/autor?tr=1
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,False
                      /api/autor?tr=1
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,True
                      /api/autor?tr=3
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,False
                      /api/autor?tr=3
                          &q_0=parlamentar_set__nome_parlamentar__icontains,
                               parlamentar_set__ativo
                          &q_1=Carvalho,True


                  não importa o campo que vc passe de qualquer dos Models
                  ligados... é possível ver que models são esses,
                      na ocasião do commit deste texto, executando:
                        In [6]: from sapl.utils import models_with_gr_for_model

                        In [7]: models_with_gr_for_model(Autor)
                        Out[7]:
                        [sapl.parlamentares.models.Parlamentar,
                         sapl.parlamentares.models.Frente,
                         sapl.comissoes.models.Comissao,
                         sapl.materia.models.Orgao,
                         sapl.sessao.models.Bancada,
                         sapl.sessao.models.Bloco]

                      qualquer atributo destes models podem ser passados
                      para busca
    """
    logger = logging.getLogger(__name__)

    TR_AUTOR_CHOICE_SERIALIZER = 1
    TR_AUTOR_SERIALIZER = 3

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    filter_class = AutorChoiceFilterSet
    filter_backends = (DjangoFilterBackend, )
    serializer_class = AutorChoiceSerializer

    @property
    def tr(self):
        username = self.request.user.username
        try:
            tr = int(self.request.GET.get
                     ('tr', AutorListView.TR_AUTOR_CHOICE_SERIALIZER))

            if tr not in (AutorListView.TR_AUTOR_CHOICE_SERIALIZER,
                          AutorListView.TR_AUTOR_SERIALIZER):
                return AutorListView.TR_AUTOR_CHOICE_SERIALIZER
        except Exception as e:
            self.logger.error('user=' + username + '. ' + str(e))
            return AutorListView.TR_AUTOR_CHOICE_SERIALIZER
        return tr

    def get(self, request, *args, **kwargs):
        if self.tr == AutorListView.TR_AUTOR_SERIALIZER:
            self.serializer_class = AutorSerializer
            self.permission_classes = (IsAuthenticated,)

        if self.filter_class and 'q_0' in request.GET:
            self.filter_class = AutorSearchForFieldFilterSet

        return ListAPIView.get(self, request, *args, **kwargs)


class AutoresProvaveisListView(ListAPIView):
    """
    Deprecated

    TODO Migrar para customização na api automática
    """

    logger = logging.getLogger(__name__)

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    filter_class = None
    filter_backends = []
    serializer_class = ChoiceSerializer

    def get_queryset(self):

        params = {'content_type__isnull': False}
        username = self.request.user.username
        tipo = ''
        try:
            tipo = int(self.request.GET.get('tipo', ''))
            if tipo:
                params['id'] = tipo
        except Exception as e:
            self.logger.error('user= ' + username + '. ' + str(e))
            pass

        tipos = TipoAutor.objects.filter(**params)

        if not tipos.exists() and tipo:
            raise Http404()

        r = []
        for tipo in tipos:
            q = self.request.GET.get('q', '').strip()

            model_class = tipo.content_type.model_class()

            fields = list(filter(
                lambda field: isinstance(field, SaplGenericRelation) and
                field.related_model == Autor,
                model_class._meta.get_fields(include_hidden=True)))

            """
            fields - é um array de SaplGenericRelation que deve possuir o
                 atributo fields_search. Verifique na documentação da classe
                 a estrutura de fields_search.
            """

            assert len(fields) >= 1, (_(
                'Não foi encontrado em %(model)s um atributo do tipo '
                'SaplGenericRelation que use o model %(model_autor)s') % {
                'model': model_class._meta.verbose_name,
                'model_autor': Autor._meta.verbose_name})

            qs = model_class.objects.all()

            q_filter = Q()
            if q:
                for item in fields:
                    if item.related_model != Autor:
                        continue
                    q_fs = Q()
                    for field in item.fields_search:
                        q_fs = q_fs | Q(**{'%s%s' % (
                            field[0],
                            field[1]): q})
                    q_filter = q_filter & q_fs

                qs = qs.filter(q_filter).distinct(
                    fields[0].fields_search[0][0]).order_by(
                        fields[0].fields_search[0][0])
            else:
                qs = qs.order_by(fields[0].fields_search[0][0])

            qs = qs.values_list(
                'id', fields[0].fields_search[0][0])
            r += list(qs)

        if tipos.count() > 1:
            r.sort(key=lambda x: x[1].upper())
        return r


class AutoresPossiveisListView(ListAPIView):
    """
    Deprecated

    TODO Migrar para customização na api automática
    """

    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = Autor.objects.all()
    model = Autor

    pagination_class = None

    filter_class = AutoresPossiveisFilterSet
    serializer_class = AutorChoiceSerializer


class MateriaLegislativaViewSet(ListModelMixin,
                                RetrieveModelMixin,
                                GenericViewSet):
    """
    Deprecated

    TODO Migrar para customização na api automática
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = MateriaLegislativaOldSerializer
    queryset = MateriaLegislativa.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('numero', 'ano', 'tipo', )


class SessaoPlenariaViewSet(ListModelMixin,
                            RetrieveModelMixin,
                            GenericViewSet):
    """
    Deprecated

    TODO Migrar para customização na api automática
    """

    permission_classes = (AllowAny,)
    serializer_class = SessaoPlenariaOldSerializer
    queryset = SessaoPlenaria.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('data_inicio', 'data_fim', 'interativa')
