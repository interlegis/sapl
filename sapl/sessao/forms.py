import django_filters

from crispy_forms.layout import Button, Fieldset, HTML, Layout
from datetime import datetime

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import ModelForm
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import Autor, TipoAutor
from sapl.crispy_layout_mixin import (form_actions, to_row, 
                                      SaplFormHelper, SaplFormLayout)
from sapl.materia.forms import MateriaLegislativaFilterSet
from sapl.materia.models import (MateriaLegislativa, StatusTramitacao,
                                 TipoMateriaLegislativa)
from sapl.parlamentares.models import Mandato, Parlamentar
from sapl.utils import (autor_label, autor_modal,
                        choice_anos_com_sessaoplenaria,
                        FileFieldCheckMixin,
                        MateriaPesquisaOrderingFilter,
                        RANGE_DIAS_MES, RANGE_MESES,
                        timezone, validar_arquivo)

from .models import (Bancada, ExpedienteMateria,
                     JustificativaAusencia, OcorrenciaSessao, Orador,
                     OradorExpediente, OradorOrdemDia, OrdemDia,
                     ORDENACAO_RESUMO, PresencaOrdemDia,
                     RegistroLeitura, ResumoOrdenacao, RetiradaPauta,
                     SessaoPlenaria, SessaoPlenariaPresenca,
                     TipoResultadoVotacao, TipoRetiradaPauta)


MES_CHOICES = RANGE_MESES
DIA_CHOICES = RANGE_DIAS_MES


class SessaoPlenariaForm(FileFieldCheckMixin, ModelForm):

    class Meta:
        model = SessaoPlenaria
        exclude = ['cod_andamento_sessao']

    def clean(self):
        super(SessaoPlenariaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        instance = self.instance

        num = self.cleaned_data['numero']
        sl = self.cleaned_data['sessao_legislativa']
        leg = self.cleaned_data['legislatura']
        tipo = self.cleaned_data['tipo']
        abertura = self.cleaned_data['data_inicio']
        encerramento = self.cleaned_data['data_fim']

        error = ValidationError(
            "Número de Sessão Plenária já existente "
            "para a Legislatura, Sessão Legislativa e Tipo informados. "
            "Favor escolher um número distinto.")

        qs = tipo.queryset_tipo_numeracao(leg, sl, abertura)
        qs &= Q(numero=num)

        if SessaoPlenaria.objects.filter(qs).exclude(pk=instance.pk).exists():
            raise error

        # Condições da verificação
        abertura_entre_leg = leg.data_inicio <= abertura <= leg.data_fim
        abertura_entre_sl = sl.data_inicio <= abertura <= sl.data_fim
        if encerramento is not None:
            # Verifica se a data de encerramento é anterior a data de abertura
            if encerramento < abertura:
                raise ValidationError("A data de encerramento não pode ser "
                                      "anterior a data de abertura.")
            encerramento_entre_leg = leg.data_inicio <= encerramento <= leg.data_fim
            encerramento_entre_sl = sl.data_inicio <= encerramento <= sl.data_fim
        else:
            encerramento_entre_leg = True
            encerramento_entre_sl = True


        ## Sessões Extraordinárias podem estar fora da sessão legislativa
        descricao_tipo = tipo.nome.lower()
        if "extraordinária" in descricao_tipo or "especial" in descricao_tipo:
            # Ignora checagem de limites para Sessão Legislativa
            abertura_entre_sl = True
            encerramento_entre_sl = True

        if not (abertura_entre_leg and encerramento_entre_leg):
            raise ValidationError("A data de abertura e encerramento da Sessão "
                                  "Plenária deve estar compreendida entre a "
                                  "data de abertura e encerramento da Legislatura")

        if not (abertura_entre_sl and encerramento_entre_sl):
            raise ValidationError("A data de abertura e encerramento da Sessão "
                                  "Plenária deve estar compreendida entre a "
                                  "data de abertura e encerramento da Sessão Legislativa")
        

        upload_pauta = self.cleaned_data.get('upload_pauta', False)
        upload_ata = self.cleaned_data.get('upload_ata', False)
        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_pauta:
            validar_arquivo(upload_pauta, "Pauta da Sessão")
        
        if upload_ata:
            validar_arquivo(upload_ata, "Ata da Sessão")

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo da Sessão")

        return self.cleaned_data


class RetiradaPautaForm(ModelForm):

    tipo_de_retirada = forms.ModelChoiceField(required=True,
                                              empty_label='------------',
                                              queryset=TipoRetiradaPauta.objects.all())
    expediente = forms.ModelChoiceField(required=False,
                                        label='Matéria do Expediente',
                                        queryset=ExpedienteMateria.objects.all())
    ordem = forms.ModelChoiceField(required=False,
                                   label='Matéria da Ordem do Dia',
                                   queryset=OrdemDia.objects.all())
    materia = forms.ModelChoiceField(required=False,
                                     widget=forms.HiddenInput(),
                                     queryset=MateriaLegislativa.objects.all())

    class Meta:
        model = RetiradaPauta
        fields = ['ordem',
                  'expediente',
                  'parlamentar',
                  'tipo_de_retirada',
                  'data',
                  'observacao',
                  'materia']

    def __init__(self, *args, **kwargs):

        row1 = to_row([('tipo_de_retirada', 5),
                       ('parlamentar', 4),
                       ('data', 3)])
        row2 = to_row([('ordem', 6),
                       ('expediente', 6)])
        row3 = to_row([('observacao', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Retirada de Pauta'),
                     row1, row2, row3))

        q = Q(sessao_plenaria=kwargs['initial']['sessao_plenaria'])
        ordens = OrdemDia.objects.filter(q)
        expedientes = ExpedienteMateria.objects.filter(q)
        retiradas_ordem = [
            r.ordem for r in RetiradaPauta.objects.filter(q, ordem__in=ordens)]
        retiradas_expediente = [r.expediente for r in RetiradaPauta.objects.filter(
            q, expediente__in=expedientes)]
        setOrdem = set(ordens) - set(retiradas_ordem)
        setExpediente = set(expedientes) - set(retiradas_expediente)

        super(RetiradaPautaForm, self).__init__(
            *args, **kwargs)

        if self.instance.pk:
            setOrdem = set(ordens)
            setExpediente = set(expedientes)

        presencas = SessaoPlenariaPresenca.objects.filter(
            q).order_by('parlamentar__nome_parlamentar')
        presentes = [p.parlamentar for p in presencas]

        self.fields['expediente'].choices = [
            (None, "------------")] + [(e.id, e.materia) for e in setExpediente]
        self.fields['ordem'].choices = [
            (None, "------------")] + [(o.id, o.materia) for o in setOrdem]
        self.fields['parlamentar'].choices = [
            (None, "------------")] + [(p.id, p) for p in presentes]

    def clean(self):

        super(RetiradaPautaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        sessao_plenaria = self.instance.sessao_plenaria
        if self.cleaned_data['data'] < sessao_plenaria.data_inicio:
            raise ValidationError(
                _("Data de retirada de pauta anterior à abertura da Sessão."))
        if sessao_plenaria.data_fim and self.cleaned_data['data'] > sessao_plenaria.data_fim:
            raise ValidationError(
                _("Data de retirada de pauta posterior ao encerramento da Sessão."))

        if self.cleaned_data['ordem'] and self.cleaned_data['ordem'].registrovotacao_set.exists():
            raise ValidationError(
                _("Essa matéria já foi votada, portanto não pode ser retirada de pauta."))
        elif self.cleaned_data['expediente'] and self.cleaned_data['expediente'].registrovotacao_set.exists():
            raise ValidationError(
                _("Essa matéria já foi votada, portanto não pode ser retirada de pauta."))

        return self.cleaned_data

    def save(self, commit=False):
        retirada = super(RetiradaPautaForm, self).save(commit=commit)
        if retirada.ordem:
            ordem = retirada.ordem
            retirada.materia = ordem.materia
            ordem.votacao_aberta = False
            ordem.save()
        elif retirada.expediente:
            expediente = retirada.expediente
            retirada.materia = expediente.materia
            expediente.votacao_aberta = False
            expediente.save()
        retirada.save()
        return retirada


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


class ExpedienteMateriaForm(ModelForm):

    _model = ExpedienteMateria
    data_atual = timezone.now()

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
        widget=forms.Select(attrs={'autocomplete': 'off'}))

    numero_materia = forms.CharField(
        label='Número Matéria', required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    ano_materia = forms.CharField(
        label='Ano Matéria',
        initial=int(data_atual.year),
        required=True,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    data_ordem = forms.CharField(
        label='Data Sessão',
        initial=datetime.strftime(timezone.now(), '%d/%m/%Y'),
        widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    apenas_leitura = forms.BooleanField(label='Apenas Leitura', required=False)

    class Meta:
        model = ExpedienteMateria
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_numero_ordem(self):
        sessao = self.instance.sessao_plenaria

        numero_ordem_exists = ExpedienteMateria.objects.filter(
            sessao_plenaria=sessao,
            numero_ordem=self.cleaned_data['numero_ordem']).exists()

        if numero_ordem_exists and not self.instance.pk:
            msg = _('Esse número de ordem já existe.')
            raise ValidationError(msg)

        return self.cleaned_data['numero_ordem']

    def clean_data_ordem(self):
        return self.instance.sessao_plenaria.data_inicio

    def clean(self):
        cleaned_data = super(ExpedienteMateriaForm, self).clean()
        if not self.is_valid():
            return cleaned_data

        sessao = self.instance.sessao_plenaria

        try:
            materia = MateriaLegislativa.objects.get(
                numero=self.cleaned_data['numero_materia'],
                ano=self.cleaned_data['ano_materia'],
                tipo=self.cleaned_data['tipo_materia'])
        except ObjectDoesNotExist:
            msg = _('A matéria a ser inclusa não existe no cadastro'
                    ' de matérias legislativas.')
            raise ValidationError(msg)
        else:
            cleaned_data['materia'] = materia

        return cleaned_data

    def save(self, commit=False):
        expediente = super(ExpedienteMateriaForm, self).save(commit)
        expediente.materia = self.cleaned_data['materia']
        expediente.save()
        return expediente


class OrdemDiaForm(ExpedienteMateriaForm):

    _model = OrdemDia

    class Meta:
        model = OrdemDia
        fields = ['data_ordem', 'numero_ordem', 'tipo_materia', 'observacao',
                  'numero_materia', 'ano_materia', 'tipo_votacao']

    def clean_data_ordem(self):
        return self.instance.sessao_plenaria.data_inicio

    def clean_numero_ordem(self):
        sessao = self.instance.sessao_plenaria

        numero_ordem_exists = OrdemDia.objects.filter(
            sessao_plenaria=sessao,
            numero_ordem=self.cleaned_data['numero_ordem']).exists()

        if numero_ordem_exists and not self.instance.pk:
            msg = _('Esse número de ordem já existe.')
            raise ValidationError(msg)

        return self.cleaned_data['numero_ordem']

    def clean(self):
        cleaned_data = super(OrdemDiaForm, self).clean()
        if not self.is_valid():
            return cleaned_data
        return self.cleaned_data

    def save(self, commit=False):
        ordem = super(OrdemDiaForm, self).save(commit)
        ordem.materia = self.cleaned_data['materia']
        ordem.save()
        return ordem


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class MesaForm(forms.Form):
    parlamentar = forms.IntegerField(required=True)
    cargo = forms.IntegerField(required=True)


class ExpedienteForm(forms.Form):
    conteudo = forms.CharField(required=False, widget=forms.Textarea)


class OcorrenciaSessaoForm(ModelForm):
    class Meta:
        model = OcorrenciaSessao
        fields = ['conteudo']


class VotacaoForm(forms.Form):
    votos_sim = forms.IntegerField(label='Sim')
    votos_nao = forms.IntegerField(label='Não')
    abstencoes = forms.IntegerField(label='Abstenções')
    total_presentes = forms.IntegerField(
        required=False, widget=forms.HiddenInput())
    total_votantes = forms.IntegerField(
        required=False, widget=forms.HiddenInput()
    )
    voto_presidente = forms.IntegerField(
        label='A totalização inclui o voto do Presidente?')
    total_votos = forms.IntegerField(required=False, label='total')
    observacao = forms.CharField(required=False, label='Observação')
    resultado_votacao = forms.CharField(label='Resultado da Votação')

    def clean(self):
        cleaned_data = super().clean()
        if not self.is_valid():
            return cleaned_data

        votos_sim = cleaned_data['votos_sim']
        votos_nao = cleaned_data['votos_nao']
        abstencoes = cleaned_data['abstencoes']
        qtde_presentes = cleaned_data['total_presentes']
        qtde_votantes = cleaned_data['total_votantes']
        qtde_votos = votos_sim + votos_nao + abstencoes
        voto_presidente = cleaned_data['voto_presidente']

        if qtde_votantes and not voto_presidente:
            qtde_votantes -= 1

        if qtde_votantes and qtde_votos != qtde_votantes:
            raise ValidationError(
                'O total de votos não corresponde com a quantidade de votantes!')

        return cleaned_data

    # def save(self, commit=False):
    #     #TODO Verificar se esse códido é utilizado

    #     votacao = super(VotacaoForm, self).save(commit)
    #     votacao.materia = self.cleaned_data['materia']
    #     votacao.save()
    #     return votacao


class VotacaoNominalForm(forms.Form):
    resultado_votacao = forms.ModelChoiceField(label='Resultado da Votação',
                                               required=False,
                                               queryset=TipoResultadoVotacao.objects.all())


class VotacaoEditForm(forms.Form):
    pass


class SessaoPlenariaFilterSet(django_filters.FilterSet):

    data_inicio__year = django_filters.ChoiceFilter(
        required=False,
        label='Ano',
        choices=choice_anos_com_sessaoplenaria
    )
    data_inicio__month = django_filters.ChoiceFilter(required=False,
                                                     label='Mês',
                                                     choices=MES_CHOICES)
    data_inicio__day = django_filters.ChoiceFilter(required=False,
                                                   label='Dia',
                                                   choices=DIA_CHOICES)
    titulo = _('Pesquisa de Sessão Plenária')

    class Meta:
        model = SessaoPlenaria
        fields = ['tipo']

    def __init__(self, *args, **kwargs):
        super(SessaoPlenariaFilterSet, self).__init__(*args, **kwargs)

        # pré-popula o campo do formulário com o ano corrente
        self.form.fields['data_inicio__year'].initial = timezone.now().year

        row1 = to_row(
            [('data_inicio__year', 3),
             ('data_inicio__month', 3),
             ('data_inicio__day', 3),
             ('tipo', 3)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(self.titulo,
                     row1,
                     form_actions(label='Pesquisar'))
        )


class AdicionarVariasMateriasFilterSet(MateriaLegislativaFilterSet):

    o = MateriaPesquisaOrderingFilter()
    tramitacao__status = django_filters.ModelChoiceFilter(
        required=False,
        queryset=StatusTramitacao.objects.all(),
        label=_('Status da Matéria'))

    class Meta:
        model = MateriaLegislativa
        fields = ['tramitacao__status',
                  'numero',
                  'numero_protocolo',
                  'ano',
                  'tipo',
                  'data_apresentacao',
                  'data_publicacao',
                  'autoria__autor__tipo',
                  # FIXME 'autoria__autor__partido',
                  'relatoria__parlamentar_id',
                  'local_origem_externa',
                  'em_tramitacao',
                  ]

    def __init__(self, *args, **kwargs):
        # Colocar super().__init__(*args, **kwargs) quebra a tela
        # de adicionar várias matérias em expediente e ordem dia.
        # pois herda da classe AdicionarVariasMateriasFilterSet em
        # vez de MateriaLegislativaFilterSet
        super(MateriaLegislativaFilterSet, self).__init__(*args, **kwargs)

        self.filters['tipo'].label = 'Tipo de Matéria'
        self.filters['autoria__autor__tipo'].label = 'Tipo de Autor'
        # self.filters['autoria__autor__partido'].label = 'Partido do Autor'
        self.filters['relatoria__parlamentar_id'].label = 'Relatoria'

        row1 = to_row(
            [('tramitacao__status', 12)])
        row2 = to_row(
            [('tipo', 12)])
        row3 = to_row(
            [('numero', 4),
             ('ano', 4),
             ('numero_protocolo', 4)])
        row4 = to_row(
            [('data_apresentacao', 6),
             ('data_publicacao', 6)])
        row5 = to_row(
            [('autoria__autor', 0),
             (Button('pesquisar',
                     'Pesquisar Autor',
                     css_class='btn btn-primary btn-sm'), 2),
             (Button('limpar',
                     'Limpar Autor',
                     css_class='btn btn-primary btn-sm'), 10)])
        row6 = to_row(
            [('autoria__autor__tipo', 6),
             # ('autoria__autor__partido', 6)
             ])
        row7 = to_row(
            [('relatoria__parlamentar_id', 6),
             ('local_origem_externa', 6)])
        row8 = to_row(
            [('em_tramitacao', 6),
             ('o', 6)])
        row9 = to_row(
            [('ementa', 12)])

        self.form.helper = SaplFormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.layout = Layout(
            Fieldset(_('Pesquisa de Matéria'),
                     row1, row2, row3,
                     HTML(autor_label),
                     HTML(autor_modal),
                     row4, row5, row6, row7, row8, row9,
                     form_actions(label='Pesquisar'))
        )


class OradorForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parlamentar'].queryset = \
            Parlamentar.objects.filter(ativo=True).order_by('nome_parlamentar')

    def clean(self):
        super(OradorForm, self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return self.cleaned_data

        sessao_id = self.initial['id_sessao']
        numero = self.initial.get('numero')
        numero_ordem = cleaned_data['numero_ordem']
        ordem = Orador.objects.filter(
            sessao_plenaria_id=sessao_id,
            numero_ordem=numero_ordem
        ).exists()

        if ordem and numero_ordem != numero:
            raise ValidationError(_(
                "Já existe orador nesta posição de ordem de pronunciamento"
            ))

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo do Orador")

        return self.cleaned_data

    class Meta:
        model = Orador
        exclude = ['sessao_plenaria']


class OradorExpedienteForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        id_sessao = int(self.initial['id_sessao'])
        sessao = SessaoPlenaria.objects.get(id=id_sessao)
        legislatura_vigente = sessao.legislatura
        self.fields['parlamentar'].queryset = \
            Parlamentar.objects.filter(mandato__legislatura=legislatura_vigente,
                                       ativo=True).order_by('nome_parlamentar')

    def clean(self):
        super(OradorExpedienteForm, self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return self.cleaned_data

        sessao_id = self.initial['id_sessao']
        numero = self.initial.get('numero', None)
        ordem = OradorExpediente.objects.filter(
            sessao_plenaria_id=sessao_id,
            numero_ordem=cleaned_data['numero_ordem']
        ).exists()

        if ordem and (cleaned_data['numero_ordem'] != numero):
            raise ValidationError(_(
                'Já existe orador nesta posição da ordem de pronunciamento'))

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo do Orador")

        return self.cleaned_data

    class Meta:
        model = OradorExpediente
        exclude = ['sessao_plenaria']


class OradorOrdemDiaForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        id_sessao = int(self.initial['id_sessao'])
        sessao = SessaoPlenaria.objects.get(id=id_sessao)
        legislatura_vigente = sessao.legislatura
        self.fields['parlamentar'].queryset = \
            Parlamentar.objects.filter(mandato__legislatura=legislatura_vigente,
                                       ativo=True).order_by('nome_parlamentar')

    def clean(self):
        super(OradorOrdemDiaForm, self).clean()
        cleaned_data = self.cleaned_data

        if not self.is_valid():
            return self.cleaned_data

        sessao_id = self.initial['id_sessao']
        numero = self.initial.get('numero')
        numero_ordem = cleaned_data['numero_ordem']
        ordem = OradorOrdemDia.objects.filter(
            sessao_plenaria_id=sessao_id,
            numero_ordem=numero_ordem
        ).exists()

        if ordem and numero_ordem != numero:
            raise ValidationError(_(
                "Já existe orador nesta posição de ordem de pronunciamento"
            ))

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo do Orador")

        return self.cleaned_data

    class Meta:
        model = OradorOrdemDia
        exclude = ['sessao_plenaria']


class PautaSessaoFilterSet(SessaoPlenariaFilterSet):
    titulo = _('Pesquisa de Pauta de Sessão')


class ResumoOrdenacaoForm(forms.Form):
    primeiro = forms.ChoiceField(
        label='1°',
        choices=ORDENACAO_RESUMO
    )
    segundo = forms.ChoiceField(
        label='2°',
        choices=ORDENACAO_RESUMO
    )
    terceiro = forms.ChoiceField(
        label='3°',
        choices=ORDENACAO_RESUMO
    )
    quarto = forms.ChoiceField(
        label='4°',
        choices=ORDENACAO_RESUMO
    )
    quinto = forms.ChoiceField(
        label='5°',
        choices=ORDENACAO_RESUMO
    )
    sexto = forms.ChoiceField(
        label='6°',
        choices=ORDENACAO_RESUMO
    )
    setimo = forms.ChoiceField(
        label='7°',
        choices=ORDENACAO_RESUMO
    )
    oitavo = forms.ChoiceField(
        label='8°',
        choices=ORDENACAO_RESUMO
    )
    nono = forms.ChoiceField(
        label='9°',
        choices=ORDENACAO_RESUMO
    )
    decimo = forms.ChoiceField(
        label='10°',
        choices=ORDENACAO_RESUMO
    )
    decimo_primeiro = forms.ChoiceField(
        label='11°',
        choices=ORDENACAO_RESUMO
    )
    decimo_segundo = forms.ChoiceField(
        label='12°',
        choices=ORDENACAO_RESUMO
    )
    decimo_terceiro = forms.ChoiceField(
        label='13°',
        choices=ORDENACAO_RESUMO
    )
    decimo_quarto = forms.ChoiceField(
        label='14°',
        choices=ORDENACAO_RESUMO
    )

    def __init__(self, *args, **kwargs):
        row1 = to_row(
            [('primeiro', 12)])
        row2 = to_row(
            [('segundo', 12)])
        row3 = to_row(
            [('terceiro', 12)])
        row4 = to_row(
            [('quarto', 12)])
        row5 = to_row(
            [('quinto', 12)])
        row6 = to_row(
            [('sexto', 12)])
        row7 = to_row(
            [('setimo', 12)])
        row8 = to_row(
            [('oitavo', 12)])
        row9 = to_row(
            [('nono', 12)])
        row10 = to_row(
            [('decimo', 12)])
        row11 = to_row(
            [('decimo_primeiro', 12)])
        row12 = to_row(
            [('decimo_segundo', 12)])
        row13 = to_row(
            [('decimo_terceiro', 12)])
        row14 = to_row(
            [('decimo_quarto', 12)]
        )

        self.helper = SaplFormHelper()
        self.helper.layout = Layout(
            Fieldset(_(''),
                     row1, row2, row3, row4, row5,
                     row6, row7, row8, row9, row10,
                     row11, row12, row13, row14,
                     form_actions(label='Atualizar'))
        )

        super().__init__(*args, **kwargs)

    def clean(self):
        super(ResumoOrdenacaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        cleaned_data = self.cleaned_data

        for c1 in cleaned_data:
            i = 0
            for c2 in cleaned_data:
                if cleaned_data[str(c1)] == cleaned_data[str(c2)]:
                    i = i + 1
                    if i > 1:
                        raise ValidationError(_(
                            'Não é possível ter campos repetidos'))
        return self.cleaned_data

    def save(self):
        ordenacao = ResumoOrdenacao.objects.get()
        cleaned_data = self.cleaned_data

        ordenacao.primeiro = cleaned_data['primeiro']
        ordenacao.segundo = cleaned_data['segundo']
        ordenacao.terceiro = cleaned_data['terceiro']
        ordenacao.quarto = cleaned_data['quarto']
        ordenacao.quinto = cleaned_data['quinto']
        ordenacao.sexto = cleaned_data['sexto']
        ordenacao.setimo = cleaned_data['setimo']
        ordenacao.oitavo = cleaned_data['oitavo']
        ordenacao.nono = cleaned_data['nono']
        ordenacao.decimo = cleaned_data['decimo']
        ordenacao.decimo_primeiro = cleaned_data['decimo_primeiro']
        ordenacao.decimo_segundo = cleaned_data['decimo_segundo']
        ordenacao.decimo_terceiro = cleaned_data['decimo_terceiro']
        ordenacao.decimo_quarto = cleaned_data['decimo_quarto']

        ordenacao.save()


class JustificativaAusenciaForm(ModelForm):

    class Meta:
        model = JustificativaAusencia
        fields = ['parlamentar',
                  'hora',
                  'data',
                  'upload_anexo',
                  'tipo_ausencia',
                  'ausencia',
                  'materias_do_expediente',
                  'materias_da_ordem_do_dia',
                  'observacao'
                  ]

        widgets = {
            'materias_do_expediente': CheckboxSelectMultiple(),
            'materias_da_ordem_do_dia': CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('parlamentar', 12)])
        row2 = to_row(
            [('data', 6),
             ('hora', 6)])
        row3 = to_row(
            [('upload_anexo', 6)])
        row4 = to_row(
            [('tipo_ausencia', 12)])
        row5 = to_row(
            [('ausencia', 12)])
        row6 = to_row(
            [('materias_do_expediente', 12)])
        row7 = to_row(
            [('materias_da_ordem_do_dia', 12)])
        row8 = to_row(
            [('observacao', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Justificativa de Ausência'),
                     row1, row2, row3,
                     row4, row5,
                     row6,
                     row7,
                     row8)
        )
        q = Q(sessao_plenaria=kwargs['initial']['sessao_plenaria'])
        ordens = OrdemDia.objects.filter(q)
        expedientes = ExpedienteMateria.objects.filter(q)
        legislatura = kwargs['initial']['sessao_plenaria'].legislatura
        mandato = Mandato.objects.filter(
            legislatura=legislatura).order_by('parlamentar__nome_parlamentar')
        parlamentares = [m.parlamentar for m in mandato]

        super(JustificativaAusenciaForm, self).__init__(
            *args, **kwargs)

        presencas = SessaoPlenariaPresenca.objects.filter(
            q).order_by('parlamentar__nome_parlamentar')
        presencas_ordem = PresencaOrdemDia.objects.filter(
            q).order_by('parlamentar__nome_parlamentar')

        presentes = [p.parlamentar for p in presencas]
        presentes_ordem = [p.parlamentar for p in presencas_ordem]

        presentes_ambos = set(presentes).intersection(set(presentes_ordem))
        setFinal = set(parlamentares) - presentes_ambos

        self.fields['materias_do_expediente'].choices = [
            (e.id, e.materia) for e in expedientes]

        self.fields['materias_da_ordem_do_dia'].choices = [
            (o.id, o.materia) for o in ordens]

        self.fields['parlamentar'].choices = [
            ("0", "------------")] + [(p.id, p) for p in setFinal]

    def clean(self):
        super(JustificativaAusenciaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        sessao_plenaria = self.instance.sessao_plenaria

        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo de Justificativa")

        if not sessao_plenaria.finalizada or sessao_plenaria.finalizada is None:
            raise ValidationError(
                "A sessão deve estar finalizada para registrar uma Ausência")
        else:
            return self.cleaned_data

    def save(self):

        justificativa = super().save(True)

        if justificativa.ausencia == 2:
            justificativa.materias_do_expediente.clear()
            justificativa.materias_da_ordem_do_dia.clear()
        return justificativa


class OrdemExpedienteLeituraForm(forms.ModelForm):

    observacao = forms.CharField(required=False, label='Observação', widget=forms.Textarea,)

    class Meta:
        model = RegistroLeitura
        fields = ['materia',
                  'ordem',
                  'expediente',
                  'observacao',
                  'user', 
                  'ip']
        widgets = {'materia': forms.HiddenInput(),
                   'ordem': forms.HiddenInput(),
                   'expediente': forms.HiddenInput(),
                   'user': forms.HiddenInput(),
                   'ip': forms.HiddenInput()
                   }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        instance = self.initial['instance']
        if instance:
            self.instance = instance.first()
            self.fields['observacao'].initial = self.instance.observacao

        row1 = to_row(
            [('observacao', 12)])   

        actions = [HTML('<a href="{{ view.cancel_url }}"'
                        ' class="btn btn-warning">Cancelar Leitura</a>')]

        self.helper = SaplFormHelper()
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Fieldset(_('Leitura de Matéria'),
                    HTML('''
                        <b>Matéria:</b> {{materia}}<br>
                        <b>Ementa:</b> {{materia.ementa}} <br>
                    '''),
                     row1,
                     form_actions(more=actions),
                    )
        )