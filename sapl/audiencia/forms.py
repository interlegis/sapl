from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica, AnexoAudienciaPublica
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.utils import timezone

class AudienciaForm(forms.ModelForm):

    data_atual = timezone.now()

    tipo = forms.ModelChoiceField(required=True,
                                  label='Tipo de Audiência Pública',
                                  queryset=TipoAudienciaPublica.objects.all().order_by('nome'))

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=False,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número Matéria', required=False)

    ano_materia = forms.CharField(
        label='Ano Matéria',
        required=False)

    materia = forms.ModelChoiceField(required=False,
                                     widget=forms.HiddenInput(),
                                     queryset=MateriaLegislativa.objects.all())

    class Meta:
        model = AudienciaPublica
        fields = ['tipo', 'numero', 'nome',
                  'tema', 'data', 'hora_inicio', 'hora_fim',
                  'observacao', 'audiencia_cancelada', 'url_audio',
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

        if materia and ano_materia and tipo_materia:
            try:
                materia = MateriaLegislativa.objects.get(
                    numero=materia,
                    ano=ano_materia,
                    tipo=tipo_materia)
            except ObjectDoesNotExist:
                msg = _('A matéria %s nº %s/%s não existe no cadastro'
                        ' de matérias legislativas.' % (tipo_materia, materia, ano_materia))
                raise ValidationError(msg)
            else:
                cleaned_data['materia'] = materia

        else:
            campos = [materia, tipo_materia, ano_materia]
            if campos.count(None) + campos.count('') < len(campos):
                msg = _('Preencha todos os campos relacionados à Matéria Legislativa')
                raise ValidationError(msg)

        if not cleaned_data['numero']:

            ultima_audiencia = AudienciaPublica.objects.all().order_by('numero').last()
            if ultima_audiencia:
                cleaned_data['numero'] = ultima_audiencia.numero + 1
            else:
                cleaned_data['numero'] = 1



        if self.cleaned_data['hora_inicio'] and self.cleaned_data['hora_fim']:
            if (self.cleaned_data['hora_fim'] <
                self.cleaned_data['hora_inicio']):
                    msg = _('A hora de fim não pode ser anterior a hora de início')
                    raise ValidationError(msg)

        return cleaned_data


class AnexoAudienciaPublicaForm(forms.ModelForm):

    class Meta:
        model = AnexoAudienciaPublica
        fields = ['nome',
                  'data',
                  'arquivo',
                  'assunto']

        widgets = {
            'data': forms.DateInput(format='%d/%m/%Y')
        }