from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa
from sapl.utils import timezone

class AudienciaForm(forms.ModelForm):

    data_atual = timezone.now()

    tipo = forms.ModelChoiceField(required=True,
                                  label='Tipo de Audiência Pública',
                                  queryset=TipoAudienciaPublica.objects.all().order_by('nome'))

    tipo_materia = forms.ModelChoiceField(
        label=_('Tipo Matéria'),
        required=True,
        queryset=TipoMateriaLegislativa.objects.all(),
        empty_label='Selecione',
    )

    numero_materia = forms.CharField(
        label='Número Matéria', required=True)

    ano_materia = forms.CharField(
        label='Ano Matéria',
        initial=int(data_atual.year),
        required=True)

    class Meta:
        model = AudienciaPublica
        fields = '__all__'


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
        super(AudienciaForm, self).clean()

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

        if self.cleaned_data['hora_inicio'] and self.cleaned_data['hora_fim']:
            if (self.cleaned_data['hora_fim'] <
                self.cleaned_data['hora_inicio']):
                    msg = _('A hora de fim não pode ser anterior a hora de ínicio')
                    raise ValidationError(msg)

        return self.cleaned_data

    @transaction.atomic()
    def save(self, commit=True):
        audiencia = super(AudienciaForm, self).save(commit)
        return audiencia