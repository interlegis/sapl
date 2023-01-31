import logging

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from crispy_forms.layout import Button, Column, Fieldset, HTML, Layout

from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica, AnexoAudienciaPublica
from sapl.crispy_layout_mixin import form_actions, SaplFormHelper, SaplFormLayout, to_row
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.parlamentares.models import Parlamentar
from sapl.utils import timezone, FileFieldCheckMixin, validar_arquivo


class AudienciaForm(FileFieldCheckMixin, forms.ModelForm):
    logger = logging.getLogger(__name__)
    data_atual = timezone.now()

    tipo = forms.ModelChoiceField(
        required=True,
        label=_('Tipo de Audiência Pública'),
        queryset=TipoAudienciaPublica.objects.all().order_by('nome'))

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label=_('Selecione'))

    numero_materia = forms.CharField(
        label=_('Número Matéria'),
        required=False)

    ano_materia = forms.CharField(
        label=_('Ano Matéria'),
        required=False)

    materia = forms.ModelChoiceField(
        required=False,
        widget=forms.HiddenInput(),
        queryset=MateriaLegislativa.objects.all())

    parlamentar_autor = forms.ModelChoiceField(
        label=_("Parlamentar Autor"),
        required=False,
        queryset=Parlamentar.objects.all())

    requerimento = forms.ModelChoiceField(
        label=_("Requerimento"),
        required=False,
        queryset=MateriaLegislativa.objects.select_related("tipo").filter(tipo__descricao="Requerimento"))

    class Meta:
        model = AudienciaPublica
        fields = ['tipo', 'numero', 'ano', 'nome',
                  'tema', 'data', 'hora_inicio', 'hora_fim',
                  'observacao', 'audiencia_cancelada', 'parlamentar_autor', 'requerimento', 'url_audio',
                  'url_video', 'upload_pauta', 'upload_ata',
                  'upload_anexo', 'tipo_materia', 'numero_materia',
                  'ano_materia', 'materia']

    def __init__(self, **kwargs):
        super(AudienciaForm, self).__init__(**kwargs)

        tipos = []

        if not self.fields['tipo'].queryset:
            tipos.append(TipoAudienciaPublica.objects.create(nome='Audiência Pública', tipo='A'))
            tipos.append(TipoAudienciaPublica.objects.create(nome='Plebiscito', tipo='P'))
            tipos.append(TipoAudienciaPublica.objects.create(nome='Referendo', tipo='R'))
            tipos.append(TipoAudienciaPublica.objects.create(nome='Iniciativa Popular', tipo='I'))

            for t in tipos:
                t.save()

    def clean(self):
        cleaned_data = super(AudienciaForm, self).clean()
        if not self.is_valid():
            return cleaned_data

        materia = cleaned_data['numero_materia']
        ano_materia = cleaned_data['ano_materia']
        tipo_materia = cleaned_data['tipo_materia']
        parlamentar_autor = cleaned_data["parlamentar_autor"]
        requerimento = cleaned_data["requerimento"]

        if materia and ano_materia and tipo_materia:
            try:
                self.logger.debug("Tentando obter MateriaLegislativa %s nº %s/%s." % (tipo_materia, materia, ano_materia))
                materia = MateriaLegislativa.objects.get(
                    numero=materia,
                    ano=ano_materia,
                    tipo=tipo_materia)
            except ObjectDoesNotExist:
                msg = _('A matéria %s nº %s/%s não existe no cadastro'
                        ' de matérias legislativas.' % (tipo_materia, materia, ano_materia))
                self.logger.warning(
                    'A MateriaLegislativa %s nº %s/%s não existe no cadastro'
                    ' de matérias legislativas.' % (tipo_materia, materia, ano_materia)
                )
                raise ValidationError(msg)
            else:
                self.logger.info("MateriaLegislativa %s nº %s/%s obtida com sucesso." % (tipo_materia, materia, ano_materia))
                cleaned_data['materia'] = materia

        else:
            campos = [materia, tipo_materia, ano_materia]
            if campos.count(None) + campos.count('') < len(campos):
                msg = _('Preencha todos os campos relacionados à Matéria Legislativa')
                self.logger.warning(
                    'Algum campo relacionado à MatériaLegislativa %s nº %s/%s \
                    não foi preenchido.' % (tipo_materia, materia, ano_materia)
                )
                raise ValidationError(msg)

        if not cleaned_data['numero']:
            ultima_audiencia = AudienciaPublica.objects.all().order_by('-ano', 'numero').last()
            if ultima_audiencia:
                cleaned_data['numero'] = ultima_audiencia.numero + 1
            else:
                cleaned_data['numero'] = 1
        else:
            if AudienciaPublica.objects.filter(numero=cleaned_data['numero'], ano=cleaned_data['ano']).exclude(pk=self.instance.pk).exists():
                raise ValidationError(f"Já existe uma audiência com a numeração {cleaned_data['numero']}.")

        if self.cleaned_data['hora_inicio'] and self.cleaned_data['hora_fim']:
            if self.cleaned_data['hora_fim'] < self.cleaned_data['hora_inicio']:
                msg = _('A hora de fim ({}) não pode ser anterior a hora de início({})'
                        .format(self.cleaned_data['hora_fim'], self.cleaned_data['hora_inicio']))
                self.logger.warning(
                    'Hora de fim anterior à hora de início.'
                )
                raise ValidationError(msg)

        # requerimento é optativo
        if parlamentar_autor and requerimento:
            if parlamentar_autor.autor.first() not in requerimento.autores.all():
                raise ValidationError("Parlamentar Autor selecionado não faz"
                                      " parte da autoria do Requerimento "
                                      "selecionado.")
        elif parlamentar_autor:
            raise ValidationError("Para informar um autor deve-se informar um requerimento.")
        elif requerimento:
            raise ValidationError("Para informar um requerimento deve-se informar um autor.")


        upload_pauta = self.cleaned_data.get('upload_pauta', False)
        upload_ata = self.cleaned_data.get('upload_ata', False)
        upload_anexo = self.cleaned_data.get('upload_anexo', False)

        if upload_pauta:
            validar_arquivo(upload_pauta, "Pauta da Audiência Pública")

        if upload_ata:
            validar_arquivo(upload_ata, "Ata da Audiência Pública")

        if upload_anexo:
            validar_arquivo(upload_anexo, "Anexo da Audiência Pública")

        return cleaned_data


class AnexoAudienciaPublicaForm(forms.ModelForm):

    class Meta:
        model = AnexoAudienciaPublica
        fields = ['arquivo',
                  'assunto']

    def __init__(self, *args, **kwargs):

        row1 = to_row(
            [('arquivo', 4)])

        row2 = to_row(
            [('assunto', 12)])

        self.helper = SaplFormHelper()
        self.helper.layout = SaplFormLayout(
            Fieldset(_('Identificação Básica'),
                     row1, row2))
        super(AnexoAudienciaPublicaForm, self).__init__(
            *args, **kwargs)

    def clean(self):
        super(AnexoAudienciaPublicaForm, self).clean()

        if not self.is_valid():
            return self.cleaned_data

        arquivo = self.cleaned_data.get('arquivo', False)

        if arquivo:
            validar_arquivo(arquivo, "Arquivo")

        return self.cleaned_data
