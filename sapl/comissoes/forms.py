import logging

from django import forms
from sapl.settings import MAX_DOC_UPLOAD_SIZE
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from sapl.base.models import Autor, TipoAutor
from sapl.comissoes.models import (Comissao, Composicao, DocumentoAcessorio,
                                   Participacao, Reuniao, Periodo)
from sapl.materia.models import PautaReuniao
from sapl.parlamentares.models import Legislatura, Mandato, Parlamentar
from sapl.utils import FileFieldCheckMixin


class ComposicaoForm(forms.ModelForm):

    comissao = forms.CharField(
        required=False, label='Comissao', widget=forms.HiddenInput())
    logger = logging.getLogger(__name__)

    class Meta:
        model = Composicao
        exclude = []

    def __init__(self, user=None, **kwargs):
        super(ComposicaoForm, self).__init__(**kwargs)
        self.fields['comissao'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super(ComposicaoForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        periodo = cleaned_data['periodo']
        comissao_pk = self.initial['comissao'].id
        cleaned_data['comissao'] = self.initial['comissao']
        
        if periodo.data_fim:
            intersecao_periodo = Composicao.objects.filter(
                Q(periodo__data_inicio__lte=periodo.data_fim,
                    periodo__data_fim__gte=periodo.data_fim) |
                Q(periodo__data_inicio__gte=periodo.data_inicio,
                    periodo__data_fim__lte=periodo.data_inicio),
                comissao_id=comissao_pk)
        else:
            intersecao_periodo = Composicao.objects.filter(
                Q(periodo__data_inicio__gte=periodo.data_inicio,
                    periodo__data_fim__lte=periodo.data_inicio),
                comissao_id=comissao_pk)

        if intersecao_periodo:
            if periodo.data_fim:
                self.logger.error('O período informado ({} a {})'
                                'choca com períodos já '
                                'cadastrados para esta comissão'
                                .format(periodo.data_inicio, periodo.data_fim))
            else:
                self.logger.error('O período informado ({} - )'
                                'choca com períodos já '
                                'cadastrados para esta comissão'
                                .format(periodo.data_inicio))
            raise ValidationError('O período informado '
                                  'choca com períodos já '
                                  'cadastrados para esta comissão')

        return cleaned_data


class PeriodoForm(forms.ModelForm):

    logger = logging.getLogger(__name__)

    class Meta:
        model = Periodo
        exclude = []

    def clean(self):
        cleaned_data = super(PeriodoForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        data_inicio = cleaned_data['data_inicio']
        data_fim = cleaned_data['data_fim']

        if data_fim and data_fim < data_inicio:
            self.logger.error('A Data Final ({}) é menor que '
                              'a Data Inicial({}).'.format(data_fim, data_inicio))
            raise ValidationError('A Data Final não pode ser menor que '
                                  'a Data Inicial')

        # Evita NoneType exception se não preenchida a data_fim
        if not data_fim:
            data_fim = data_inicio

        legislatura = Legislatura.objects.filter(data_inicio__lte=data_inicio,
                                                 data_fim__gte=data_fim,
                                                 )

        if not legislatura:
            self.logger.error('O período informado ({} a {})'
                              'não está contido em uma única '
                              'legislatura existente'.format(data_inicio, data_fim))
            raise ValidationError('O período informado '
                                  'deve estar contido em uma única '
                                  'legislatura existente')

        return cleaned_data


class ParticipacaoCreateForm(forms.ModelForm):

    logger = logging.getLogger(__name__)
    parent_pk = forms.CharField(required=False)  # widget=forms.HiddenInput())

    class Meta:
        model = Participacao
        fields = '__all__'
        exclude = ['composicao']

    def __init__(self, user=None, **kwargs):
        super(ParticipacaoCreateForm, self).__init__(**kwargs)

        if self.instance:
            comissao = kwargs['initial']
            comissao_pk = int(comissao['parent_pk'])
            composicao = Composicao.objects.get(id=comissao_pk)
            participantes = composicao.participacao_set.all()
            id_part = [p.parlamentar.id for p in participantes]
        else:
            id_part = []

        qs = self.create_participacao()

        parlamentares = Mandato.objects.filter(qs,
                                               parlamentar__ativo=True
                                               ).prefetch_related('parlamentar').\
            values_list('parlamentar',
                        flat=True
                        ).distinct()

        qs = Parlamentar.objects.filter(id__in=parlamentares).distinct().\
            exclude(id__in=id_part)
        eligible = self.verifica()
        result = list(set(qs) & set(eligible))
        if result == eligible:
            self.fields['parlamentar'].queryset = qs
        else:
            ids = [e.id for e in eligible]
            qs = Parlamentar.objects.filter(id__in=ids)
            self.fields['parlamentar'].queryset = qs

    def clean(self):
        cleaned_data = super(ParticipacaoCreateForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        data_designacao = cleaned_data['data_designacao']
        data_desligamento = cleaned_data['data_desligamento']

        if data_desligamento and \
                data_designacao > data_desligamento:
            self.logger.error('Data de designação ({}) superior '
                              'à data de desligamento ({})'.format(data_designacao, data_desligamento))
            raise ValidationError(_('Data de designação não pode ser superior '
                                    'à data de desligamento'))

        composicao = Composicao.objects.get(id=self.initial['parent_pk'])
        cargos_unicos = [
            c.cargo.nome for c in composicao.participacao_set.filter(cargo__unico=True)]

        if cleaned_data['cargo'].nome in cargos_unicos:
            msg = _('Este cargo é único para esta Comissão.')
            self.logger.error('Este cargo ({}) é único para esta Comissão.'.format(
                cleaned_data['cargo'].nome))
            raise ValidationError(msg)
        return cleaned_data

    def create_participacao(self):
        composicao = Composicao.objects.get(id=self.initial['parent_pk'])
        data_inicio_comissao = composicao.periodo.data_inicio
        data_fim_comissao = composicao.periodo.data_fim
        q1 = Q(data_fim_mandato__isnull=False,
               data_fim_mandato__gte=data_inicio_comissao)
        q2 = Q(data_inicio_mandato__gte=data_inicio_comissao) \
            & Q(data_inicio_mandato__lte=data_fim_comissao)
        q3 = Q(data_fim_mandato__isnull=True,
               data_inicio_mandato__lte=data_inicio_comissao)
        qs = q1 | q2 | q3
        return qs

    def verifica(self):
        composicao = Composicao.objects.get(id=self.initial['parent_pk'])
        participantes = composicao.participacao_set.all()
        participantes_id = [p.parlamentar.id for p in participantes]
        parlamentares = Parlamentar.objects.all().exclude(
            id__in=participantes_id).order_by('nome_completo')
        parlamentares = [p for p in parlamentares if p.ativo]

        lista = []

        for p in parlamentares:
            mandatos = p.mandato_set.all()
            for m in mandatos:
                data_inicio = m.data_inicio_mandato
                data_fim = m.data_fim_mandato
                comp_data_inicio = composicao.periodo.data_inicio
                comp_data_fim = composicao.periodo.data_fim
                if (data_fim and data_fim >= comp_data_inicio)\
                        or (data_inicio >= comp_data_inicio and data_inicio <= comp_data_fim)\
                        or (data_fim is None and data_inicio <= comp_data_inicio):
                    lista.append(p)

        lista = list(set(lista))

        return lista


class ParticipacaoEditForm(forms.ModelForm):

    logger = logging.getLogger(__name__)
    parent_pk = forms.CharField(required=False)  # widget=forms.HiddenInput())
    nome_parlamentar = forms.CharField(required=False, label='Parlamentar')

    class Meta:
        model = Participacao
        fields = ['nome_parlamentar', 'parlamentar', 'cargo', 'titular',
                  'data_designacao', 'data_desligamento',
                  'motivo_desligamento', 'observacao']
        widgets = {
            'parlamentar': forms.HiddenInput(),
        }

    def __init__(self, user=None, **kwargs):
        super(ParticipacaoEditForm, self).__init__(**kwargs)
        self.initial['nome_parlamentar'] = Parlamentar.objects.get(
            id=self.initial['parlamentar']).nome_parlamentar
        self.fields['nome_parlamentar'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super(ParticipacaoEditForm, self).clean()

        if not self.is_valid():
            return cleaned_data

        data_designacao = cleaned_data['data_designacao']
        data_desligamento = cleaned_data['data_desligamento']

        if data_desligamento and \
           data_designacao > data_desligamento:
            self.logger.error('Data de designação ({}) superior '
                              'à data de desligamento ({})'.format(data_designacao, data_desligamento))
            raise ValidationError(_('Data de designação não pode ser superior '
                                    'à data de desligamento'))

        composicao_id = self.instance.composicao_id

        composicao = Composicao.objects.get(id=composicao_id)
        cargos_unicos = [c.cargo.nome for c in
                         composicao.participacao_set.filter(cargo__unico=True).exclude(id=self.instance.pk)]

        if cleaned_data['cargo'].nome in cargos_unicos:
            msg = _('Este cargo é único para esta Comissão.')
            self.logger.error('Este cargo ({}) é único para esta Comissão (id={}).'
                              .format(cleaned_data['cargo'].nome, composicao_id))
            raise ValidationError(msg)

        return cleaned_data


class ComissaoForm(forms.ModelForm):

    logger = logging.getLogger(__name__)

    class Meta:
        model = Comissao
        fields = '__all__'

    def __init__(self, user=None, **kwargs):
        super(ComissaoForm, self).__init__(**kwargs)
        inst = self.instance
        if inst.pk:
            if inst.tipo.natureza == 'P':
                self.fields['apelido_temp'].widget.attrs['disabled'] = 'disabled'
                self.fields['data_instalacao_temp'].widget.attrs['disabled'] = 'disabled'
                self.fields['data_final_prevista_temp'].widget.attrs['disabled'] = 'disabled'
                self.fields['data_prorrogada_temp'].widget.attrs['disabled'] = 'disabled'
                self.fields['data_fim_comissao'].widget.attrs['disabled'] = 'disabled'

    def clean(self):
        super(ComissaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        if len(self.cleaned_data['nome']) > 100:
            msg = _('Nome da Comissão informado ({}) tem mais de 50 caracteres.'.format(
                self.cleaned_data['nome']))
            self.logger.error(
                'Nome da Comissão deve ter no máximo 50 caracteres.')
            raise ValidationError(msg)
        if (self.cleaned_data['data_extincao'] and
            self.cleaned_data['data_extincao'] <
                self.cleaned_data['data_criacao']):
            msg = _('Data de extinção não pode ser menor que a de criação')
            self.logger.error('Data de extinção ({}) não pode ser menor que a de criação ({}).'
                              .format(self.cleaned_data['data_extincao'], self.cleaned_data['data_criacao']))
            raise ValidationError(msg)
        if (self.cleaned_data['data_final_prevista_temp'] and
            self.cleaned_data['data_final_prevista_temp'] <
                self.cleaned_data['data_criacao']):
            msg = _('Data Prevista para Término não pode ser menor que a de criação')
            self.logger.error('Data Prevista para Término ({}) não pode ser menor que a de criação ({}).'
                              .format(self.cleaned_data['data_final_prevista_temp'], self.cleaned_data['data_criacao']))
            raise ValidationError(msg)
        if (self.cleaned_data['data_prorrogada_temp'] and
            self.cleaned_data['data_prorrogada_temp'] <
                self.cleaned_data['data_criacao']):
            msg = _('Data Novo Prazo não pode ser menor que a de criação')
            self.logger.error('Data Novo Prazo ({}) não pode ser menor que a de criação ({}).'
                              .format(self.cleaned_data['data_prorrogada_temp'], self.cleaned_data['data_criacao']))
            raise ValidationError(msg)
        if (self.cleaned_data['data_instalacao_temp'] and
            self.cleaned_data['data_instalacao_temp'] <
                self.cleaned_data['data_criacao']):
            msg = _('Data de Instalação não pode ser menor que a de criação')
            self.logger.error('Data de Instalação ({}) não pode ser menor que a de criação ({}).'
                              .format(self.cleaned_data['data_instalacao_temp'], self.cleaned_data['data_criacao']))
            raise ValidationError(msg)
        if (self.cleaned_data['data_final_prevista_temp'] and self.cleaned_data['data_instalacao_temp'] and
            self.cleaned_data['data_final_prevista_temp'] <
                self.cleaned_data['data_instalacao_temp']):
            msg = _(
                'Data Prevista para Término não pode ser menor que a de Instalação.')
            self.logger.error('Data Prevista para Término ({}) não pode ser menor que a de Instalação ({}).'
                              .format(self.cleaned_data['data_final_prevista_temp'], self.cleaned_data['data_instalacao_temp']))
            raise ValidationError(msg)
        if (self.cleaned_data['data_prorrogada_temp'] and self.cleaned_data['data_instalacao_temp'] and
            self.cleaned_data['data_prorrogada_temp'] <
                self.cleaned_data['data_instalacao_temp']):
            msg = _('Data Novo Prazo não pode ser menor que a de Instalação.')
            self.logger.error('Data Novo Prazo ({}) não pode ser menor que a de Instalação ({}).'
                              .format(self.cleaned_data['data_prorrogada_temp'], self.cleaned_data['data_instalacao_temp']))
            raise ValidationError(msg)
        return self.cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        inst = self.instance
        if not inst.pk:
            comissao = super(ComissaoForm, self).save(commit)
            content_type = ContentType.objects.get_for_model(Comissao)
            object_id = comissao.pk
            tipo = TipoAutor.objects.get(content_type=content_type)
            nome = comissao.sigla + ' - ' + comissao.nome
            Autor.objects.create(
                content_type=content_type,
                object_id=object_id,
                tipo=tipo,
                nome=nome
            )
            return comissao
        else:
            comissao = super(ComissaoForm, self).save(commit)
            return comissao


class ReuniaoForm(ModelForm):

    logger = logging.getLogger(__name__)
    comissao = forms.ModelChoiceField(queryset=Comissao.objects.all(),
                                      widget=forms.HiddenInput())

    class Meta:
        model = Reuniao
        exclude = ['cod_andamento_reuniao']

    def clean(self):
        super(ReuniaoForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        if self.cleaned_data['hora_fim']:
            if (self.cleaned_data['hora_fim'] <
                    self.cleaned_data['hora_inicio']):
                msg = _(
                    'A hora de término da reunião não pode ser menor que a de início')
                self.logger.error("A hora de término da reunião ({}) não pode ser menor que a de início ({})."
                                  .format(self.cleaned_data['hora_fim'], self.cleaned_data['hora_inicio']))
                raise ValidationError(msg)

        upload_pauta = self.cleaned_data.get('upload_pauta', False)
        upload_ata = self.cleaned_data.get('upload_ata', False)
        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_pauta and upload_pauta.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Pauta da Reunião deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (upload_pauta.size/1024)/1024))
        
        if upload_ata and upload_ata.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Ata da Reunião deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (upload_ata.size/1024)/1024))
        
        if upload_anexo and upload_anexo.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Anexo da Reunião deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (upload_anexo.size/1024)/1024))

        return self.cleaned_data


class PautaReuniaoForm(forms.ModelForm):

    class Meta:
        model = PautaReuniao
        exclude = ['reuniao']


class DocumentoAcessorioCreateForm(FileFieldCheckMixin, forms.ModelForm):

    parent_pk = forms.CharField(required=False)  # widget=forms.HiddenInput())

    class Meta:
        model = DocumentoAcessorio
        exclude = ['reuniao']

    def __init__(self, user=None, **kwargs):
        super(DocumentoAcessorioCreateForm, self).__init__(**kwargs)

        if self.instance:
            reuniao = Reuniao.objects.get(id=self.initial['parent_pk'])
            comissao = reuniao.comissao
            comissao_pk = comissao.id
            documentos = reuniao.documentoacessorio_set.all()
            return self.create_documentoacessorio()

    def create_documentoacessorio(self):
        reuniao = Reuniao.objects.get(id=self.initial['parent_pk'])

    def clean(self):
        super(DocumentoAcessorioCreateForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        arquivo = self.cleaned_data.get('arquivo', False)

        if arquivo and arquivo.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Texto Integral deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (arquivo.size/1024)/1024))

        return self.cleaned_data


class DocumentoAcessorioEditForm(FileFieldCheckMixin, forms.ModelForm):

    parent_pk = forms.CharField(required=False)  # widget=forms.HiddenInput())

    class Meta:
        model = DocumentoAcessorio
        fields = ['nome', 'data', 'autor', 'ementa',
                  'indexacao', 'arquivo']

    def __init__(self, user=None, **kwargs):
        super(DocumentoAcessorioEditForm, self).__init__(**kwargs)

    def clean(self):
        super(DocumentoAcessorioEditForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        arquivo = self.cleaned_data.get('arquivo', False)

        if arquivo and arquivo.size > MAX_DOC_UPLOAD_SIZE:
            raise ValidationError("O arquivo Texto Integral deve ser menor que {0:.1f} mb, o tamanho atual desse arquivo é {1:.1f} mb" \
                .format((MAX_DOC_UPLOAD_SIZE/1024)/1024, (arquivo.size/1024)/1024))

        return self.cleaned_data
