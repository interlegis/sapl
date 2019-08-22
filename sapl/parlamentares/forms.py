from datetime import timedelta
import logging

from sapl.crispy_layout_mixin import SaplFormHelper
from crispy_forms.layout import Fieldset, Layout
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import ModelForm
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from floppyforms.widgets import ClearableFileInput
from image_cropping.widgets import CropWidget, ImageCropWidget
from sapl.utils import FileFieldCheckMixin, filiacao_data, intervalos_tem_intersecao

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import form_actions, to_row
from sapl.rules import SAPL_GROUP_VOTANTE
import django_filters

from .models import (ComposicaoColigacao, Filiacao, Frente, Legislatura,
                     Mandato, Parlamentar, Votante, Bloco, Bancada, CargoBloco,
                     CargoBlocoPartido, AfastamentoParlamentar, TipoAfastamento)


class ImageThumbnailFileInput(ClearableFileInput):
    template_name = 'floppyforms/image_thumbnail.html'


class CustomImageCropWidget(ImageCropWidget):
    """
    Custom ImageCropWidget that doesn't show the initial value of the field.
    We use this trick, and place it right under the CropWidget so that
    it looks like the user is seeing the image and clearing the image.
    """
    template_with_initial = (
        # '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )


def validar_datas_legislatura(eleicao, inicio, fim, pk=None):
    logger = logging.getLogger(__name__)
    # Verifica se data de eleição < inicio < fim
    if inicio >= fim or eleicao >= inicio:
        logger.error('A data início ({}) deve ser menor que a ' +
                     'data fim ({}) e a data eleição ({}) deve ser ' +
                     'menor que a data início ({})'.format(inicio, fim, eleicao, inicio))
        msg_error = _('A data início deve ser menor que a ' +
                      'data fim e a data eleição deve ser ' +
                      'menor que a data início')
        return (False, msg_error)

    # Verifica se há alguma data cadastrada no intervalo de tempo desejado
    intersecao_legislatura = Legislatura.objects.filter(
        data_inicio__lte=fim, data_fim__gte=inicio
    ).exclude(pk=pk).exists()
    if intersecao_legislatura:
        logger.error("Já existe uma legislatura neste intervalo de datas (data_inicio<={} e data_fim>={})."
                     .format(fim, inicio))
        msg_error = _('Já existe uma legislatura neste intervalo de datas')
        return (False, msg_error)

    # Verifica se há alguma outra data de eleição cadastrada
    if Legislatura.objects.filter(
            data_eleicao=eleicao).exclude(pk=pk).exists():
        logger.error(
            "Esta data de eleição ({}) já foi cadastrada.".format(eleicao))
        msg_error = _('Esta data de eleição já foi cadastrada')
        return (False, msg_error)

    return (True, None)


class MandatoForm(ModelForm):
    logger = logging.getLogger(__name__)

    class Meta:
        model = Mandato
        fields = ['legislatura', 'coligacao', 'votos_recebidos',
                  'data_inicio_mandato', 'data_fim_mandato',
                  'data_expedicao_diploma', 'titular',
                  'tipo_afastamento', 'observacao', 'parlamentar']
        widgets = {'parlamentar': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tipo_afastamento'].queryset = TipoAfastamento.objects.filter(indicador='F')


    def clean(self):
        super(MandatoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data

        legislatura = data['legislatura']

        data_inicio_mandato = data['data_inicio_mandato']
        if data_inicio_mandato:
            if (data_inicio_mandato < legislatura.data_inicio or
                    data_inicio_mandato > legislatura.data_fim):
                self.logger.error("Data início mandato ({}) fora do intervalo"
                                  " de legislatura informada ({} a {})."
                                  .format(data_inicio_mandato, legislatura.data_inicio, legislatura.data_fim))
                raise ValidationError(_("Data início mandato fora do intervalo"
                                        " de legislatura informada"))

        data_fim_mandato = data['data_fim_mandato']
        if data_fim_mandato:
            if (data_fim_mandato < legislatura.data_inicio or
                    data_fim_mandato > legislatura.data_fim):
                self.logger.error("Data fim mandato ({}) fora do intervalo"
                                  " de legislatura informada ({} a {})."
                                  .format(data_fim_mandato, legislatura.data_inicio, legislatura.data_fim))
                raise ValidationError(_("Data fim mandato fora do intervalo de"
                                        " legislatura informada"))

        data_expedicao_diploma = data['data_expedicao_diploma']
        if (data_expedicao_diploma and
                data_expedicao_diploma > data_inicio_mandato):
            self.logger.error("A data da expedição do diploma ({}) deve ser anterior "
                              "a data de início do mandato ({}).".format(data_expedicao_diploma, data_inicio_mandato))
            raise ValidationError(_("A data da expedição do diploma deve ser anterior "
                                    "a data de início do mandato"))

        coligacao = data['coligacao']
        if coligacao and not coligacao.legislatura == legislatura:
            self.logger.error("A coligação selecionada ({}) não está cadastrada "
                              "na mesma legislatura ({}) que o presente mandato ({}), "
                              "favor verificar a coligação ou fazer o cadastro "
                              "de uma nova coligação na legislatura correspondente"
                              .format(coligacao, coligacao.legislatura, legislatura))
            raise ValidationError(_("A coligação selecionada não está cadastrada "
                                    "na mesma legislatura que o presente mandato, "
                                    "favor verificar a coligação ou fazer o cadastro "
                                    "de uma nova coligação na legislatura correspondente"))

        existe_mandato = Mandato.objects.filter(
            parlamentar=data['parlamentar'],
            legislatura=data['legislatura']).exists()
        if existe_mandato and data['titular']:
            self.logger.error("Mandato nesta legislatura (parlamentar={}, legislatura={}) já existe."
                              .format(data['parlamentar'], data['legislatura']))
            raise ValidationError(_('Mandato nesta legislatura já existe.'))

        return self.cleaned_data


class LegislaturaForm(ModelForm):

    logger = logging.getLogger(__name__)

    class Meta:
        model = Legislatura
        exclude = []

    def clean(self):
        data = super(LegislaturaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        numero = data['numero']
        data_inicio = data['data_inicio']
        data_fim = data['data_fim']
        data_eleicao = data['data_eleicao']

        pk = self.instance.pk

        ultima_legislatura = Legislatura.objects.filter(data_inicio__lt=data_inicio
                                                        ).order_by('-data_inicio').exclude(id=pk).first()
        proxima_legislatura = Legislatura.objects.filter(data_fim__gt=data_fim
                                                         ).order_by('data_fim').exclude(id=pk).first()

        if ultima_legislatura and ultima_legislatura.numero >= numero:
            self.logger.error("Número ({}) deve ser maior que o da legislatura anterior ({})."
                              .format(numero, ultima_legislatura.numero))
            raise ValidationError(_("Número deve ser maior que o da legislatura anterior ({})."
                                    .format(numero)))
        elif proxima_legislatura and proxima_legislatura.numero <= numero:
            self.logger.error("O Número ({}) deve ser menor que {}, pois existe uma "
                              "legislatura cronologicamente à frente desta que está sendo criada!"
                              .format(numero, proxima_legislatura.numero))
            msg_erro = "O Número deve ser menor que {}, pois existe uma " \

            "legislatura cronologicamente à frente desta que está sendo criada!"
            msg_erro = msg_erro.format(proxima_legislatura.numero)
            raise ValidationError(_(msg_erro))

        valida_datas = validar_datas_legislatura(data_eleicao,
                                                 data_inicio,
                                                 data_fim,
                                                 pk=pk)
        if not valida_datas[0]:
            raise ValidationError(valida_datas[1])

        return data


class ParlamentarForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = Parlamentar
        exclude = []

        widgets = {
            'fotografia': CustomImageCropWidget(),
            'cropping': CropWidget(),
            'biografia': forms.Textarea(
                attrs={'id': 'texto-rico'})}


class ParlamentarFilterSet(django_filters.FilterSet):
    nome_parlamentar = django_filters.CharFilter(
        label=_('Nome do Parlamentar'),
        lookup_expr='icontains')

    class Meta:
        model = Parlamentar
        fields = ['nome_parlamentar']

    def __init__(self, *args, **kwargs):
        super(ParlamentarFilterSet, self).__init__(*args, **kwargs)

        row0 = to_row([('nome_parlamentar', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Parlamentar'),
                     row0,
                     form_actions(label='Pesquisar'))
        )


class ParlamentarCreateForm(ParlamentarForm):

    logger = logging.getLogger(__name__)

    class Meta(ParlamentarForm.Meta):
        widgets = {
            'fotografia': forms.ClearableFileInput(),
            'biografia': forms.Textarea(
                attrs={'id': 'texto-rico'})
        }

    def clean(self):
        super().clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data
        parlamentar = Parlamentar.objects.filter(nome_parlamentar=cleaned_data['nome_parlamentar']).exists()

        if parlamentar:
            self.logger.error('Parlamentar já cadastrado.')
            raise ValidationError('Parlamentar já cadastrado.')

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        parlamentar = super(ParlamentarCreateForm, self).save(commit)
        content_type = ContentType.objects.get_for_model(Parlamentar)
        object_id = parlamentar.pk
        tipo = TipoAutor.objects.get(content_type=content_type)
        Autor.objects.create(
            content_type=content_type,
            object_id=object_id,
            tipo=tipo,
            nome=parlamentar.nome_parlamentar
        )
        return parlamentar


def validar_datas(data_filiacao, data_desfiliacao, parlamentar, filiacao):

    logger = logging.getLogger(__name__)

    # Verifica se data de desfiliacao é anterior a data de filiacao
    if data_desfiliacao and data_desfiliacao < data_filiacao:
        logger.error("A data de desfiliação ({}) é anterior à data de filiação ({})."
                     .format(data_desfiliacao, data_filiacao))
        error_msg = _("A data de desfiliação não pode anterior \
                       à data de filiação")
        return [False, error_msg]

    filiacoes = parlamentar.filiacao_set.order_by('data')
    if not filiacoes.exists():
        return [True, '']

    # data ficticia de desfiliacao
    today = timezone.now()
    df_desfiliacao = data_desfiliacao if data_desfiliacao else today

    # se não puder haver filiação no mesmo dia de desfiliação, basta
    # retirar os timedelta abaixo
    range_livre_exigido = Q(
        data__range=[data_filiacao + timedelta(days=1),
                     df_desfiliacao - timedelta(days=1)]) | Q(
        data_desfiliacao__range=[data_filiacao + timedelta(days=1),
                                 df_desfiliacao - timedelta(days=1)])

    filiacao_em_edicao_id = filiacao.pk
    error_msg = None
    # filiação em edição não é a última e está sem data de desfiliação
    if not data_desfiliacao and filiacao_em_edicao_id and\
            filiacao_em_edicao_id != filiacoes.last().pk:
        logger.error("Data de desfiliação do parlamentar não pode ser "
                     "ausente, se existirem datas de filiação posteriores.")
        error_msg = _("Data de desfiliação do parlamentar não pode ser\
                    ausente, se existirem datas de filiação posteriores.")

    # a filiação que está sendo inclusa não tem data de desfiliação mas
    #  já existe outra sem data de desfiliação
    elif not data_desfiliacao and not filiacao_em_edicao_id and\
            not filiacoes.last().data_desfiliacao:
        logger.error("O parlamentar não pode se filiar a novo partido sem"
                     " antes se desfiliar do partido anterior.")
        error_msg = _("O parlamentar não pode se filiar a novo partido sem\
                        antes se desfiliar do partido anterior.")

    if not error_msg:
        # se a filiação é uma edição, a exclui das possibilidades
        if filiacao_em_edicao_id:
            filiacoes = filiacoes.exclude(pk=filiacao_em_edicao_id)

        # testa a intercessão de intervalo com outra filiação
        if filiacoes.filter(range_livre_exigido).exists():
            logger.error("A data de filiação e desfiliação não podem estar"
                         " no intervalo de outro período de filiação.")
            error_msg = _("A data de filiação e desfiliação (intervalo de {} a {}) "
                          "não podem estar no intervalo de outro período de filiação."
                          .format(data_filiacao, df_desfiliacao, ))

    if not error_msg:
        # passou pelo teste de intervalo mas a data de filiação é maior que
        # a ultima que está em aberto
        if filiacoes.filter(data_desfiliacao__isnull=True,
                            data__lte=data_filiacao).exists():
            logger.error("Não pode haver um registro de filiação com data de "
                         "filiação igual ou superior a data de filiação em aberto ({})."
                         .format(data_filiacao))
            error_msg = _("Não pode haver um registro de filiação com data de \
                    filiação igual ou superior a data de filiação em aberto.")

    if error_msg:
        return [False, error_msg]

    return [True, '']


class FiliacaoForm(ModelForm):

    class Meta:
        model = Filiacao
        fields = ['partido',
                  'data',
                  'data_desfiliacao']
        widgets = {'data': forms.DateInput(attrs={'autocomplete': 'off'}),
                   'data_desfiliacao': forms.DateInput(attrs={'autocomplete': 'off'})}

    def clean(self):
        super(FiliacaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        filiacao = super(FiliacaoForm, self).save(commit=False)
        validacao = validar_datas(self.cleaned_data['data'],
                                  self.cleaned_data['data_desfiliacao'],
                                  filiacao.parlamentar,
                                  filiacao)

        if not validacao[0]:
            raise ValidationError(validacao[1])

        return self.cleaned_data


class ComposicaoColigacaoForm(ModelForm):

    logger = logging.getLogger(__name__)

    class Meta:
        model = ComposicaoColigacao
        fields = ['partido']

    def clean(self):
        super(ComposicaoColigacaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data
        pk = self.initial['coligacao_id']
        if (ComposicaoColigacao.objects.filter(
           coligacao_id=pk,
           partido=cleaned_data.get('partido')).exists()):
            self.logger.error("Esse partido (coligacao_id={} e partido={}) já foi cadastrado "
                              "nesta coligação.".format(pk, cleaned_data.get('partido')))
            msg = _('Esse partido já foi cadastrado nesta coligação.')
            raise ValidationError(msg)

        return self.cleaned_data


class FrenteForm(ModelForm):
    logger = logging.getLogger(__name__)

    def __init__(self, *args, **kwargs):
        super(FrenteForm, self).__init__(*args, **kwargs)
        self.fields['parlamentares'].queryset = Parlamentar.objects.filter(
            ativo=True).order_by('nome_completo')
        self.fields['parlamentares'].label = _('Parlamentares \
                (Mantenha CTRL pressionado para selecionar vários)')

    class Meta:
        model = Frente
        fields = '__all__'

    def clean(self):
        super(FrenteForm, self).clean()
        cd = self.cleaned_data
        if not self.is_valid():
            return self.cleaned_data

        if cd['data_extincao'] and cd['data_criacao'] >= cd['data_extincao']:
            self.logger.error("Data Dissolução ({}) não pode ser anterior a Data Criação ({})."
                              .format(cd['data_extincao'], cd['data_criacao']))
            raise ValidationError(
                _("Data Dissolução não pode ser anterior a Data Criação"))

        return cd

    @transaction.atomic
    def save(self, commit=True):
        frente = super(FrenteForm, self).save(commit)

        if not self.instance.pk:
            frente = super(FrenteForm, self).save(commit)
            content_type = ContentType.objects.get_for_model(Frente)
            object_id = frente.pk
            tipo = TipoAutor.objects.get(descricao__icontains='Frente')
            Autor.objects.create(
                content_type=content_type,
                object_id=object_id,
                tipo=tipo,
                nome=frente.nome
            )
        return frente


class VotanteForm(ModelForm):

    username = forms.CharField(
        label=_('Usuário'),
        required=True,
        max_length=30)

    logger = logging.getLogger(__name__)

    class Meta:
        model = Votante
        fields = ['username']

    def __init__(self, *args, **kwargs):
        row1 = to_row([('username', 4)])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_('Votante'),
                     row1, form_actions(label='Salvar'))
        )
        super(VotanteForm, self).__init__(*args, **kwargs)

    def valida_igualdade(self, texto1, texto2, msg):
        if texto1 != texto2:
            raise ValidationError(msg)
        return True

    def clean(self):
        super(VotanteForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cd = self.cleaned_data

        username = cd['username']
        user = get_user_model().objects.filter(username=username)
        if not user.exists():
            self.logger.error(
                "Não foi possível vincular usuário. Usuário {} não existe.".format(username))
            raise ValidationError(_(
                "{} [{}] {}".format(
                    'Não foi possível vincular usuário. Usuário',
                    username,
                    'não existe')))
        if Votante.objects.filter(user=user[0].pk).exists():
            self.logger.error("Não foi possível vincular usuário. Usuário {} já está "
                              "vinculado à outro parlamentar.".format(username))
            raise ValidationError(_(
                "{} [{}] {}".format(
                    'Não foi possível vincular usuário. Usuário',
                    username,
                    'já esta vinculado à outro parlamentar')))

        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=False):
        votante = super(VotanteForm, self).save(commit)

        # Cria user
        u = User.objects.get(username=self.cleaned_data['username'])
        # Adiciona user ao grupo
        g = Group.objects.filter(name=SAPL_GROUP_VOTANTE)[0]
        u.groups.add(g)

        votante.user = u
        votante.save()
        return votante


class VincularParlamentarForm(forms.Form):
    logger = logging.getLogger(__name__)

    parlamentar = forms.ModelChoiceField(
        label=Parlamentar._meta.verbose_name,
        queryset=Parlamentar.objects.filter(ativo=True),
        required=True,
        empty_label='Selecione'
    )

    legislatura = forms.ModelChoiceField(
        label=Legislatura._meta.verbose_name,
        queryset=Legislatura.objects.all(),
        required=True,
        empty_label='Selecione'
    )

    data_expedicao_diploma = forms.DateField(
        label='Data de Expedição do Diploma',
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        row1 = to_row([
            ('parlamentar', 6),
            ('legislatura', 3),
            ('data_expedicao_diploma', 3)
        ])

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Vincular Parlamentar',
                row1,
                form_actions(label='Vincular')
            )
        )

    def clean(self):
        super().clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data
        parlamentar = cleaned_data['parlamentar']
        legislatura = cleaned_data['legislatura']
        data_expedicao_diploma = cleaned_data['data_expedicao_diploma']

        if parlamentar.mandato_set.filter(legislatura=legislatura):
            self.logger.error('Parlamentar já está vinculado a legislatura informada.')
            raise ValidationError(_('Parlamentar já está vinculado a legislatura informada.'))
        elif data_expedicao_diploma and legislatura.data_inicio <= data_expedicao_diploma:
            self.logger.error('Data da Expedição do Diploma deve ser anterior a data de início da Legislatura.')
            raise ValidationError(_('Data da Expedição do Diploma deve ser anterior a data de início da Legislatura.'))

        return cleaned_data


class BlocoForm(ModelForm):
    class Meta:
        model = Bloco
        fields = ['nome', 'partidos', 'data_criacao',
                  'data_extincao', 'descricao']

    def clean(self):
        super(BlocoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        if self.cleaned_data['data_extincao']:
            if (self.cleaned_data['data_extincao'] <
                    self.cleaned_data['data_criacao']):
                msg = _('Data de extinção não pode ser menor que a de criação')
                raise ValidationError(msg)
        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        bloco = super(BlocoForm, self).save(commit)
        content_type = ContentType.objects.get_for_model(Bloco)
        object_id = bloco.pk
        tipo = TipoAutor.objects.get(content_type=content_type)
        Autor.objects.create(
            content_type=content_type,
            object_id=object_id,
            tipo=tipo,
            nome=bloco.nome
        )
        return bloco


class BancadaForm(ModelForm):

    class Meta:
        model = Bancada
        fields = ['legislatura', 'nome', 'partido', 'data_criacao',
                  'data_extincao', 'descricao']

    def clean(self):
        super(BancadaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data

        legislatura = data['legislatura']

        data_criacao = data['data_criacao']
        if data_criacao:
            if (data_criacao < legislatura.data_inicio or
                    data_criacao > legislatura.data_fim):
                raise ValidationError(_("Data de criação da bancada fora do intervalo"
                                        " de legislatura informada"))

        data_extincao = data['data_extincao']
        if data_extincao:
            if (data_extincao < legislatura.data_inicio or
                    data_extincao > legislatura.data_fim):
                raise ValidationError(_("Data fim da bancada fora do intervalo de"
                                        " legislatura informada"))

        if self.cleaned_data['data_extincao']:
            if (self.cleaned_data['data_extincao'] <
                    self.cleaned_data['data_criacao']):
                msg = _('Data de extinção não pode ser menor que a de criação')
                raise ValidationError(msg)
        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        bancada = super(BancadaForm, self).save(commit)
        content_type = ContentType.objects.get_for_model(Bancada)
        object_id = bancada.pk
        tipo = TipoAutor.objects.get(content_type=content_type)
        Autor.objects.create(
            content_type=content_type,
            object_id=object_id,
            tipo=tipo,
            nome=bancada.nome
        )
        return bancada


class CargoBlocoForm(ModelForm):
    class Meta:
        model = CargoBloco
        fields = '__all__'

class CargoBlocoPartidoForm(ModelForm):

    class Meta:
        model = CargoBlocoPartido
        fields = ['cargo','parlamentar','data_inicio','data_fim']
    

    def __init__(self, *args, **kwargs):
        super(CargoBlocoPartidoForm, self).__init__(*args, **kwargs)
        bloco_pk = self.initial['bloco_pk']
        if bloco_pk:
            self.bloco = Bloco.objects.get(pk=bloco_pk)
            partidos = self.bloco.partidos.all().values_list('id', flat=True)
            parlamentares_filiacao = Filiacao.objects.select_related('partido').filter(partido__in=partidos).values_list('parlamentar', flat=True)
            self.fields['parlamentar'].queryset = Parlamentar.objects.filter(id__in=parlamentares_filiacao)
        
        if self.instance and self.instance.pk:
            self.fields['parlamentar'].widget.attrs['disabled'] = 'disabled'
            self.fields['parlamentar'].required = False


    def clean(self):
        super(CargoBlocoPartidoForm, self).clean()
        cleaned_data = self.cleaned_data

        aux_data_fim = cleaned_data['data_fim'] if cleaned_data['data_fim'] else (cleaned_data['data_inicio'] + timedelta(days=1))

        if cleaned_data['cargo'].unico:
            for vinculo in CargoBlocoPartido.objects.filter(bloco=self.bloco):
                if not vinculo.data_fim:
                    vinculo.data_fim = timezone.now().date()
                if intervalos_tem_intersecao(cleaned_data['data_inicio'],
                    aux_data_fim,
                    vinculo.data_inicio,
                    vinculo.data_fim) and vinculo.cargo.unico and \
                    not(self.instance and self.instance.id == vinculo.id):
                        raise ValidationError("Cargo unico já é utilizado nesse período.")
        
        if aux_data_fim <= cleaned_data['data_inicio']:
            raise ValidationError("Data Inicial deve ser anterior a data final.")
        
        if self.instance and self.instance.pk:
            self.cleaned_data['parlamentar'] = self.instance.parlamentar
        else:
            self.cleaned_data['parlamentar'] = self.cleaned_data.get('parlamentar')

        fora_de_mandato = True
        for mandato in Mandato.objects.filter(parlamentar=self.cleaned_data.get('parlamentar')):
            if not intervalos_tem_intersecao(mandato.data_inicio_mandato,
                    cleaned_data['data_inicio'],
                    aux_data_fim,
                    mandato.legislatura.data_fim):
                fora_de_mandato = False              
        if fora_de_mandato:
            raise ValidationError("Data de inicio e fim fora de periodo do mandato do parlamentar.")

        if self.instance.pk and (cleaned_data['parlamentar'].id != self.instance.parlamentar.id):
            raise ValidationError("Não é possivel alterar o parlamentar " + str(self.instance.parlamentar))


class AfastamentoParlamentarForm(ModelForm):
    logger = logging.getLogger(__name__)

    class Meta:
        model = AfastamentoParlamentar
        fields = ['data_inicio', 'data_fim', 'mandato',
                  'tipo_afastamento', 'observacao', 'parlamentar']
        widgets = {'parlamentar': forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not (self.instance and self.instance.pk):
            parlamentar = kwargs['initial']['parlamentar']
            self.fields['mandato'].queryset = Mandato.objects.filter(parlamentar=parlamentar)

        self.fields['tipo_afastamento'].queryset = TipoAfastamento.objects.filter(indicador='A')

    def clean(self):
        super(AfastamentoParlamentarForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        data = self.cleaned_data

        mandato = data['mandato']

        data_inicio_mandato = mandato.data_inicio_mandato
        data_fim_mandato = mandato.data_fim_mandato
        data_inicio_afastamento = data['data_inicio']
        data_fim_afastamento = data['data_fim']

        if data_inicio_afastamento < data_inicio_mandato:
            self.logger.error("Data início de afastamento ({}) anterior ao inicio"
                              " do mandato informado ({})."
                              .format(data_inicio_afastamento, data_inicio_mandato))
            raise ValidationError(_("Data início do afastamento anterior ao início"
                                    " do mandato informado."))

        if data_fim_mandato and data_inicio_afastamento > data_fim_mandato:
            self.logger.error("Data início de afastamento ({}) posterior ao fim"
                                " do mandato informado ({} a {})."
                                .format(data_inicio_afastamento, data_fim_mandato))
            raise ValidationError(_("Data início do afastamento posterior ao fim"
                                    " do mandato informado."))
                                    
        if data_fim_afastamento:
            if data_fim_afastamento < data_inicio_afastamento:
                self.logger.error("Data fim de afastamento ({}) anterior à data início"
                                  " do afastamento ({})."
                                  .format(data_fim_afastamento, data_inicio_afastamento))
                raise ValidationError(_("Data fim do afastamento anterior à data início do"
                                        " afastamento."))

            if data_fim_afastamento < data_inicio_mandato:
                self.logger.error("Data fim de afastamento ({}) anterior ao início"
                                  " do mandato informado ({} a {})."
                                .format(data_fim_afastamento, data_inicio_mandato))
                raise ValidationError(_("Data fim do afastamento anterior ao início"
                               " do mandato informado."))

            if data_fim_mandato and data_fim_afastamento > data_fim_mandato:
                self.logger.error("Data fim de afastamento ({}) posterior ao fim"
                                  " do mandato informado ({})."
                                .format(data_inicio_afastamento, data_fim_mandato))
                raise ValidationError(_("Data fim do afastamento posterior ao fim"
                               " do mandato informado."))

        ultimo_afastamento = AfastamentoParlamentar.objects.last()
        if ultimo_afastamento and not ultimo_afastamento.data_fim \
           and ultimo_afastamento != self.instance:
            self.logger.error("Existe Afastamento sem Data Fim.")
            raise ValidationError(_("Existe Afastamento sem Data Fim.")) 

        return self.cleaned_data
